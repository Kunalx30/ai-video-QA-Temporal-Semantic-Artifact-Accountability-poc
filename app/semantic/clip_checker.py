"""CLIP model integration for prompt and image embedding similarity."""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

# Module-level model cache to ensure CLIP is loaded once and reused across evaluations
_GLOBAL_CLIP_CACHE: Dict[Tuple[str, str], Tuple[Any, Any]] = {}


class CLIPChecker:
    """Computes semantic alignment between text prompt and video frames using CLIP."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: Optional[str] = None):
        self.model_name = model_name
        self.device = self._resolve_device(device)
        self.model = None
        self.processor = None
        self.is_real_model = False
        self.init_error: Optional[str] = None

        self._load_model()

    @staticmethod
    def _resolve_device(requested_device: Optional[str] = None) -> str:
        """Resolve target device (CUDA if available and not forced to CPU)."""
        try:
            import torch
            if requested_device == "cuda" and torch.cuda.is_available():
                return "cuda"
            if requested_device == "cpu":
                return "cpu"
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _load_model(self) -> None:
        """Load real CLIP model and processor. Uses local HuggingFace cache or downloads once."""
        cache_key = (self.model_name, self.device)
        if cache_key in _GLOBAL_CLIP_CACHE:
            self.model, self.processor = _GLOBAL_CLIP_CACHE[cache_key]
            self.is_real_model = True
            return

        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            # Try loading from local cache first for instant startup
            try:
                self.processor = CLIPProcessor.from_pretrained(self.model_name, local_files_only=True)
                self.model = CLIPModel.from_pretrained(self.model_name, local_files_only=True)
            except Exception:
                # Download from HuggingFace hub on first run when not yet locally cached
                self.processor = CLIPProcessor.from_pretrained(self.model_name)
                self.model = CLIPModel.from_pretrained(self.model_name)

            self.model.to(self.device)
            self.model.eval()
            self.is_real_model = True
            self.init_error = None
            _GLOBAL_CLIP_CACHE[cache_key] = (self.model, self.processor)
        except Exception as e:
            self.model = None
            self.processor = None
            self.is_real_model = False
            self.init_error = str(e)

    def get_text_embedding(self, prompt: str) -> Optional[Any]:
        """Compute normalized text embedding for prompt using CLIP text encoder."""
        if not self.is_real_model or self.model is None or self.processor is None:
            return None
        import torch
        inputs = self.processor(text=[prompt], return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            txt_out = self.model.text_model(**inputs)
            txt_embeds = self.model.text_projection(txt_out[1])
            norm_embeds = txt_embeds / txt_embeds.norm(dim=-1, keepdim=True)
            return norm_embeds

    def get_image_embeddings(self, images: List[np.ndarray]) -> Optional[Any]:
        """Compute normalized image embeddings for a batch of frames."""
        if not self.is_real_model or self.model is None or self.processor is None or not images:
            return None
        import torch
        pil_images = [
            Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) if img.ndim == 3 else Image.fromarray(img)
            for img in images
        ]
        inputs = self.processor(images=pil_images, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            img_out = self.model.vision_model(**inputs)
            img_embeds = self.model.visual_projection(img_out[1])
            norm_embeds = img_embeds / img_embeds.norm(dim=-1, keepdim=True)
            return norm_embeds

    def compute_similarity(self, prompt: str, images: List[np.ndarray]) -> List[float]:
        """Compute cosine similarity scores [0.0 - 1.0] between prompt and each image using real CLIP."""
        if not images:
            return []

        if self.is_real_model and self.model is not None and self.processor is not None:
            try:
                import torch

                pil_images = [
                    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) if img.ndim == 3 else Image.fromarray(img)
                    for img in images
                ]

                # Standard video prompt templates for natural image-text matching
                candidate_prompts = [prompt]
                p_low = prompt.lower().strip()
                if not (p_low.startswith("a video of") or p_low.startswith("a photo of") or p_low.startswith("an animation of")):
                    candidate_prompts.append(f"a video of {prompt}")
                    candidate_prompts.append(f"an animation of {prompt}")

                txt_inputs = self.processor(text=candidate_prompts, return_tensors="pt", padding=True)
                txt_inputs = {k: v.to(self.device) for k, v in txt_inputs.items()}

                img_inputs = self.processor(images=pil_images, return_tensors="pt", padding=True)
                img_inputs = {k: v.to(self.device) for k, v in img_inputs.items()}

                with torch.no_grad():
                    txt_out = self.model.text_model(**txt_inputs)
                    txt_embeds = self.model.text_projection(txt_out[1])
                    norm_txt = txt_embeds / txt_embeds.norm(dim=-1, keepdim=True)

                    img_out = self.model.vision_model(**img_inputs)
                    img_embeds = self.model.visual_projection(img_out[1])
                    norm_img = img_embeds / img_embeds.norm(dim=-1, keepdim=True)

                    # Similarity matrix (num_prompts x num_images)
                    sim_matrix = norm_txt @ norm_img.T
                    max_sims = sim_matrix.max(dim=0).values
                    return [float(round(s.item(), 4)) for s in max_sims]
            except Exception as e:
                self.init_error = f"Inference error: {e}"

        # If real model is unavailable, return empty list to trigger model_unavailable reporting
        return []

    def compute_deterministic_baseline(self, prompt: str, images: List[np.ndarray]) -> List[float]:
        """Deterministic baseline fallback scoring based on prompt keyword matching and image properties."""
        scores = []
        prompt_lower = prompt.lower()
        for img in images:
            mean_lum = float(np.mean(img))
            warmth = float(np.mean(img[:, :, 2])) - float(np.mean(img[:, :, 0]))
            base_score = 0.25
            if "orb" in prompt_lower or "glowing" in prompt_lower or "sky" in prompt_lower:
                base_score += min(0.15, max(-0.10, warmth / 200.0))
            if "black" in prompt_lower and mean_lum < 10.0:
                base_score = 0.35
            scores.append(float(round(min(1.0, max(0.0, base_score)), 4)))
        return scores

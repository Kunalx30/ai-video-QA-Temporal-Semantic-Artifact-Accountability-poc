"""Prompt alignment evaluator using multi-frame semantic sampling with real CLIP."""

from typing import Any, Dict, List, Optional
import numpy as np

from app.config import SemanticConfig
from app.media.frame_extractor import FrameInfo
from app.schemas.results import CheckStatus, ReasonCode, SemanticResult
from app.semantic.clip_checker import CLIPChecker


class PromptAlignmentEvaluator:
    """Evaluates semantic alignment between video and generation prompt."""

    def __init__(self, config: Optional[SemanticConfig] = None, clip_checker: Optional[CLIPChecker] = None):
        self.config = config or SemanticConfig()
        self.clip = clip_checker or CLIPChecker(model_name=self.config.model_name)

    def evaluate(self, frames: List[FrameInfo], prompt: str) -> SemanticResult:
        if not prompt or not prompt.strip():
            return SemanticResult(
                status=CheckStatus.FAIL,
                score=0.0,
                similarity_score=0.0,
                sampled_frame_scores=[],
                evidence={
                    "error": "Empty prompt provided for semantic alignment",
                    "model_backend": "real_clip" if self.clip.is_real_model else "clip_unavailable",
                    "model_name": self.clip.model_name,
                    "device": self.clip.device,
                },
                reason_codes=[ReasonCode.SEMANTIC_LOW_ALIGNMENT],
            )

        if not frames:
            return SemanticResult(
                status=CheckStatus.FAIL,
                score=0.0,
                similarity_score=0.0,
                sampled_frame_scores=[],
                evidence={
                    "error": "No frames provided for semantic evaluation",
                    "model_backend": "real_clip" if self.clip.is_real_model else "clip_unavailable",
                    "model_name": self.clip.model_name,
                    "device": self.clip.device,
                },
                reason_codes=[ReasonCode.SEMANTIC_LOW_ALIGNMENT],
            )

        # 1. Configurable fractional sampling
        sample_ratios = self.config.sample_points
        total = len(frames)
        sampled_indices = sorted(list(set(
            min(total - 1, max(0, int(round(r * (total - 1)))))
            for r in sample_ratios
        )))
        sampled_frames = [frames[i] for i in sampled_indices]

        # 2. Check if real CLIP model is available
        if not self.clip.is_real_model:
            evidence: Dict[str, Any] = {
                "status": "UNCERTAIN",
                "error": self.clip.init_error or "CLIP model weights unavailable",
                "model_backend": "clip_unavailable",
                "model_name": self.clip.model_name,
                "device": self.clip.device,
                "prompt": prompt,
                "sample_points": sample_ratios,
                "sampled_frame_indices": [f.frame_index for f in sampled_frames],
                "scores_per_frame": [],
                "frame_details": [],
            }
            return SemanticResult(
                status=CheckStatus.WARN,
                score=None,
                similarity_score=None,
                sampled_frame_scores=[],
                evidence=evidence,
                reason_codes=[ReasonCode.SEMANTIC_MODEL_UNAVAILABLE, ReasonCode.SEMANTIC_UNCERTAIN],
            )

        # 3. Compute similarity per sampled frame
        images = [f.image for f in sampled_frames]
        scores = self.clip.compute_similarity(prompt, images)

        if not scores:
            # Inference failed
            evidence = {
                "status": "UNCERTAIN",
                "error": self.clip.init_error or "CLIP inference failed",
                "model_backend": "clip_unavailable",
                "model_name": self.clip.model_name,
                "device": self.clip.device,
                "prompt": prompt,
                "sample_points": sample_ratios,
                "sampled_frame_indices": [f.frame_index for f in sampled_frames],
                "scores_per_frame": [],
                "frame_details": [],
            }
            return SemanticResult(
                status=CheckStatus.WARN,
                score=None,
                similarity_score=None,
                sampled_frame_scores=[],
                evidence=evidence,
                reason_codes=[ReasonCode.SEMANTIC_MODEL_UNAVAILABLE, ReasonCode.SEMANTIC_UNCERTAIN],
            )

        mean_sim = float(np.mean(scores))
        min_sim = float(np.min(scores))

        # Calibrated threshold evaluation
        reason_codes: List[ReasonCode] = []
        if mean_sim >= self.config.pass_threshold:
            status = CheckStatus.PASS
        elif mean_sim >= self.config.uncertain_threshold:
            status = CheckStatus.WARN
            reason_codes.append(ReasonCode.SEMANTIC_UNCERTAIN)
        else:
            status = CheckStatus.FAIL
            reason_codes.append(ReasonCode.SEMANTIC_LOW_ALIGNMENT)

        # Build detailed frame evidence with frame_index, timestamp, similarity
        frame_details = []
        for f, score in zip(sampled_frames, scores):
            frame_details.append({
                "frame_index": f.frame_index,
                "timestamp_seconds": round(f.timestamp, 3) if f.timestamp is not None else None,
                "similarity_score": round(score, 4),
            })

        evidence = {
            "prompt": prompt,
            "sample_points": sample_ratios,
            "sampled_frame_indices": [f.frame_index for f in sampled_frames],
            "scores_per_frame": scores,
            "frame_details": frame_details,
            "mean_similarity": round(mean_sim, 4),
            "min_similarity": round(min_sim, 4),
            "pass_threshold": self.config.pass_threshold,
            "uncertain_threshold": self.config.uncertain_threshold,
            "model_backend": "real_clip",
            "model_name": self.clip.model_name,
            "device": self.clip.device,
        }

        return SemanticResult(
            status=status,
            score=round(mean_sim, 4),
            similarity_score=round(mean_sim, 4),
            sampled_frame_scores=scores,
            evidence=evidence,
            reason_codes=reason_codes,
        )

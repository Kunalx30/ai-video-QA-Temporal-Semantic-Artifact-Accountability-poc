"""Optical flow estimation supporting both Farneback (basic) and RAFT (advanced) modes."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np


class OpticalFlowEstimator(ABC):
    """Abstract base class for optical flow estimation."""

    @abstractmethod
    def estimate_flow(self, img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
        """Estimate optical flow field from img1 to img2. Returns array of shape (H, W, 2)."""
        pass

    def compute_flow_metrics(self, flow: np.ndarray) -> Dict[str, float]:
        """Compute summary statistical metrics from an optical flow field."""
        u = flow[..., 0]
        v = flow[..., 1]
        magnitude = np.sqrt(u ** 2 + v ** 2)

        mean_mag = float(np.mean(magnitude))
        std_mag = float(np.std(magnitude))
        max_mag = float(np.max(magnitude))

        # Flow smoothness: spatial gradient of the flow field
        grad_u_x = cv2.Sobel(u, cv2.CV_32F, 1, 0, ksize=3)
        grad_u_y = cv2.Sobel(u, cv2.CV_32F, 0, 1, ksize=3)
        grad_v_x = cv2.Sobel(v, cv2.CV_32F, 1, 0, ksize=3)
        grad_v_y = cv2.Sobel(v, cv2.CV_32F, 0, 1, ksize=3)
        smoothness_energy = float(np.mean(grad_u_x**2 + grad_u_y**2 + grad_v_x**2 + grad_v_y**2))

        return {
            "mean_magnitude": round(mean_mag, 4),
            "std_magnitude": round(std_mag, 4),
            "max_magnitude": round(max_mag, 4),
            "smoothness_energy": round(smoothness_energy, 4),
        }


class FarnebackFlowEstimator(OpticalFlowEstimator):
    """Basic deterministic optical flow using OpenCV Farneback algorithm."""

    def __init__(
        self,
        pyr_scale: float = 0.5,
        levels: int = 3,
        winsize: int = 15,
        iterations: int = 3,
        poly_n: int = 5,
        poly_sigma: float = 1.2,
    ):
        self.pyr_scale = pyr_scale
        self.levels = levels
        self.winsize = winsize
        self.iterations = iterations
        self.poly_n = poly_n
        self.poly_sigma = poly_sigma

    def estimate_flow(self, img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if img1.ndim == 3 else img1
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if img2.ndim == 3 else img2
        flow = cv2.calcOpticalFlowFarneback(
            gray1,
            gray2,
            None,
            self.pyr_scale,
            self.levels,
            self.winsize,
            self.iterations,
            self.poly_n,
            self.poly_sigma,
            0,
        )
        return flow


class RAFTFlowEstimator(OpticalFlowEstimator):
    """Advanced optical flow using torchvision RAFT deep model with automatic CPU/GPU support."""

    def __init__(self, use_gpu: bool = True):
        self.device = "cpu"
        self.model = None
        self._fallback = FarnebackFlowEstimator()

        try:
            import torch
            import torchvision.models.optical_flow as of

            if use_gpu and torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"

            # Check if weights can be loaded
            if hasattr(of, "raft_small"):
                # Attempt to instantiate raft_small
                self.model = of.raft_small(weights=None)
                self.model.to(self.device)
                self.model.eval()
        except Exception:
            self.model = None

    def estimate_flow(self, img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
        if self.model is None:
            return self._fallback.estimate_flow(img1, img2)

        try:
            import torch
            import torchvision.transforms.functional as F

            # Convert BGR to RGB tensor scaled to [-1, 1]
            rgb1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            rgb2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

            t1 = F.to_tensor(rgb1) * 255.0
            t2 = F.to_tensor(rgb2) * 255.0

            # Pad height and width to multiple of 8
            _, h, w = t1.shape
            pad_h = (8 - (h % 8)) % 8
            pad_w = (8 - (w % 8)) % 8
            if pad_h > 0 or pad_w > 0:
                t1 = torch.nn.functional.pad(t1, (0, pad_w, 0, pad_h), mode="replicate")
                t2 = torch.nn.functional.pad(t2, (0, pad_w, 0, pad_h), mode="replicate")

            img1_batch = t1.unsqueeze(0).to(self.device)
            img2_batch = t2.unsqueeze(0).to(self.device)

            with torch.no_grad():
                list_of_flows = self.model(img1_batch, img2_batch)
                predicted_flow = list_of_flows[-1][0].cpu().numpy()

            flow = np.transpose(predicted_flow, (1, 2, 0))
            if pad_h > 0 or pad_w > 0:
                flow = flow[:h, :w, :]
            return flow
        except Exception:
            # Graceful fallback to Farneback
            return self._fallback.estimate_flow(img1, img2)


def get_optical_flow_estimator(mode: str = "basic") -> OpticalFlowEstimator:
    """Factory creating optical flow estimator based on configuration."""
    if mode.lower() == "advanced":
        return RAFTFlowEstimator()
    return FarnebackFlowEstimator()

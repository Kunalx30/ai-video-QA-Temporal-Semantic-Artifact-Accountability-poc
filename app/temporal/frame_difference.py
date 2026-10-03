"""Frame difference metrics calculation between consecutive video frames."""

import math
from typing import Dict, List, Tuple
import cv2
import numpy as np
from app.media.frame_extractor import FrameInfo


def compute_frame_diff(img1: np.ndarray, img2: np.ndarray) -> Dict[str, float]:
    """Compute difference metrics between two BGR frames."""
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if img1.ndim == 3 else img1
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if img2.ndim == 3 else img2

    # L1 normalized difference [0.0 - 1.0]
    l1_diff = float(np.mean(np.abs(gray2.astype(np.float32) - gray1.astype(np.float32))) / 255.0)

    # Mean squared error
    mse = float(np.mean((gray2.astype(np.float32) - gray1.astype(np.float32)) ** 2))

    # PSNR
    if mse == 0:
        psnr = 100.0
    else:
        psnr = float(10.0 * math.log10((255.0 ** 2) / mse))

    # Luminance delta (mean gray difference)
    lum1 = float(np.mean(gray1))
    lum2 = float(np.mean(gray2))
    lum_delta = lum2 - lum1

    return {
        "l1_diff": l1_diff,
        "mse": mse,
        "psnr": psnr,
        "lum_delta": lum_delta,
        "lum1": lum1,
        "lum2": lum2,
    }


def compute_sequence_diffs(frames: List[FrameInfo]) -> List[Dict[str, float]]:
    """Compute consecutive frame differences across a sequence."""
    diffs = []
    for i in range(len(frames) - 1):
        m = compute_frame_diff(frames[i].image, frames[i + 1].image)
        m["frame_from"] = frames[i].frame_index
        m["frame_to"] = frames[i + 1].frame_index
        diffs.append(m)
    return diffs

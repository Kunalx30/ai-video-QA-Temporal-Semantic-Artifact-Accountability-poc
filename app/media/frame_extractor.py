"""Reusable frame extraction module supporting sequential and sampled access."""

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class FrameInfo:
    """Represents an extracted frame and its temporal metadata."""
    frame_index: int
    timestamp: float
    image: np.ndarray
    width: int
    height: int


class FrameExtractor:
    """Extracts frames from video files with memory-efficient streaming and sampling."""

    def __init__(self, default_fps: float = 24.0):
        self.default_fps = default_fps

    def get_video_properties(self, video_path: str | Path) -> Tuple[int, int, float, int]:
        """Return (width, height, fps, total_frames)."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS)) or self.default_fps
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            return width, height, fps, frame_count
        finally:
            cap.release()

    def iter_frames(
        self,
        video_path: str | Path,
        max_frames: Optional[int] = None,
        step: int = 1,
    ) -> Generator[FrameInfo, None, None]:
        """Stream frames sequentially with optional step skipping and frame cap."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS)) or self.default_fps
        frame_idx = 0
        emitted_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                if frame_idx % step == 0:
                    timestamp = frame_idx / fps
                    h, w, _ = frame.shape
                    yield FrameInfo(
                        frame_index=frame_idx,
                        timestamp=timestamp,
                        image=frame,
                        width=w,
                        height=h,
                    )
                    emitted_count += 1
                    if max_frames is not None and emitted_count >= max_frames:
                        break

                frame_idx += 1
        finally:
            cap.release()

    def sample_frames(
        self,
        video_path: str | Path,
        sample_ratios: Optional[List[float]] = None,
    ) -> List[FrameInfo]:
        """Extract frames at specific fractional timeline points (e.g. 0.0, 0.25, 0.5, 0.75, 1.0)."""
        if sample_ratios is None:
            sample_ratios = [0.0, 0.25, 0.5, 0.75, 1.0]

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS)) or self.default_fps
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                # Fallback: iterate and count
                all_frames = list(self.iter_frames(video_path))
                total_frames = len(all_frames)
                if total_frames == 0:
                    return []
                sampled = []
                for r in sample_ratios:
                    idx = min(total_frames - 1, max(0, int(round(r * (total_frames - 1)))))
                    sampled.append(all_frames[idx])
                return sampled

            target_indices = sorted(list(set(
                min(total_frames - 1, max(0, int(round(r * (total_frames - 1)))))
                for r in sample_ratios
            )))

            results: List[FrameInfo] = []
            for target_idx in target_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w, _ = frame.shape
                    results.append(
                        FrameInfo(
                            frame_index=target_idx,
                            timestamp=target_idx / fps,
                            image=frame,
                            width=w,
                            height=h,
                        )
                    )
            return results
        finally:
            cap.release()

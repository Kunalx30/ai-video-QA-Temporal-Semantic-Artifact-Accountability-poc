"""Unified artifact detector aggregating visual defect checks."""

from typing import Any, Dict, List, Optional
from app.artifacts.black_frame import detect_black_frames
from app.artifacts.blur import detect_blur
from app.artifacts.decode_errors import detect_decode_errors
from app.artifacts.resolution_change import detect_resolution_change
from app.artifacts.text_overlay import detect_text_overlay
from app.config import ArtifactConfig
from app.media.frame_extractor import FrameInfo
from app.schemas.results import ArtifactResult, CheckStatus, ReasonCode


class ArtifactDetector:
    """Detects visual artifacts, decode glitches, blur, and black frames."""

    def __init__(self, config: Optional[ArtifactConfig] = None):
        self.config = config or ArtifactConfig()

    def detect(self, frames: List[FrameInfo]) -> ArtifactResult:
        if not frames:
            return ArtifactResult(
                status=CheckStatus.FAIL,
                black_frame_count=0,
                blur_score=0.0,
                decode_errors_count=1,
                evidence={"error": "No frames provided for artifact detection"},
                reason_codes=[ReasonCode.ARTIFACT_CORRUPTION],
            )

        # 1. Black frames
        has_black, black_count, black_frames, black_ev = detect_black_frames(frames, self.config)

        # 2. Blur
        has_blur, blur_score, blurry_frames, blur_ev = detect_blur(frames, self.config)

        # 3. Resolution change / pixelation
        has_res_change, res_frames, res_ev = detect_resolution_change(frames, self.config)

        # 4. Decode errors
        has_decode_err, decode_count, corrupt_frames, decode_ev = detect_decode_errors(frames, self.config)

        # 5. Text overlay / watermark
        has_text_overlay, text_frames, text_ev = detect_text_overlay(frames)

        reason_codes: List[ReasonCode] = []
        is_fail = False
        is_warn = False

        if has_black:
            reason_codes.append(ReasonCode.ARTIFACT_BLACK_FRAME)
            is_fail = True
        if has_blur:
            reason_codes.append(ReasonCode.ARTIFACT_BLUR)
            is_fail = True
        if has_res_change:
            reason_codes.append(ReasonCode.ARTIFACT_RESOLUTION_CHANGE)
            is_fail = True
        if has_decode_err:
            reason_codes.append(ReasonCode.ARTIFACT_DECODE_FAILURE)
            is_fail = True
        if has_text_overlay:
            reason_codes.append(ReasonCode.ARTIFACT_TEXT_OVERLAY)
            is_warn = True

        evidence: Dict[str, Any] = {
            "black_frame_evidence": black_ev,
            "blur_evidence": blur_ev,
            "resolution_evidence": res_ev,
            "decode_evidence": decode_ev,
            "text_overlay_evidence": text_ev,
        }

        status = CheckStatus.FAIL if is_fail else (CheckStatus.WARN if is_warn else CheckStatus.PASS)

        return ArtifactResult(
            status=status,
            black_frame_count=black_count,
            blur_score=round(blur_score, 2),
            decode_errors_count=decode_count,
            evidence=evidence,
            reason_codes=reason_codes,
        )

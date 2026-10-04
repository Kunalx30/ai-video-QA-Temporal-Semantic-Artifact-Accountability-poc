"""Technical media validation using ffprobe."""

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, Optional, Tuple

from app.config import QAConfig, TechnicalConfig
from app.schemas.input import GenerationMetadata
from app.schemas.results import CheckStatus, ReasonCode, TechnicalResult
from app.technical.aspect_ratio import validate_aspect_ratio


def parse_fps(fps_str: str) -> Optional[float]:
    """Parse fractional framerate string (e.g. '24/1' or '30000/1001') to float."""
    if not fps_str or fps_str == "0/0":
        return None
    if "/" in fps_str:
        num, den = fps_str.split("/", 1)
        try:
            den_val = float(den)
            if den_val == 0:
                return None
            return float(num) / den_val
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(fps_str)
    except ValueError:
        return None


def run_ffprobe(video_path: str | Path) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Execute ffprobe and return parsed JSON metadata or error message."""
    ffprobe_cmd = shutil.which("ffprobe") or "ffprobe"
    cmd = [
        ffprobe_cmd,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode != 0:
            return False, None, res.stderr.strip() or f"ffprobe exited with code {res.returncode}"
        data = json.loads(res.stdout)
        return True, data, ""
    except subprocess.TimeoutExpired:
        return False, None, "ffprobe execution timed out"
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse ffprobe JSON output: {e}"
    except Exception as e:
        return False, None, f"ffprobe execution error: {str(e)}"


class FFprobeValidator:
    """Validates technical media validity of video files."""

    def __init__(self, config: Optional[TechnicalConfig] = None):
        self.config = config or TechnicalConfig()

    def validate(
        self,
        video_path: str | Path,
        expected_meta: Optional[GenerationMetadata] = None,
        prompt: Optional[str] = None,
    ) -> TechnicalResult:
        p = Path(video_path)
        if not p.exists() or not p.is_file():
            return TechnicalResult(
                status=CheckStatus.FAIL,
                evidence={"error": f"File does not exist: {p}"},
                reason_codes=[ReasonCode.TECHNICAL_FILE_NOT_FOUND],
            )

        success, probe_data, err_msg = run_ffprobe(p)
        if not success or not probe_data:
            return TechnicalResult(
                status=CheckStatus.FAIL,
                evidence={"error": err_msg},
                reason_codes=[ReasonCode.TECHNICAL_INVALID_MEDIA],
            )

        streams = probe_data.get("streams", [])
        format_info = probe_data.get("format", {})

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        if not video_stream:
            return TechnicalResult(
                status=CheckStatus.FAIL,
                evidence={"error": "No video stream found in container"},
                reason_codes=[ReasonCode.TECHNICAL_INVALID_MEDIA],
            )

        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        width = video_stream.get("width")
        height = video_stream.get("height")
        video_codec = video_stream.get("codec_name")
        fps = parse_fps(video_stream.get("avg_frame_rate", "")) or parse_fps(video_stream.get("r_frame_rate", ""))

        # Duration determination
        duration_sec: Optional[float] = None
        duration_str = video_stream.get("duration") or format_info.get("duration")
        if duration_str:
            try:
                duration_sec = float(duration_str)
            except ValueError:
                pass

        # Frame count determination
        nb_frames: Optional[int] = None
        nb_frames_str = video_stream.get("nb_frames")
        if nb_frames_str:
            try:
                nb_frames = int(nb_frames_str)
            except ValueError:
                pass
        if nb_frames is None and duration_sec and fps:
            nb_frames = int(round(duration_sec * fps))

        reason_codes = []
        is_fail = False
        is_warn = False
        evidence: Dict[str, Any] = {
            "format_name": format_info.get("format_name"),
            "bit_rate": format_info.get("bit_rate"),
            "video_stream": {
                "codec": video_codec,
                "pix_fmt": video_stream.get("pix_fmt"),
                "width": width,
                "height": height,
                "fps": fps,
                "duration": duration_sec,
                "nb_frames": nb_frames,
            },
            "streams_count": len(streams),
            "has_audio": has_audio,
        }

        # Check technical limits
        if width is None or height is None or width < self.config.min_width or height < self.config.min_height:
            is_fail = True
            reason_codes.append(ReasonCode.TECHNICAL_INVALID_MEDIA)
            evidence["resolution_error"] = f"Resolution ({width}x{height}) is invalid or below minimum ({self.config.min_width}x{self.config.min_height})"

        if fps is None or fps < self.config.min_fps or fps > self.config.max_fps:
            is_fail = True
            if ReasonCode.TECHNICAL_INVALID_MEDIA not in reason_codes:
                reason_codes.append(ReasonCode.TECHNICAL_INVALID_MEDIA)
            evidence["fps_error"] = f"FPS ({fps}) is outside allowable range [{self.config.min_fps}, {self.config.max_fps}]"

        if duration_sec is not None and duration_sec < self.config.min_duration_seconds:
            is_fail = True
            if ReasonCode.TECHNICAL_INVALID_MEDIA not in reason_codes:
                reason_codes.append(ReasonCode.TECHNICAL_INVALID_MEDIA)
            evidence["duration_error"] = f"Duration ({duration_sec}s) is shorter than minimum ({self.config.min_duration_seconds}s)"

        # Check expected metadata mismatch if provided
        if expected_meta:
            mismatches = []
            if expected_meta.width and width and expected_meta.width != width:
                mismatches.append(f"Width mismatch: expected {expected_meta.width}, got {width}")
            if expected_meta.height and height and expected_meta.height != height:
                mismatches.append(f"Height mismatch: expected {expected_meta.height}, got {height}")
            if expected_meta.fps and fps and abs(expected_meta.fps - fps) > 1.0:
                mismatches.append(f"FPS mismatch: expected {expected_meta.fps}, got {fps}")

            if mismatches:
                is_warn = True
                reason_codes.append(ReasonCode.TECHNICAL_METADATA_MISMATCH)
                evidence["metadata_mismatches"] = mismatches

        # Check aspect ratio against generation prompt if dimensions are valid
        detected_ar: Optional[str] = None
        if width and height and width > 0 and height > 0:
            effective_prompt = prompt or (
                expected_meta.extra.get("prompt") if expected_meta and expected_meta.extra else None
            )
            ar_evidence, ar_matched = validate_aspect_ratio(
                width=width,
                height=height,
                prompt=effective_prompt,
                tolerance=self.config.aspect_ratio_tolerance,
            )
            evidence["aspect_ratio_evidence"] = ar_evidence
            detected_ar = ar_evidence.get("actual_aspect_ratio")
            if not ar_matched:
                is_fail = True
                reason_codes.append(ReasonCode.PROMPT_ASPECT_RATIO_MISMATCH)
                evidence["aspect_ratio_error"] = (
                    f"Prompt requested aspect ratio '{ar_evidence['requested_aspect_ratio']}' "
                    f"({ar_evidence['expected_ratio']}), but actual video aspect ratio is "
                    f"'{ar_evidence['actual_aspect_ratio']}' ({ar_evidence['actual_ratio']}, {width}x{height})"
                )

        status = CheckStatus.FAIL if is_fail else (CheckStatus.WARN if is_warn else CheckStatus.PASS)

        return TechnicalResult(
            status=status,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_sec,
            video_codec=video_codec,
            has_audio=has_audio,
            frame_count=nb_frames,
            aspect_ratio=detected_ar,
            evidence=evidence,
            reason_codes=reason_codes,
        )

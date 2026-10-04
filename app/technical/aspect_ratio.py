"""Prompt-to-video aspect ratio validation and deterministic prompt parsing."""

import math
import re
from typing import Any, Dict, Optional, Tuple

KNOWN_ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "16:9": (16, 9),
    "9:16": (9, 16),
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:4": (3, 4),
    "21:9": (21, 9),
}

# Regex to match numeric ratios, e.g.:
# "16:9", "16 : 9", "16/9", "16 by 9", "16by9", "16x9", "9:16", "1:1", etc.
# Optionally preceded by "aspect ratio", "--ar", "ratio", "format", "portrait", "vertical", "square", etc.
_NUMERIC_RATIO_RE = re.compile(
    r"(?i)\b(16|9|1|4|3|21)\s*(?::|/|\bby\b|x)\s*(16|9|1|4|3|9)\b"
)

# Regex to match explicit directive keywords, e.g.:
# "aspect ratio: vertical", "aspect ratio portrait", "--ar square", "format: landscape"
_DIRECTIVE_KEYWORD_RE = re.compile(
    r"(?i)\b(?:aspect[-_\s]*ratio|--?ar|video\s+format|format|ratio)\s*[:=]?\s*(?:is\s*)?"
    r"\b(square|vertical|portrait|landscape|horizontal|widescreen|cinematic)\b"
)

_KEYWORD_TO_RATIO: Dict[str, str] = {
    "square": "1:1",
    "vertical": "9:16",
    "portrait": "9:16",
    "landscape": "16:9",
    "horizontal": "16:9",
    "widescreen": "16:9",
    "cinematic": "16:9",
}


def parse_prompt_aspect_ratio(prompt: Optional[str]) -> Dict[str, Optional[str]]:
    """Deterministically parse generation prompt for an explicit aspect-ratio directive.

    Supported formats include:
    - "16:9", "aspect ratio 16:9", "16 by 9", "16/9", "16x9"
    - "portrait 9:16", "vertical 9:16", "9:16", "9 by 16"
    - "square 1:1", "1:1", "1 by 1"
    - "aspect ratio: square", "aspect ratio: vertical", "aspect ratio: portrait", "--ar 16:9"

    Returns:
        dict: {"requested_aspect_ratio": "16:9"} or {"requested_aspect_ratio": None}
    """
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        return {"requested_aspect_ratio": None}

    clean_prompt = prompt.strip()

    # 1. Search for explicit numeric ratio patterns first (e.g. 16:9, 16 by 9, 9:16, 1:1)
    num_match = _NUMERIC_RATIO_RE.search(clean_prompt)
    if num_match:
        try:
            w_str, h_str = num_match.group(1), num_match.group(2)
            w_val, h_val = int(w_str), int(h_str)
            pair = (w_val, h_val)
            for canonical, dims in KNOWN_ASPECT_RATIOS.items():
                if pair == dims:
                    return {"requested_aspect_ratio": canonical}
        except (ValueError, IndexError):
            pass

    # 2. Search for explicit directive keywords (e.g. "aspect ratio: vertical", "--ar square")
    kw_match = _DIRECTIVE_KEYWORD_RE.search(clean_prompt)
    if kw_match:
        kw = kw_match.group(1).lower()
        if kw in _KEYWORD_TO_RATIO:
            return {"requested_aspect_ratio": _KEYWORD_TO_RATIO[kw]}

    # No explicit aspect ratio directive found
    return {"requested_aspect_ratio": None}


def calculate_aspect_ratio(
    width: int, height: int, tolerance: float = 0.02
) -> Tuple[float, str]:
    """Calculate decimal aspect ratio and map to nearest canonical ratio string if within tolerance.

    Args:
        width: Video frame width in pixels.
        height: Video frame height in pixels.
        tolerance: Allowed decimal variance for known standard ratios.

    Returns:
        Tuple of (decimal_ratio, canonical_ratio_string).
    """
    if height <= 0:
        return 0.0, "unknown"

    raw_ratio = width / height

    # Match against known canonical ratios within tolerance
    for canonical, (w, h) in KNOWN_ASPECT_RATIOS.items():
        ref_ratio = w / h
        if abs(raw_ratio - ref_ratio) <= tolerance:
            return raw_ratio, canonical

    # If non-standard, simplify via GCD or return decimal ratio
    gcd = math.gcd(width, height)
    if gcd > 1:
        simp_w = width // gcd
        simp_h = height // gcd
        return raw_ratio, f"{simp_w}:{simp_h}"

    return raw_ratio, f"{round(raw_ratio, 2)}:1"


def validate_aspect_ratio(
    width: int,
    height: int,
    prompt: Optional[str] = None,
    tolerance: float = 0.02,
) -> Tuple[Dict[str, Any], bool]:
    """Validate requested aspect ratio from prompt against actual video dimensions.

    Args:
        width: Detected video width.
        height: Detected video height.
        prompt: Generation prompt text (optional).
        tolerance: Configurable tolerance for ratio matching.

    Returns:
        Tuple of (aspect_ratio_evidence_dict, matched_boolean).
    """
    parsed = parse_prompt_aspect_ratio(prompt)
    requested = parsed.get("requested_aspect_ratio")

    actual_dec, actual_canonical = calculate_aspect_ratio(width, height, tolerance=tolerance)

    # If no aspect ratio requested, always PASS with no mismatch
    if requested is None:
        evidence = {
            "requested_aspect_ratio": None,
            "actual_aspect_ratio": actual_canonical,
            "width": width,
            "height": height,
            "expected_ratio": None,
            "actual_ratio": round(actual_dec, 4),
            "tolerance": tolerance,
            "matched": True,
        }
        return evidence, True

    # Compute expected ratio decimal
    if requested in KNOWN_ASPECT_RATIOS:
        ew, eh = KNOWN_ASPECT_RATIOS[requested]
        expected_dec = ew / eh
    elif ":" in requested:
        try:
            parts = requested.split(":", 1)
            expected_dec = float(parts[0]) / float(parts[1])
        except (ValueError, ZeroDivisionError):
            expected_dec = 0.0
    else:
        expected_dec = 0.0

    matched = abs(actual_dec - expected_dec) <= tolerance

    evidence = {
        "requested_aspect_ratio": requested,
        "actual_aspect_ratio": actual_canonical,
        "width": width,
        "height": height,
        "expected_ratio": round(expected_dec, 4),
        "actual_ratio": round(actual_dec, 4),
        "tolerance": tolerance,
        "matched": matched,
    }

    return evidence, matched

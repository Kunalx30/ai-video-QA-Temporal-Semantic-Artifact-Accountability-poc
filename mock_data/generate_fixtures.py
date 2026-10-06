"""Deterministic mock fixture generator for Member 8 QA testing.

Generates:
- 24 labelled defect fixtures (Temporal, Artifact, Technical/Metadata)
- 24 matching clean controls
- Preserves 11 legacy fixtures for backward compatibility
- Generates ClipMetadata JSON, expected result JSON, prompt JSON, and manifest.json
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import cv2
import numpy as np


def compute_file_sha256(path: Path) -> str:
    """Compute cryptographic SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_base_frame(
    frame_idx: int,
    total_frames: int,
    width: int = 640,
    height: int = 360,
    seed_offset: int = 0,
) -> np.ndarray:
    """Create a deterministic synthetic frame with background gradient and moving object."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        img[y, :, 0] = int((30 + seed_offset * 5) % 150 + (y / height) * 80)
        img[y, :, 1] = int((50 + seed_offset * 3) % 150 + (y / height) * 60)
        img[y, :, 2] = int((70 + seed_offset * 7) % 150 + (y / height) * 100)

    # Moving circle from left to right
    progress = frame_idx / max(1, total_frames - 1)
    cx = int(80 + progress * (width - 160))
    cy = int(height / 2 + 40 * np.sin(progress * 2 * np.pi))
    radius = 35

    # Draw colored circle
    cv2.circle(img, (cx, cy), radius, (0, 220, 255), -1, lineType=cv2.LINE_AA)
    # Draw internal contrast pattern so flow/blur detection has rich high frequencies
    cv2.rectangle(img, (cx - 15, cy - 15), (cx + 15, cy + 15), (50, 50, 200), -1)
    cv2.putText(
        img,
        f"F:{frame_idx}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (240, 240, 240),
        2,
        cv2.LINE_AA,
    )
    return img


def write_video(output_path: Path, frames: List[np.ndarray], fps: float = 24.0) -> None:
    """Write list of frames to an MP4 video file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    for f in frames:
        writer.write(f)
    writer.release()


def generate_all_fixtures(output_dir: str | Path = "mock_data") -> Dict[str, Any]:
    """Generate all deterministic mock video fixtures, metadata, expected outcomes, and manifest."""
    base_dir = Path(output_dir)
    media_dir = base_dir / "media"
    inputs_dir = base_dir / "inputs"
    expected_dir = base_dir / "expected"
    failures_dir = base_dir / "failures"
    meta_dir = base_dir / "metadata"

    for d in [media_dir, inputs_dir, expected_dir, failures_dir, meta_dir]:
        d.mkdir(parents=True, exist_ok=True)

    total_frames = 60
    width, height = 640, 360
    fps = 24.0
    duration_s = total_frames / fps  # 2.5s

    # Generate standard clean frames
    clean_frames = [create_base_frame(i, total_frames, width, height) for i in range(total_frames)]

    # ---------------------------------------------------------
    # 1. DEFECT FIXTURE DEFINITIONS (24 defect fixtures)
    # ---------------------------------------------------------
    prompt_orb = "A golden glowing orb traveling smoothly across an evening sky."

    defect_specs: List[Dict[str, Any]] = [
        # --- Temporal Defects (10) ---
        {
            "id": "M8_TEMP_001",
            "category": "temporal",
            "defect": "Duplicate frames (mild)",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_DUPLICATE_FRAMES"],
            "failure_reason": "Consecutive identical duplicate frames in middle segment",
            "builder": lambda: [
                clean_frames[20].copy() if 20 <= i <= 28 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_002",
            "category": "temporal",
            "defect": "Duplicate frames (repeated segments)",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_DUPLICATE_FRAMES"],
            "failure_reason": "Multiple distinct duplicate frame sequences",
            "builder": lambda: [
                clean_frames[12].copy() if 12 <= i <= 19
                else (clean_frames[35].copy() if 35 <= i <= 43 else clean_frames[i].copy())
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_003",
            "category": "temporal",
            "defect": "Dropped frames (single abrupt cut)",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_FRAME_DROP"],
            "failure_reason": "Abrupt frame discontinuity dropping 15 frames at index 25",
            "builder": lambda: [
                clean_frames[i + 15].copy() if i >= 25 else clean_frames[i].copy()
                for i in range(total_frames - 15)
            ],
        },
        {
            "id": "M8_TEMP_004",
            "category": "temporal",
            "defect": "Dropped frames (stutter jumps)",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_FRAME_DROP"],
            "failure_reason": "Abrupt frame discontinuity dropping 15 frames at index 30",
            "builder": lambda: [
                clean_frames[i + 15].copy() if i >= 30 else clean_frames[i].copy()
                for i in range(total_frames - 15)
            ],
        },
        {
            "id": "M8_TEMP_005",
            "category": "temporal",
            "defect": "Luminance flicker",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_FLICKER"],
            "failure_reason": "Rapid alternating luminance changes",
            "builder": lambda: [
                cv2.convertScaleAbs(clean_frames[i], alpha=1.9, beta=40)
                if 15 <= i <= 40 and i % 2 == 0
                else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_006",
            "category": "temporal",
            "defect": "Severe strobe flicker",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_FLICKER"],
            "failure_reason": "High amplitude strobe lighting flicker spikes",
            "builder": lambda: [
                cv2.convertScaleAbs(clean_frames[i], alpha=2.2, beta=60)
                if 18 <= i <= 38 and i % 3 == 0
                else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_007",
            "category": "temporal",
            "defect": "Freeze frame sequence",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_FREEZE"],
            "failure_reason": "Extended static freeze sequence",
            "builder": lambda: [
                clean_frames[18].copy() if 18 <= i <= 36 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_008",
            "category": "temporal",
            "defect": "Long freeze sequence",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_FREEZE"],
            "failure_reason": "Long continuous frozen block across half the clip",
            "builder": lambda: [
                clean_frames[15].copy() if 15 <= i <= 45 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_009",
            "category": "temporal",
            "defect": "Motion anomaly speed jump",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_MOTION_ANOMALY"],
            "failure_reason": "Sudden abnormal speed acceleration jump",
            "builder": lambda: [
                clean_frames[min(total_frames - 1, int(i * 3.5))].copy() if 20 <= i <= 32
                else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_TEMP_010",
            "category": "temporal",
            "defect": "Erratic velocity surge",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TEMPORAL_MOTION_ANOMALY"],
            "failure_reason": "Violent multi-frame velocity surge",
            "builder": lambda: [
                clean_frames[min(total_frames - 1, int(i * 4.0))].copy() if 22 <= i <= 30
                else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },

        # --- Artifact Defects (10) ---
        {
            "id": "M8_ART_001",
            "category": "artifacts",
            "defect": "Single black frame",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["ARTIFACT_BLACK_FRAME"],
            "failure_reason": "Completely black frames injected",
            "builder": lambda: [
                np.zeros_like(clean_frames[i]) if 22 <= i <= 24 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_002",
            "category": "artifacts",
            "defect": "Multiple burst black frames",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["ARTIFACT_BLACK_FRAME"],
            "failure_reason": "Multiple blackout frame flashes",
            "builder": lambda: [
                np.zeros_like(clean_frames[i]) if (14 <= i <= 15 or 38 <= i <= 39) else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_003",
            "category": "artifacts",
            "defect": "Gaussian blur artifact",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["ARTIFACT_BLUR"],
            "failure_reason": "Severe Gaussian blur distortion",
            "builder": lambda: [
                cv2.GaussianBlur(clean_frames[i], (35, 35), 18.0) if 20 <= i <= 35 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_004",
            "category": "artifacts",
            "defect": "Heavy defocus blur",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["ARTIFACT_BLUR"],
            "failure_reason": "Extremely heavy defocus blur destroying image details",
            "builder": lambda: [
                cv2.GaussianBlur(clean_frames[i], (51, 51), 25.0) if 15 <= i <= 45 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_005",
            "category": "artifacts",
            "defect": "Resolution pixelation artifact",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["ARTIFACT_RESOLUTION_CHANGE"],
            "failure_reason": "Pixelated letterbox resolution artifact",
            "builder": lambda: [
                cv2.resize(cv2.resize(clean_frames[i], (120, 68)), (width, height), interpolation=cv2.INTER_NEAREST)
                if 20 <= i <= 35 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_006",
            "category": "artifacts",
            "defect": "Dynamic resolution shift / scaling",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["ARTIFACT_RESOLUTION_CHANGE"],
            "failure_reason": "Downsampled scaling artifact with severe aspect distortion",
            "builder": lambda: [
                cv2.resize(cv2.resize(clean_frames[i], (80, 160)), (width, height), interpolation=cv2.INTER_NEAREST)
                if 22 <= i <= 38 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_007",
            "category": "artifacts",
            "defect": "Watermark text overlay",
            "expected_decision": "HUMAN_REVIEW",
            "expected_reason_codes": ["ARTIFACT_TEXT_OVERLAY"],
            "failure_reason": "Unwanted text overlay watermark across screen",
            "builder": lambda: [
                cv2.putText(
                    clean_frames[i].copy(),
                    "UNLICENSED TRIAL WATERMARK",
                    (50, 180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.1,
                    (0, 0, 255),
                    4,
                ) if 10 <= i <= 45 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_008",
            "category": "artifacts",
            "defect": "Timecode text overlay banner",
            "expected_decision": "HUMAN_REVIEW",
            "expected_reason_codes": ["ARTIFACT_TEXT_OVERLAY"],
            "failure_reason": "Diagnostic timecode and REC banner overlay",
            "builder": lambda: [
                cv2.putText(
                    clean_frames[i].copy(),
                    "REC [00:02:14:08] OVERLAY",
                    (50, 180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.1,
                    (0, 0, 255),
                    4,
                ) for i in range(total_frames)
            ],
        },
        {
            "id": "M8_ART_009",
            "category": "artifacts",
            "defect": "Corrupted media header",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TECHNICAL_INVALID_MEDIA"],
            "failure_reason": "Truncated / invalid MP4 container header",
            "builder": None,  # Custom binary writer
        },
        {
            "id": "M8_ART_010",
            "category": "artifacts",
            "defect": "Corrupted video bitstream",
            "expected_decision": "AUTO_RETRY",
            "expected_reason_codes": ["TECHNICAL_INVALID_MEDIA"],
            "failure_reason": "Glitched bitstream packets rendering container unreadable",
            "builder": None,  # Custom binary writer
        },

        # --- Technical / Metadata Defects (4) ---
        {
            "id": "M8_TECH_001",
            "category": "technical",
            "defect": "Framerate metadata mismatch",
            "expected_decision": "HUMAN_REVIEW",
            "expected_reason_codes": ["TECHNICAL_METADATA_MISMATCH"],
            "failure_reason": "Metadata specifies 30.0 fps, but container is 24.0 fps",
            "meta_overrides": {"fps": 30.0},
            "builder": lambda: [f.copy() for f in clean_frames],
        },
        {
            "id": "M8_TECH_002",
            "category": "technical",
            "defect": "Resolution metadata mismatch",
            "expected_decision": "HUMAN_REVIEW",
            "expected_reason_codes": ["TECHNICAL_METADATA_MISMATCH"],
            "failure_reason": "Metadata specifies 1280x720, but actual video is 640x360",
            "meta_overrides": {"width": 1280, "height": 720},
            "builder": lambda: [f.copy() for f in clean_frames],
        },
        {
            "id": "M8_TECH_003",
            "category": "technical",
            "defect": "Codec metadata mismatch",
            "expected_decision": "HUMAN_REVIEW",
            "expected_reason_codes": ["TECHNICAL_METADATA_MISMATCH"],
            "failure_reason": "Metadata specifies hevc, but container is h264",
            "meta_overrides": {"codec": "hevc"},
            "builder": lambda: [f.copy() for f in clean_frames],
        },
        {
            "id": "M8_TECH_004",
            "category": "technical",
            "defect": "Duration metadata mismatch",
            "expected_decision": "HUMAN_REVIEW",
            "expected_reason_codes": ["TECHNICAL_METADATA_MISMATCH"],
            "failure_reason": "Metadata specifies 10.0s, but actual video is 2.5s",
            "meta_overrides": {"duration_s": 10.0},
            "builder": lambda: [f.copy() for f in clean_frames],
        },
    ]

    manifest: Dict[str, Any] = {
        "version": "2.0",
        "created_by": "member8_fixture_generator",
        "seed": 42,
        "fixtures": {},
    }

    # ---------------------------------------------------------
    # 2. GENERATE DEFECT FIXTURES & MATCHING CLEAN CONTROLS
    # ---------------------------------------------------------
    for idx, defect in enumerate(defect_specs, start=1):
        def_id = defect["id"]
        clean_id = f"M8_CLEAN_{idx:03d}"
        shot_id = f"S01_SH{idx:02d}"
        clip_id_defect = f"CLIP_{shot_id}_T2V_02"
        clip_id_clean = f"CLIP_{shot_id}_T2V_01"

        def_filename = f"{def_id}.mp4"
        clean_filename = f"{clean_id}.mp4"

        def_media_path = media_dir / def_filename
        clean_media_path = media_dir / clean_filename

        # Write clean control media
        clean_instance_frames = [create_base_frame(i, total_frames, width, height, seed_offset=idx) for i in range(total_frames)]
        write_video(clean_media_path, clean_instance_frames, fps=fps)
        clean_sha256 = compute_file_sha256(clean_media_path)

        # Write defect media
        builder = defect["builder"]
        if builder is not None:
            def_frames = builder()
            write_video(def_media_path, def_frames, fps=fps)
            actual_frames_count = len(def_frames)
            actual_duration = round(actual_frames_count / fps, 2)
        else:
            # Custom corrupted binary
            with open(def_media_path, "wb") as f:
                f.write(b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00isommp42\xff\xff" + f"CORRUPTED_{def_id}".encode("utf-8") * 50)
            actual_frames_count = 0
            actual_duration = 0.0

        def_sha256 = compute_file_sha256(def_media_path)

        # Build clean ClipMetadata
        clean_meta = {
            "clip_id": clip_id_clean,
            "shot_id": shot_id,
            "mode": "T2V",
            "source_type": "MOCK",
            "file": str(clean_media_path.as_posix()),
            "duration_s": duration_s,
            "fps": fps,
            "width": width,
            "height": height,
            "aspect_ratio": "16:9",
            "codec": "mpeg4",
            "model": "mock-engine",
            "settings": {},
            "reference_ids": [],
            "motion_controls": {},
            "seed": 42 + idx,
            "status": "OK",
            "failure_reason": None,
            "checksum_sha256": clean_sha256,
        }

        # Build defect ClipMetadata
        def_meta = {
            "clip_id": clip_id_defect,
            "shot_id": shot_id,
            "mode": "T2V",
            "source_type": "MOCK",
            "file": str(def_media_path.as_posix()),
            "duration_s": actual_duration if actual_duration > 0 else duration_s,
            "fps": fps,
            "width": width,
            "height": height,
            "aspect_ratio": "16:9",
            "codec": "mpeg4",
            "model": "mock-engine",
            "settings": {},
            "reference_ids": [],
            "motion_controls": {},
            "seed": 42 + idx,
            "status": "OK",
            "failure_reason": defect["failure_reason"],
            "checksum_sha256": def_sha256,
        }
        # Apply any metadata overrides (e.g. wrong fps/resolution/codec)
        if "meta_overrides" in defect:
            def_meta.update(defect["meta_overrides"])

        # Write prompt fixtures
        prompt_data = {
            "prompt": prompt_orb,
            "shot_description": prompt_orb,
        }
        with open(inputs_dir / f"{clean_id}_prompt.json", "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2)
        with open(inputs_dir / f"{def_id}_prompt.json", "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2)

        # Write inputs/
        with open(inputs_dir / f"{clean_id}.json", "w", encoding="utf-8") as f:
            json.dump(clean_meta, f, indent=2)
        with open(inputs_dir / f"{def_id}.json", "w", encoding="utf-8") as f:
            json.dump(def_meta, f, indent=2)

        # Write expected/
        clean_expected = {
            "fixture_id": clean_id,
            "expected_decision": "PASS",
            "expected_reason_codes": [],
        }
        def_expected = {
            "fixture_id": def_id,
            "expected_decision": defect["expected_decision"],
            "expected_reason_codes": defect["expected_reason_codes"],
        }
        with open(expected_dir / f"{clean_id}.json", "w", encoding="utf-8") as f:
            json.dump(clean_expected, f, indent=2)
        with open(expected_dir / f"{def_id}.json", "w", encoding="utf-8") as f:
            json.dump(def_expected, f, indent=2)

        # Write metadata/
        with open(meta_dir / f"{clean_id}.json", "w", encoding="utf-8") as f:
            json.dump(clean_meta, f, indent=2)
        with open(meta_dir / f"{def_id}.json", "w", encoding="utf-8") as f:
            json.dump(def_meta, f, indent=2)

        # Add clean control to manifest
        manifest["fixtures"][clean_id] = {
            "fixture_id": clean_id,
            "module": "member8_qa",
            "video": str(clean_media_path.as_posix()),
            "video_path": str(clean_media_path.as_posix()),
            "filename": clean_filename,
            "input_metadata": f"inputs/{clean_id}.json",
            "expected": f"expected/{clean_id}.json",
            "prompt": f"inputs/{clean_id}_prompt.json",
            "prompt_text": prompt_orb,
            "expected_decision": "PASS",
            "expected_reason_codes": [],
            "expected_status": "PASS",
            "control_fixture_id": clean_id,
            "defect": "None (Clean Control)",
            "failure_reason": None,
            "reason_code": None,
            "seed": 42 + idx,
            "frame_count": total_frames,
            "fps": fps,
            "width": width,
            "height": height,
        }

        # Add defect fixture to manifest
        manifest["fixtures"][def_id] = {
            "fixture_id": def_id,
            "module": "member8_qa",
            "video": str(def_media_path.as_posix()),
            "video_path": str(def_media_path.as_posix()),
            "filename": def_filename,
            "input_metadata": f"inputs/{def_id}.json",
            "expected": f"expected/{def_id}.json",
            "prompt": f"inputs/{def_id}_prompt.json",
            "prompt_text": prompt_orb,
            "expected_decision": defect["expected_decision"],
            "expected_reason_codes": defect["expected_reason_codes"],
            "expected_status": "FAIL" if defect["expected_decision"] != "PASS" else "PASS",
            "control_fixture_id": clean_id,
            "defect": defect["defect"],
            "failure_reason": defect["failure_reason"],
            "reason_code": defect["expected_reason_codes"][0] if defect["expected_reason_codes"] else None,
            "seed": 42 + idx,
            "frame_count": actual_frames_count,
            "fps": fps,
            "width": width,
            "height": height,
        }

    # ---------------------------------------------------------
    # 3. PRESERVE LEGACY DAY 1 FIXTURES
    # ---------------------------------------------------------
    legacy_defs = [
        ("good", "good.mp4", "None", "PASS", "PASS", None, None, lambda: [f.copy() for f in clean_frames]),
        ("duplicate_frames", "duplicate_frames.mp4", "Duplicate frames", "AUTO_RETRY", "FAIL", "Repeated identical consecutive frames", "TEMPORAL_DUPLICATE_FRAMES", lambda: [clean_frames[20].copy() if 20 <= i <= 28 else clean_frames[i].copy() for i in range(total_frames)]),
        ("dropped_frames", "dropped_frames.mp4", "Dropped frames / abrupt jump", "AUTO_RETRY", "FAIL", "Abrupt frame discontinuity / dropped frames", "TEMPORAL_FRAME_DROP", lambda: [clean_frames[i + 15].copy() if i >= 25 else clean_frames[i].copy() for i in range(total_frames - 15)]),
        ("flicker", "flicker.mp4", "Luminance flicker", "AUTO_RETRY", "FAIL", "Rapid alternating luminance changes", "TEMPORAL_FLICKER", lambda: [cv2.convertScaleAbs(clean_frames[i], alpha=1.9, beta=40) if 15 <= i <= 40 and i % 2 == 0 else clean_frames[i].copy() for i in range(total_frames)]),
        ("freeze", "freeze.mp4", "Frozen sequence", "AUTO_RETRY", "FAIL", "Extended frozen sequence", "TEMPORAL_FREEZE", lambda: [clean_frames[18].copy() if 18 <= i <= 36 else clean_frames[i].copy() for i in range(total_frames)]),
        ("speed_jump", "speed_jump.mp4", "Motion anomaly speed jump", "AUTO_RETRY", "FAIL", "Sudden abnormal speed acceleration", "TEMPORAL_MOTION_ANOMALY", lambda: [clean_frames[min(total_frames - 1, int(i * 3.5))].copy() if 20 <= i <= 32 else clean_frames[i].copy() for i in range(total_frames)]),
        ("black_frame", "black_frame.mp4", "Black frame artifact", "AUTO_RETRY", "FAIL", "Completely black frames injected", "ARTIFACT_BLACK_FRAME", lambda: [np.zeros_like(clean_frames[i]) if 22 <= i <= 24 else clean_frames[i].copy() for i in range(total_frames)]),
        ("blur", "blur.mp4", "Severe blur artifact", "AUTO_RETRY", "FAIL", "Severe Gaussian blur distortion", "ARTIFACT_BLUR", lambda: [cv2.GaussianBlur(clean_frames[i], (35, 35), 18.0) if 20 <= i <= 35 else clean_frames[i].copy() for i in range(total_frames)]),
        ("resolution_change", "resolution_change.mp4", "Resolution / scaling artifact", "AUTO_RETRY", "FAIL", "Pixelated letterbox resolution artifact", "ARTIFACT_RESOLUTION_CHANGE", lambda: [cv2.resize(cv2.resize(clean_frames[i], (120, 68)), (width, height), interpolation=cv2.INTER_NEAREST) if 20 <= i <= 35 else clean_frames[i].copy() for i in range(total_frames)]),
        ("text_overlay", "text_overlay.mp4", "Watermark / unexpected text overlay", "HUMAN_REVIEW", "WARN", "Unwanted text overlay watermark across screen", "ARTIFACT_TEXT_OVERLAY", lambda: [cv2.putText(clean_frames[i].copy(), "UNLICENSED TRIAL WATERMARK", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 4) if 10 <= i <= 45 else clean_frames[i].copy() for i in range(total_frames)]),
    ]

    for leg_id, leg_file, defect_desc, exp_dec, exp_stat, fail_reason, reason_code, builder in legacy_defs:
        m_path = media_dir / leg_file
        frames = builder()
        write_video(m_path, frames, fps=fps)
        sha = compute_file_sha256(m_path)

        meta = {
            "fixture_id": leg_id,
            "filename": leg_file,
            "video_path": str(m_path.as_posix()),
            "prompt": prompt_orb,
            "defect": defect_desc,
            "expected_decision": exp_dec,
            "expected_status": exp_stat,
            "failure_reason": fail_reason,
            "reason_code": reason_code,
            "created_by": "member8_fixture_generator",
            "seed": 42,
            "frame_count": len(frames),
            "fps": fps,
            "width": width,
            "height": height,
        }
        with open(inputs_dir / f"{leg_id}.json", "w", encoding="utf-8") as f:
            json.dump({
                "video_path": str(m_path.as_posix()),
                "prompt": prompt_orb,
                "video_id": f"VID_{leg_id.upper()}",
                "metadata": {"generation_id": f"GEN_{leg_id.upper()}", "fps": fps, "width": width, "height": height},
            }, f, indent=2)
        with open(expected_dir / f"{leg_id}.json", "w", encoding="utf-8") as f:
            json.dump({
                "expected_decision": exp_dec,
                "expected_status": exp_stat,
                "reason_code": reason_code,
            }, f, indent=2)
        with open(meta_dir / f"{leg_id}.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        manifest["fixtures"][leg_id] = meta

    # Legacy corrupted metadata fixture
    corrupted_path = media_dir / "corrupted_metadata.mp4"
    with open(corrupted_path, "wb") as f:
        f.write(b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00isommp42\xff\xffCORRUPTED_STREAM_DATA_GARBAGE")

    corrupted_meta = {
        "fixture_id": "corrupted_metadata",
        "filename": "corrupted_metadata.mp4",
        "video_path": str(corrupted_path.as_posix()),
        "prompt": "A test video with corrupted media container.",
        "defect": "Corrupted media container",
        "expected_decision": "AUTO_RETRY",
        "expected_status": "FAIL",
        "failure_reason": "Corrupted video container streams unparseable by ffprobe",
        "reason_code": "TECHNICAL_INVALID_MEDIA",
        "created_by": "member8_fixture_generator",
        "seed": 42,
    }
    with open(meta_dir / "corrupted_metadata.json", "w", encoding="utf-8") as f:
        json.dump(corrupted_meta, f, indent=2)
    with open(inputs_dir / "corrupted_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "video_path": str(corrupted_path.as_posix()),
            "prompt": "A test video with corrupted media container.",
            "video_id": "VID_CORRUPTED",
        }, f, indent=2)
    with open(expected_dir / "corrupted_metadata.json", "w", encoding="utf-8") as f:
        json.dump({
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "reason_code": "TECHNICAL_INVALID_MEDIA",
        }, f, indent=2)
    manifest["fixtures"]["corrupted_metadata"] = corrupted_meta

    # Write unified manifest.json
    with open(base_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    m = generate_all_fixtures()
    fixtures = m.get("fixtures", {})
    defects_count = sum(1 for f in fixtures.values() if f.get("expected_decision") != "PASS")
    controls_count = sum(1 for f in fixtures.values() if f.get("expected_decision") == "PASS")
    print(
        f"Generated {len(fixtures)} fixtures in mock_data/ "
        f"({defects_count} defect fixtures and {controls_count} clean controls: "
        f"24 Day 2 defect/clean pairs + 11 preserved Day 1 fixtures)"
    )

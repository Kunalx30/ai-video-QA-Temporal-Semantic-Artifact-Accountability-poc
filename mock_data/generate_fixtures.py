"""Deterministic mock fixture generator for Member 8 QA testing.

Creates real MP4 media files with controlled defects and metadata.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import cv2
import numpy as np


def create_base_frame(frame_idx: int, total_frames: int, width: int = 640, height: int = 360) -> np.ndarray:
    """Create a deterministic synthetic frame with background gradient and moving object."""
    # Background gradient
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        img[y, :, 0] = int(30 + (y / height) * 80)
        img[y, :, 1] = int(50 + (y / height) * 60)
        img[y, :, 2] = int(70 + (y / height) * 100)

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
    """Generate all deterministic mock video fixtures and manifest."""
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

    # 1. Base clean frames
    clean_frames = [create_base_frame(i, total_frames, width, height) for i in range(total_frames)]

    fixtures_def = [
        {
            "id": "good",
            "filename": "good.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "None",
            "expected_decision": "PASS",
            "expected_status": "PASS",
            "failure_reason": None,
            "reason_code": None,
            "builder": lambda: [f.copy() for f in clean_frames],
        },
        {
            "id": "duplicate_frames",
            "filename": "duplicate_frames.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Duplicate frames",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Repeated identical consecutive frames",
            "reason_code": "TEMPORAL_DUPLICATE_FRAMES",
            "builder": lambda: [
                clean_frames[20].copy() if 20 <= i <= 28 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "dropped_frames",
            "filename": "dropped_frames.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Dropped frames / abrupt jump",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Abrupt frame discontinuity / dropped frames",
            "reason_code": "TEMPORAL_FRAME_DROP",
            "builder": lambda: [
                clean_frames[i + 15].copy() if i >= 25 else clean_frames[i].copy()
                for i in range(total_frames - 15)
            ],
        },
        {
            "id": "flicker",
            "filename": "flicker.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Luminance flicker",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Rapid alternating luminance changes",
            "reason_code": "TEMPORAL_FLICKER",
            "builder": lambda: [
                cv2.convertScaleAbs(clean_frames[i], alpha=1.9, beta=40) if 15 <= i <= 40 and i % 2 == 0
                else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "freeze",
            "filename": "freeze.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Frozen sequence",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Extended frozen sequence",
            "reason_code": "TEMPORAL_FREEZE",
            "builder": lambda: [
                clean_frames[18].copy() if 18 <= i <= 36 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "speed_jump",
            "filename": "speed_jump.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Motion anomaly speed jump",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Sudden abnormal speed acceleration",
            "reason_code": "TEMPORAL_MOTION_ANOMALY",
            "builder": lambda: [
                clean_frames[min(total_frames - 1, int(i * 3.5))].copy() if 20 <= i <= 32
                else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "black_frame",
            "filename": "black_frame.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Black frame artifact",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Completely black frames injected",
            "reason_code": "ARTIFACT_BLACK_FRAME",
            "builder": lambda: [
                np.zeros_like(clean_frames[i]) if 22 <= i <= 24 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "blur",
            "filename": "blur.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Severe blur artifact",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Severe Gaussian blur distortion",
            "reason_code": "ARTIFACT_BLUR",
            "builder": lambda: [
                cv2.GaussianBlur(clean_frames[i], (35, 35), 18.0) if 20 <= i <= 35 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "resolution_change",
            "filename": "resolution_change.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Resolution / scaling artifact",
            "expected_decision": "AUTO_RETRY",
            "expected_status": "FAIL",
            "failure_reason": "Pixelated letterbox resolution artifact",
            "reason_code": "ARTIFACT_RESOLUTION_CHANGE",
            "builder": lambda: [
                cv2.resize(cv2.resize(clean_frames[i], (120, 68)), (width, height), interpolation=cv2.INTER_NEAREST)
                if 20 <= i <= 35 else clean_frames[i].copy()
                for i in range(total_frames)
            ],
        },
        {
            "id": "text_overlay",
            "filename": "text_overlay.mp4",
            "prompt": "A golden glowing orb traveling smoothly across an evening sky.",
            "defect": "Watermark / unexpected text overlay",
            "expected_decision": "HUMAN_REVIEW",
            "expected_status": "WARN",
            "failure_reason": "Unwanted text overlay watermark across screen",
            "reason_code": "ARTIFACT_TEXT_OVERLAY",
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
    ]

    manifest: Dict[str, Any] = {
        "version": "1.0",
        "created_by": "member8_fixture_generator",
        "seed": 42,
        "fixtures": {},
    }

    for item in fixtures_def:
        media_path = media_dir / item["filename"]
        frames = item["builder"]()
        write_video(media_path, frames, fps=fps)

        meta = {
            "fixture_id": item["id"],
            "filename": item["filename"],
            "video_path": str(media_path.as_posix()),
            "prompt": item["prompt"],
            "defect": item["defect"],
            "expected_decision": item["expected_decision"],
            "expected_status": item["expected_status"],
            "failure_reason": item["failure_reason"],
            "reason_code": item["reason_code"],
            "created_by": "member8_fixture_generator",
            "seed": 42,
            "frame_count": len(frames),
            "fps": fps,
            "width": width,
            "height": height,
        }

        # Write inputs/
        input_data = {
            "video_path": str(media_path.as_posix()),
            "prompt": item["prompt"],
            "video_id": f"VID_{item['id'].upper()}",
            "metadata": {
                "generation_id": f"GEN_{item['id'].upper()}",
                "fps": fps,
                "width": width,
                "height": height,
            },
        }
        with open(inputs_dir / f"{item['id']}.json", "w", encoding="utf-8") as f:
            json.dump(input_data, f, indent=2)

        # Write expected/
        expected_data = {
            "expected_decision": item["expected_decision"],
            "expected_status": item["expected_status"],
            "reason_code": item["reason_code"],
        }
        with open(expected_dir / f"{item['id']}.json", "w", encoding="utf-8") as f:
            json.dump(expected_data, f, indent=2)

        # Write metadata/
        with open(meta_dir / f"{item['id']}.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        manifest["fixtures"][item["id"]] = meta

    # Also create corrupted_metadata.mp4 (real file with corrupted payload)
    corrupted_path = media_dir / "corrupted_metadata.mp4"
    with open(corrupted_path, "wb") as f:
        # Invalid mp4 header and garbage bytes
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
    print(f"Generated {len(m['fixtures'])} fixtures in mock_data/")

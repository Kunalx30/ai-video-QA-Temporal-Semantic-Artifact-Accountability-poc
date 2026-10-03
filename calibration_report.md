# Member 8 QA Module — Calibration Report

Comprehensive evaluation across all 11 curated fixtures measuring detector sensitivity, reason code attribution, and classification accuracy.

## Summary Metrics

- **Total Fixtures Evaluated**: 11
- **Correct Classifications**: 11/11 (100.0%)
- **False Positives (Clean flagged as defect)**: 0
- **False Negatives (Defect missed as PASS)**: 0

## Detailed Calibration Matrix

| Fixture | Injected Defect | Expected Decision | Actual Decision | Expected Reason | Actual Reasons | Outcome |
|---|---|---|---|---|---|---|
| `good.mp4` | None | **PASS** | **PASS** | `None` | `None` | PASS |
| `duplicate_frames.mp4` | Duplicate frames | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_DUPLICATE_FRAMES` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_MOTION_ANOMALY` | PASS |
| `dropped_frames.mp4` | Dropped frames / abrupt jump | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FRAME_DROP` | `TEMPORAL_FRAME_DROP` | PASS |
| `flicker.mp4` | Luminance flicker | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FLICKER` | `TEMPORAL_FLICKER, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `freeze.mp4` | Frozen sequence | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FREEZE` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `speed_jump.mp4` | Motion anomaly speed jump | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_MOTION_ANOMALY` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `black_frame.mp4` | Black frame artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLACK_FRAME` | `TEMPORAL_FRAME_DROP, ARTIFACT_BLACK_FRAME, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `blur.mp4` | Severe blur artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLUR` | `TEMPORAL_MOTION_ANOMALY, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `resolution_change.mp4` | Resolution / scaling artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_RESOLUTION_CHANGE` | `ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `text_overlay.mp4` | Watermark / unexpected text overlay | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `ARTIFACT_TEXT_OVERLAY` | `ARTIFACT_TEXT_OVERLAY` | PASS |
| `corrupted_metadata.mp4` | Corrupted media container | **AUTO_RETRY** | **AUTO_RETRY** | `TECHNICAL_INVALID_MEDIA` | `TECHNICAL_INVALID_MEDIA` | PASS |

## Key Calibrated Thresholds

- **Temporal Flicker**: Luminance second-order difference threshold = `15.0`
- **Duplicate Frames**: PSNR threshold = `45.0` dB, L1 normalized diff <= `0.0005`
- **Freeze Sequences**: Consecutive identical frames >= `6`
- **Dropped Frames**: Motion jump spike ratio >= `2.6x` with delta > `0.005`
- **Motion Anomalies**: Sudden acceleration jump ratio > `3.5x`
- **Black Frames**: Mean luminance <= `2.0` or >= `98%` dark pixels
- **Blur**: Laplacian variance threshold = `25.0`
- **Semantic Alignment**: Pass threshold = `0.22`, Uncertain threshold = `0.18`
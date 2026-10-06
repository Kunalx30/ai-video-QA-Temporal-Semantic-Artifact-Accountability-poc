# Member 8 QA Module — Calibration Report

Comprehensive empirical evaluation measuring detector sensitivity, reason code attribution, defect detection rates, and clean-control false rejection rates.

## Summary Metrics

- **Total Fixtures Evaluated**: 59
- **Total Defect Fixtures**: 34
- **Total Clean Controls**: 25
- **Defect Detection Rate**: 34/34 (100.0%)
- **Clean Control False-Reject Rate**: 0/25 (0.0%)
- **Overall Classification Accuracy**: 59/59 (100.0%)

## Detailed Calibration Matrix

| Fixture | Defect Description | Expected Decision | Actual Decision | Expected Reason | Actual Reasons | Outcome |
|---|---|---|---|---|---|---|
| `M8_CLEAN_001` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_001` | Duplicate frames (mild) | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_DUPLICATE_FRAMES` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_MOTION_ANOMALY` | PASS |
| `M8_CLEAN_002` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_002` | Duplicate frames (repeated segments) | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_DUPLICATE_FRAMES` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `M8_CLEAN_003` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_003` | Dropped frames (single abrupt cut) | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FRAME_DROP` | `TEMPORAL_FRAME_DROP` | PASS |
| `M8_CLEAN_004` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_004` | Dropped frames (stutter jumps) | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FRAME_DROP` | `TEMPORAL_FRAME_DROP` | PASS |
| `M8_CLEAN_005` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_005` | Luminance flicker | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FLICKER` | `TEMPORAL_FLICKER, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_006` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_006` | Severe strobe flicker | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FLICKER` | `TEMPORAL_FLICKER, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_007` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_007` | Freeze frame sequence | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FREEZE` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `M8_CLEAN_008` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_008` | Long freeze sequence | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FREEZE` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `M8_CLEAN_009` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_009` | Motion anomaly speed jump | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_MOTION_ANOMALY` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `M8_CLEAN_010` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TEMP_010` | Erratic velocity surge | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_MOTION_ANOMALY` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `M8_CLEAN_011` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_001` | Single black frame | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLACK_FRAME` | `ARTIFACT_BLACK_FRAME, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_012` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_002` | Multiple burst black frames | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLACK_FRAME` | `ARTIFACT_BLACK_FRAME, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_013` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_003` | Gaussian blur artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLUR` | `TEMPORAL_MOTION_ANOMALY, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_014` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_004` | Heavy defocus blur | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLUR` | `TEMPORAL_MOTION_ANOMALY, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_015` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_005` | Resolution pixelation artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_RESOLUTION_CHANGE` | `ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_016` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_006` | Dynamic resolution shift / scaling | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_RESOLUTION_CHANGE` | `ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `M8_CLEAN_017` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_007` | Watermark text overlay | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `ARTIFACT_TEXT_OVERLAY` | `ARTIFACT_TEXT_OVERLAY` | PASS |
| `M8_CLEAN_018` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_008` | Timecode text overlay banner | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `ARTIFACT_TEXT_OVERLAY` | `ARTIFACT_TEXT_OVERLAY` | PASS |
| `M8_CLEAN_019` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_009` | Corrupted media header | **AUTO_RETRY** | **AUTO_RETRY** | `TECHNICAL_INVALID_MEDIA` | `TECHNICAL_INVALID_MEDIA` | PASS |
| `M8_CLEAN_020` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_ART_010` | Corrupted video bitstream | **AUTO_RETRY** | **AUTO_RETRY** | `TECHNICAL_INVALID_MEDIA` | `TECHNICAL_INVALID_MEDIA` | PASS |
| `M8_CLEAN_021` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TECH_001` | Framerate metadata mismatch | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `TECHNICAL_METADATA_MISMATCH` | `TECHNICAL_METADATA_MISMATCH` | PASS |
| `M8_CLEAN_022` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TECH_002` | Resolution metadata mismatch | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `TECHNICAL_METADATA_MISMATCH` | `TECHNICAL_METADATA_MISMATCH` | PASS |
| `M8_CLEAN_023` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TECH_003` | Codec metadata mismatch | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `TECHNICAL_METADATA_MISMATCH` | `TECHNICAL_METADATA_MISMATCH` | PASS |
| `M8_CLEAN_024` | None (Clean Control) | **PASS** | **PASS** | `None` | `None` | PASS |
| `M8_TECH_004` | Duration metadata mismatch | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `TECHNICAL_METADATA_MISMATCH` | `TECHNICAL_METADATA_MISMATCH` | PASS |
| `good` | None | **PASS** | **PASS** | `None` | `None` | PASS |
| `duplicate_frames` | Duplicate frames | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_DUPLICATE_FRAMES` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_MOTION_ANOMALY` | PASS |
| `dropped_frames` | Dropped frames / abrupt jump | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FRAME_DROP` | `TEMPORAL_FRAME_DROP` | PASS |
| `flicker` | Luminance flicker | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FLICKER` | `TEMPORAL_FLICKER, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `freeze` | Frozen sequence | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_FREEZE` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `speed_jump` | Motion anomaly speed jump | **AUTO_RETRY** | **AUTO_RETRY** | `TEMPORAL_MOTION_ANOMALY` | `TEMPORAL_DUPLICATE_FRAMES, TEMPORAL_FREEZE, TEMPORAL_FRAME_DROP, TEMPORAL_MOTION_ANOMALY` | PASS |
| `black_frame` | Black frame artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLACK_FRAME` | `ARTIFACT_BLACK_FRAME, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `blur` | Severe blur artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_BLUR` | `TEMPORAL_MOTION_ANOMALY, ARTIFACT_BLUR, ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `resolution_change` | Resolution / scaling artifact | **AUTO_RETRY** | **AUTO_RETRY** | `ARTIFACT_RESOLUTION_CHANGE` | `ARTIFACT_RESOLUTION_CHANGE` | PASS |
| `text_overlay` | Watermark / unexpected text overlay | **HUMAN_REVIEW** | **HUMAN_REVIEW** | `ARTIFACT_TEXT_OVERLAY` | `ARTIFACT_TEXT_OVERLAY` | PASS |
| `corrupted_metadata` | Corrupted media container | **AUTO_RETRY** | **AUTO_RETRY** | `TECHNICAL_INVALID_MEDIA` | `TECHNICAL_INVALID_MEDIA` | PASS |

## Key Calibrated Thresholds

- **Temporal Flicker**: Luminance second-order difference threshold = `15.0`
- **Duplicate Frames**: PSNR threshold = `45.0` dB, L1 normalized diff <= `0.0005`
- **Freeze Sequences**: Consecutive identical frames >= `6`
- **Dropped Frames**: Motion jump spike ratio >= `2.6x` with delta > `0.005`
- **Motion Anomalies**: Sudden acceleration jump ratio > `3.5x`
- **Black Frames**: Mean luminance <= `2.0` or >= `98%` dark pixels
- **Blur**: Laplacian variance threshold = `25.0`
- **Semantic Alignment**: Pass threshold = `0.22`, Uncertain threshold = `0.18`
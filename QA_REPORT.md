# Member 8 QA Report

## Executive Summary

Member 8 (Temporal, Semantic, Artifact & Accountability QA) evaluated a total of 59 deterministic fixtures (34 defect fixtures and 25 clean controls) under the Day 2 regression test harness. The system achieved a defect detection rate of 100.0% and a clean-control false rejection rate of 0.0%.

## Fixture Summary

- **Total Defect Fixtures**: 34
- **Total Clean Controls**: 25
- **Total Executed**: 59
- **Total Passed**: 59
- **Total Failed**: 0

## Technical QA

Technical media validation is verified via `ffprobe` against incoming `ClipMetadata`. Evaluations check container integrity, video codec, frame dimensions, framerate, duration, and prompt-level aspect ratio requirements. Fixtures testing technical mismatches (`M8_TECH_001` through `M8_TECH_004`) verify framerate, resolution, codec, and duration discrepancies, routing them deterministically to `HUMAN_REVIEW` via `TECHNICAL_METADATA_MISMATCH`.

## Temporal QA

Temporal stability covers duplicate frame detection (PSNR >= 45 dB), abrupt dropped frames (motion jump spike ratio >= 2.6x), luminance flicker (second-order luminance acceleration > 15.0), extended frozen frame sequences (>= 6 identical frames), and velocity anomalies / speed surges (velocity acceleration ratio > 3.5x). All temporal defect fixtures (`M8_TEMP_001` through `M8_TEMP_010`) are successfully classified and routed to `AUTO_RETRY`.

## Artifact QA

Visual defect detection monitors black frames (mean luminance <= 2.0), severe blur (Laplacian variance threshold = 25.0), resolution inconsistencies (pixelation and letterbox artifacts), unexpected text/watermark overlays, and corrupted bitstreams. Defect fixtures `M8_ART_001` through `M8_ART_010` trigger corresponding reason codes: `ARTIFACT_BLACK_FRAME`, `ARTIFACT_BLUR`, `ARTIFACT_RESOLUTION_CHANGE`, `ARTIFACT_TEXT_OVERLAY`, and `TECHNICAL_INVALID_MEDIA`.

## Semantic QA

Semantic prompt alignment operates via OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`), sampling frames uniformly and computing cosine similarity against the shot description. Passing threshold is calibrated at >= 0.22, with scores between 0.18 and 0.22 classified as uncertain, and below 0.18 routed to `AUTO_RETRY` via `SEMANTIC_LOW_ALIGNMENT`.

## Provenance / Accountability

For every evaluated clip, cryptographic SHA-256 media hashing is computed directly on the file bitstream. Unique identifiers (`clip_id`, `video_id`, `qa_run_id`) and machine-readable evidence files are generated for every execution and linked in `QAResult.evidence_files`.

## Decision Distribution

- **PASS**: 25
- **AUTO_RETRY**: 27
- **HUMAN_REVIEW**: 7

## Detection Rates

- **Overall Defect Detection Rate**: 100.0% (34/34)

## False Reject Rate

- **Clean Control False Reject Rate**: 0.0% (0/25)

## Failed Fixtures

None. All fixtures matched expected decisions and reason codes.


## Threshold Calibration

| Metric / Detector | Calibrated Threshold | Operational Rationale |
|---|---|---|
| Temporal Flicker | Luminance second-order diff = `15.0` | Eliminates natural motion false positives while detecting rapid strobing |
| Duplicate Frames | PSNR = `45.0` dB, L1 diff <= `0.0005` | Distinguishes static repeated frames from subtle slow-motion movements |
| Freeze Sequence | Consecutive identical frames >= `6` | Flags frozen rendering pipeline stalls |
| Dropped Frames | Jump ratio >= `2.6x`, delta > `0.005` | Shot-boundary aware filtering prevents cut transitions from false triggering |
| Motion Anomaly | Velocity acceleration ratio > `3.5x` | Catches violent erratic object teleportation and speed surges |
| Black Frames | Mean luminance <= `2.0` | High-precision blackout detection |
| Blur Artifact | Laplacian variance = `25.0` | Separates artistic soft focus from severe defocus blur |
| Semantic Alignment | Pass >= `0.22`, Uncertain >= `0.18` | Calibrated on real AI video against CLIP ViT-B/32 |

## Known Limitations

- Extremely high-motion camera pans may require RAFT optical flow rather than Farneback flow for complex deformation.
- Text overlay detection relies on edge-density contours and OCR bounding heuristics; low-contrast watermarks may require secondary model checks.
- Real CLIP model inference runs on CPU when GPU is not attached; batch sizes should remain small for interactive workflows.

## Final Acceptance Status

**Status**: ACCEPTED (All Day 2 acceptance criteria satisfied)

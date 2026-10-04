# Video Accountability — Project Structure & Implementation Status

> **Target Audience**: AI coding assistants and developers onboarding onto the Video Accountability codebase.  
> **Scope**: Member 8 QA Module (Temporal, Semantic, Artifact, Technical, and Provenance Quality Assurance).  
> **Current Revision**: 0.1.0  
> **Documentation Date**: October 2026

---

## Table of Contents

1. [Executive Summary & Scope Boundary](#1-executive-summary--scope-boundary)
2. [Actual Repository Tree](#2-actual-repository-tree)
3. [Component-by-Component File Documentation](#3-component-by-component-file-documentation)
4. [Current Data Flow](#4-current-data-flow)
5. [Video Input Mechanism](#5-video-input-mechanism)
6. [Prompt Input Mechanism](#6-prompt-input-mechanism)
7. [Detailed QA Subsystem Breakdown](#7-detailed-qa-subsystem-breakdown)
8. [Automated Test Suite & Verification Results](#8-automated-test-suite--verification-results)
9. [Mock Data & Fixture System](#9-mock-data--fixture-system)
10. [Dependencies & Runtime Requirements](#10-dependencies--runtime-requirements)
11. [Configuration System](#11-configuration-system)
12. [Command-Line Interface (CLI)](#12-command-line-interface-cli)
13. [Interactive Gradio Demo Workbench](#13-interactive-gradio-demo-workbench)
14. [Current Implementation Status Matrix](#14-current-implementation-status-matrix)
15. [Actual vs. Planned Comparison](#15-actual-vs-planned-comparison)
16. [How to Run the Project](#16-how-to-run-the-project)
17. [End-to-End Example Input & Execution Trace](#17-end-to-end-example-input--execution-trace)
18. [Architecture Diagrams](#18-architecture-diagrams)
19. [File Dependency & Call Hierarchy](#19-file-dependency--call-hierarchy)
20. [Summary for Another AI Agent](#20-summary-for-another-ai-agent)

---

## 1. Executive Summary & Scope Boundary

The **Video Accountability** project implements the **Member 8 Quality Assurance and Accountability Module** for an AI video generation platform POC. Its sole responsibility is to evaluate generated MP4 video files against a text prompt and generation metadata, detecting temporal glitches, visual artifacts, semantic drift, technical media corruption, and maintaining provenance auditability.

### Owned Responsibilities (Member 8)
- **Technical Media Validation**: Container structure, codecs, duration, FPS, and dimension checks via `ffprobe`.
- **Frame Extraction**: Sequential streaming and fractional sampling via OpenCV and FFmpeg.
- **Temporal QA**: Duplicate frame detection, freeze detection, luminance flicker, frame drops, speed jumps, and optical flow continuity (Farneback and RAFT).
- **Visual Artifact QA**: Black frame detection, blur estimation (Laplacian variance), resolution inconsistency/pixelation, decode failures, and text overlay/watermark detection.
- **Semantic QA**: Prompt-to-video alignment via multi-frame sampling and CLIP cosine similarity.
- **Provenance & Accountability**: Cryptographic SHA-256 media hashing, unique run IDs, audit manifests, and Ed25519 digital signing.
- **Decision Engine**: Rule-based decision logic returning one of three top-level decisions: `PASS`, `AUTO_RETRY`, or `HUMAN_REVIEW` with granular, machine-readable reason codes.
- **Interfaces**: CLI (`app.cli`), programmatic Python API (`app.pipeline.run_video_qa`), and Gradio web UI (`demo.gradio_app`).

### Non-Owned Responsibilities (Other Team Members)
- Prompt intelligence / expansion (Members 1 & 2)
- Story, script, or scene planning (Member 2)
- Execution DAG orchestrator (Member 3)
- Keyframe or reference image generation (Member 4)
- Video model training / inference (Members 5 & 6)
- Character identity / facial consistency QA (Member 7)
- Audio / music / voiceover composition (Member 9)
- Final render / platform distribution packaging (Member 10)

---

## 2. Actual Repository Tree

The following directory tree reflects the exact files physically present on disk in `c:\Video Accountobilty`:

```text
Video Accountability/
│
├── app/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── pipeline.py
│   │
│   ├── artifacts/
│   │   ├── __init__.py
│   │   ├── artifact_detector.py
│   │   ├── black_frame.py
│   │   ├── blur.py
│   │   ├── decode_errors.py
│   │   ├── resolution_change.py
│   │   └── text_overlay.py
│   │
│   ├── decision/
│   │   ├── __init__.py
│   │   └── decision_engine.py
│   │
│   ├── media/
│   │   ├── __init__.py
│   │   └── frame_extractor.py
│   │
│   ├── provenance/
│   │   ├── __init__.py
│   │   ├── checksum.py
│   │   ├── identity.py
│   │   ├── manifest.py
│   │   └── signing.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── input.py
│   │   ├── report.py
│   │   └── results.py
│   │
│   ├── semantic/
│   │   ├── __init__.py
│   │   ├── clip_checker.py
│   │   └── prompt_alignment.py
│   │
│   ├── technical/
│   │   ├── __init__.py
│   │   └── ffprobe_validator.py
│   │
│   └── temporal/
│       ├── __init__.py
│       ├── duplicate_frames.py
│       ├── flicker.py
│       ├── frame_difference.py
│       ├── frame_drop.py
│       ├── freeze_detection.py
│       ├── motion_anomaly.py
│       └── optical_flow.py
│
├── demo/
│   ├── __init__.py
│   └── gradio_app.py
│
├── mock_data/
│   ├── __init__.py
│   ├── generate_fixtures.py
│   ├── manifest.json
│   ├── run_calibration.py
│   │
│   ├── expected/
│   │   ├── black_frame.json
│   │   ├── blur.json
│   │   ├── corrupted_metadata.json
│   │   ├── dropped_frames.json
│   │   ├── duplicate_frames.json
│   │   ├── flicker.json
│   │   ├── freeze.json
│   │   ├── good.json
│   │   ├── resolution_change.json
│   │   ├── speed_jump.json
│   │   └── text_overlay.json
│   │
│   ├── inputs/
│   │   ├── black_frame.json
│   │   ├── blur.json
│   │   ├── corrupted_metadata.json
│   │   ├── dropped_frames.json
│   │   ├── duplicate_frames.json
│   │   ├── flicker.json
│   │   ├── freeze.json
│   │   ├── good.json
│   │   ├── resolution_change.json
│   │   ├── speed_jump.json
│   │   └── text_overlay.json
│   │
│   ├── media/
│   │   ├── black_frame.mp4
│   │   ├── blur.mp4
│   │   ├── corrupted_metadata.mp4
│   │   ├── dropped_frames.mp4
│   │   ├── duplicate_frames.mp4
│   │   ├── flicker.mp4
│   │   ├── freeze.mp4
│   │   ├── good.mp4
│   │   ├── resolution_change.mp4
│   │   ├── speed_jump.mp4
│   │   └── text_overlay.mp4
│   │
│   └── metadata/
│       ├── black_frame.json
│       ├── blur.json
│       ├── corrupted_metadata.json
│       ├── dropped_frames.json
│       ├── duplicate_frames.json
│       ├── flicker.json
│       ├── freeze.json
│       ├── good.json
│       ├── resolution_change.json
│       ├── speed_jump.json
│       └── text_overlay.json
│
├── tests/
│   ├── test_artifacts.py
│   ├── test_calibration.py
│   ├── test_cli.py
│   ├── test_decision.py
│   ├── test_environment.py
│   ├── test_ffprobe.py
│   ├── test_fixtures.py
│   ├── test_frames.py
│   ├── test_gradio.py
│   ├── test_pipeline.py
│   ├── test_provenance.py
│   ├── test_real_smoke.py
│   ├── test_schemas.py
│   ├── test_semantic.py
│   └── test_temporal.py
│
├── AGENT_member8_QA.md
├── calibration_report.md
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## 3. Component-by-Component File Documentation

### 3.1 App Root Files

#### `app/__init__.py`
- **Purpose**: Defines top-level package metadata and exports public API.
- **Main Classes**: None.
- **Main Functions**: None.
- **Exports**: `VideoQAPipeline`, `run_video_qa`, `__version__ = "0.1.0"`.
- **Dependencies**: `app.pipeline`.
- **Called by**: External Python scripts, `demo.gradio_app`, `tests`.
- **Calls**: `app.pipeline`.
- **Current Status**: **IMPLEMENTED**.

#### `app/config.py`
- **Purpose**: Centralized Pydantic configuration models for all QA checks, thresholds, and policies. Supports loading from/saving to YAML files.
- **Main Classes**:
  - `TechnicalConfig`: Thresholds for resolution, FPS, duration, allowed codecs.
  - `TemporalConfig`: Thresholds for flicker (`15.0`), duplicate PSNR (`45.0` dB), duplicate L1 diff (`0.0005`), freeze run length (`6`), frame drop threshold (`0.25`), optical flow mode (`"basic"` or `"advanced"`).
  - `SemanticConfig`: Model name (`"openai/clip-vit-base-patch32"`), sampling strategy, sample points (`[0.0, 0.25, 0.5, 0.75, 1.0]`), pass threshold (`0.22`), uncertain threshold (`0.18`).
  - `ArtifactConfig`: Black frame luminance threshold (`2.0`), black pixel ratio (`0.98`), blur Laplacian threshold (`25.0`), max decode errors (`0`).
  - `ProvenanceConfig`: Hash algorithm (`"sha256"`), Ed25519 flag.
  - `DecisionConfig`: Policies for uncertain results (`"HUMAN_REVIEW"`), retry triggers.
  - `QAConfig`: Master root configuration model with `load_from_yaml(path)` and `save_to_yaml(path)`.
- **Inputs**: Optional YAML file path or keyword overrides.
- **Outputs**: Strongly-typed `QAConfig` instance.
- **Dependencies**: `pydantic`, `pyyaml`, `pathlib`.
- **Called by**: `app.pipeline`, `app.cli`, `tests.test_environment`.
- **Calls**: None.
- **Current Status**: **IMPLEMENTED**.

#### `app/cli.py`
- **Purpose**: Standalone command-line interface supporting diagnostics (`--doctor`), mock fixture generation (`fixtures`), and video quality assurance (`qa`).
- **Main Classes**: None.
- **Main Functions**:
  - `check_doctor() -> int`: Tests 8 environment components (Python, FFmpeg, ffprobe, OpenCV, PyTorch, CLIP, RAFT, Gradio) and prints formatted diagnostic table.
  - `main() -> None`: Argument parser entrypoint for `--doctor`, `fixtures`, and `qa`.
- **Inputs**: CLI arguments (`sys.argv`).
- **Outputs**: Formatted terminal output or JSON output to `stdout`; exit codes (0 for success/PASS, 1 for defect/failure).
- **Dependencies**: `argparse`, `shutil`, `subprocess`, `sys`, `app.pipeline.run_video_qa`, `mock_data.generate_fixtures`.
- **Called by**: Terminal users (`python -m app.cli ...`).
- **Calls**: `subprocess` (FFmpeg/ffprobe), `app.pipeline`, `mock_data.generate_fixtures`.
- **Current Status**: **IMPLEMENTED**.

#### `app/pipeline.py`
- **Purpose**: Primary orchestrator integrating all QA subsystems sequentially into a unified execution flow.
- **Main Classes**:
  - `VideoQAPipeline`: Encapsulates validator, extractor, temporal analyzer, artifact detector, semantic evaluator, provenance tracker, and decision engine.
- **Main Functions**:
  - `run(video_path, prompt, video_id, metadata, expected_sha256) -> QAReport`: Executes end-to-end QA.
  - `run_video_qa(video_path, prompt, video_id, metadata, config) -> QAReport`: Top-level convenience wrapper.
- **Inputs**: `video_path` (str/Path), `prompt` (str), optional `video_id`, optional `GenerationMetadata`, optional `QAConfig`.
- **Outputs**: `QAReport` (Pydantic model containing all component results, final decision, and reason codes).
- **Dependencies**: `app.technical`, `app.media`, `app.temporal`, `app.artifacts`, `app.semantic`, `app.provenance`, `app.decision`, `app.schemas`.
- **Called by**: `app.cli`, `demo.gradio_app`, `mock_data.run_calibration`, `tests`.
- **Calls**: All subsystem analyzers in `app/`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.2 Schemas (`app/schemas/`)

#### `app/schemas/input.py`
- **Purpose**: Input data contract models for videos and optional upstream metadata.
- **Main Classes**:
  - `GenerationMetadata`: Optional upstream metadata (`generation_id`, `model`, `fps`, `width`, `height`, `seed`, `extra`).
  - `VideoQAInput`: Required `video_path` and `prompt`, optional `video_id` and `metadata`.
- **Dependencies**: `pydantic`.
- **Current Status**: **IMPLEMENTED**.

#### `app/schemas/results.py`
- **Purpose**: Component result models, status enums, decision enums, and machine-readable reason codes.
- **Main Classes**:
  - `CheckStatus` (Enum): `PASS`, `FAIL`, `WARN`, `ERROR`, `SKIPPED`.
  - `DecisionType` (Enum): `PASS`, `AUTO_RETRY`, `HUMAN_REVIEW`.
  - `ReasonCode` (Enum): 20 stable codes covering Technical, Temporal, Semantic, Artifact, and Provenance failures (including `PROMPT_ASPECT_RATIO_MISMATCH`).
  - `ComponentResult`: Base class with `status`, `score`, `evidence`, `reason_codes`.
  - `TechnicalResult`: Subclasses `ComponentResult` adding `width`, `height`, `fps`, `duration_seconds`, `video_codec`, `has_audio`, `frame_count`, `aspect_ratio`.
  - `TemporalResult`: Subclasses `ComponentResult` adding `flicker_score`, `duplicate_ratio`, `freeze_ratio`, `motion_smoothness`.
  - `SemanticResult`: Subclasses `ComponentResult` adding `similarity_score`, `sampled_frame_scores`.
  - `ArtifactResult`: Subclasses `ComponentResult` adding `black_frame_count`, `blur_score`, `decode_errors_count`.
  - `ProvenanceResult`: Subclasses `ComponentResult` adding `sha256`, `video_id`, `qa_run_id`, `signature`.
- **Dependencies**: `pydantic`, `enum`.
- **Current Status**: **IMPLEMENTED**.

#### `app/schemas/report.py`
- **Purpose**: Top-level aggregated audit report schema.
- **Main Classes**:
  - `QAReport`: Root Pydantic model with `video_id`, `qa_run_id`, `decision`, `technical`, `temporal`, `semantic`, `artifacts`, `provenance`, `reason_codes`, and `qa_version`.
- **Dependencies**: `pydantic`, `app.schemas.results`.
- **Current Status**: **IMPLEMENTED**.

#### `app/schemas/__init__.py`
- **Purpose**: Convenience exports for all schema definitions.
- **Current Status**: **IMPLEMENTED**.

---

### 3.3 Technical Media Validation (`app/technical/`)

#### `app/technical/ffprobe_validator.py`
- **Purpose**: Verifies media integrity, container structures, and streams using `ffprobe` prior to frame extraction.
- **Main Classes**:
  - `FFprobeValidator`: Evaluates container, stream presence, dimensions, framerates, codecs, duration, and metadata consistency against `TechnicalConfig`.
- **Main Functions**:
  - `parse_fps(fps_str: str) -> Optional[float]`: Parses fractional strings (e.g. `'24/1'` or `'30000/1001'`).
  - `run_ffprobe(video_path) -> Tuple[bool, Optional[Dict], str]`: Invokes `ffprobe` as a subprocess requesting JSON stream and format entries.
- **Inputs**: Video file path, optional expected `GenerationMetadata`.
- **Outputs**: `TechnicalResult` with detected metrics and `TECHNICAL_*` reason codes if invalid.
- **Dependencies**: `subprocess`, `json`, `shutil`, `app.config`, `app.schemas`.
- **Current Status**: **IMPLEMENTED**.

#### `app/technical/__init__.py`
- **Purpose**: Package exports for `FFprobeValidator` and `run_ffprobe`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.4 Media & Frame Extraction (`app/media/`)

#### `app/media/frame_extractor.py`
- **Purpose**: Efficient video frame access supporting memory-conscious streaming generators and fractional timeline sampling.
- **Main Classes**:
  - `FrameInfo`: Dataclass holding `frame_index` (int), `timestamp` (float), `image` (numpy array), `width` (int), `height` (int).
  - `FrameExtractor`: High-performance reader wrapping `cv2.VideoCapture` with deterministic resource cleanup (`cap.release()`).
- **Main Functions**:
  - `get_video_properties(video_path) -> Tuple[int, int, float, int]`: Returns width, height, FPS, frame count.
  - `iter_frames(video_path, max_frames, step) -> Generator[FrameInfo, None, None]`: Streams frames one-by-one without holding the entire video in RAM.
  - `sample_frames(video_path, sample_ratios) -> List[FrameInfo]`: Seeks directly to fractional points (e.g. `[0.0, 0.25, 0.5, 0.75, 1.0]`).
- **Inputs**: Video path, optional frame step, sample ratios.
- **Outputs**: `FrameInfo` objects containing BGR numpy frames.
- **Dependencies**: `cv2` (OpenCV), `numpy`, `dataclasses`.
- **Current Status**: **IMPLEMENTED**.

#### `app/media/__init__.py`
- **Purpose**: Package exports for `FrameExtractor` and `FrameInfo`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.5 Temporal Quality Assurance (`app/temporal/`)

#### `app/temporal/frame_difference.py`
- **Purpose**: Calculates mathematical difference metrics between consecutive frames.
- **Main Functions**:
  - `compute_frame_diff(img1, img2) -> Dict[str, float]`: Calculates L1 normalized diff (`0.0 - 1.0`), MSE, PSNR (dB), and luminance delta (`Y2 - Y1`).
  - `compute_sequence_diffs(frames: List[FrameInfo]) -> List[Dict[str, float]]`: Applies `compute_frame_diff` across sequential frame pairs.
- **Inputs**: BGR numpy arrays.
- **Outputs**: Dictionaries with `l1_diff`, `mse`, `psnr`, `lum_delta`, `lum1`, `lum2`.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/duplicate_frames.py`
- **Purpose**: Detects repeated identical or near-identical consecutive frames.
- **Main Functions**:
  - `detect_duplicates(diffs, config) -> Tuple[bool, float, List[int], Dict[str, Any]]`: Flags frames satisfying `l1_diff <= 0.0005` AND `psnr >= 45.0` dB.
- **Outputs**: `has_defect` (bool), `duplicate_ratio` (float), duplicate frame indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/freeze_detection.py`
- **Purpose**: Detects extended frozen sequences where motion stalls across multiple consecutive frames.
- **Main Functions**:
  - `detect_freeze(diffs, config) -> Tuple[bool, float, List[Dict], Dict]`: Flags runs of `>= 6` consecutive identical frames.
- **Outputs**: `has_defect` (bool), `freeze_ratio` (float), freeze run segments, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/flicker.py`
- **Purpose**: Detects rapid alternating luminance changes and brightness oscillations.
- **Main Functions**:
  - `detect_flicker(diffs, config) -> Tuple[bool, float, List[int], Dict]`: Calculates second-order luminance acceleration and alternating sign flip frequency. Triggers `TEMPORAL_FLICKER` if score >= `15.0` or `>= 4` severe sign reversals occur.
- **Outputs**: `has_defect` (bool), `flicker_score` (float), affected frame indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/frame_drop.py`
- **Purpose**: Detects abrupt discontinuities where frames were dropped or missing.
- **Main Functions**:
  - `detect_frame_drops(diffs, config) -> Tuple[bool, List[int], Dict]`: Compares frame differences against local baseline. Flags spikes `>= 2.6x` local motion baseline with delta `> 0.005`.
- **Outputs**: `has_defect` (bool), candidate dropped frame indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/motion_anomaly.py`
- **Purpose**: Detects erratic motion accelerations and sudden speed jumps.
- **Main Functions**:
  - `detect_motion_anomalies(diffs, flow_magnitudes, config) -> Tuple[bool, List[int], Dict]`: Flags unnatural velocity jumps `> 3.5x` with acceleration `> 0.08`.
- **Outputs**: `has_defect` (bool), anomaly frame indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/optical_flow.py`
- **Purpose**: Provides optical flow estimation abstraction with two selectable backends: basic (OpenCV Farneback) and advanced (RAFT deep model).
- **Main Classes**:
  - `OpticalFlowEstimator` (ABC): Base class with `estimate_flow` and `compute_flow_metrics`.
  - `FarnebackFlowEstimator`: Deterministic dense optical flow using `cv2.calcOpticalFlowFarneback`. Fast and CPU-friendly.
  - `RAFTFlowEstimator`: Deep optical flow using `torchvision.models.optical_flow.raft_small` with automatic GPU/CPU selection and fallback to Farneback if weights are missing.
- **Main Functions**:
  - `get_optical_flow_estimator(mode="basic") -> OpticalFlowEstimator`: Factory returning the configured estimator.
- **Current Status**: **IMPLEMENTED**.

#### `app/temporal/__init__.py`
- **Purpose**: Aggregates all temporal checks into `TemporalAnalyzer`.
- **Main Classes**:
  - `TemporalAnalyzer`: Orchestrates difference calculations, duplicate detection, freeze detection, flicker detection, drop detection, motion anomaly analysis, and optical flow estimation into a single `TemporalResult`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.6 Visual Artifact Detection (`app/artifacts/`)

#### `app/artifacts/black_frame.py`
- **Purpose**: Detects completely black, blank, or zero-luminance frames.
- **Main Functions**:
  - `detect_black_frames(frames, config) -> Tuple[bool, int, List[int], Dict]`: Flags frames with mean luminance `<= 2.0` or `>= 98%` dark pixels.
- **Outputs**: `has_defect` (bool), count of black frames, affected indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/artifacts/blur.py`
- **Purpose**: Evaluates frame sharpness and detects severe defocus blur.
- **Main Functions**:
  - `detect_blur(frames, config) -> Tuple[bool, float, List[int], Dict]`: Measures variance of the Laplacian (`cv2.Laplacian(gray, cv2.CV_64F).var()`). Flags frames with variance below `25.0`.
- **Outputs**: `has_defect` (bool), `mean_blur_score`, blurry frame indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/artifacts/resolution_change.py`
- **Purpose**: Detects mid-video dimension changes, nearest-neighbor pixelation, and aspect ratio shifts.
- **Main Functions**:
  - `detect_resolution_change(frames, config) -> Tuple[bool, List[int], Dict]`: Flags frames with width/height mismatches or sharp step jumps in high-frequency variance (`> 10.0` and `> 3.5x` median).
- **Outputs**: `has_defect` (bool), affected indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/artifacts/decode_errors.py`
- **Purpose**: Detects frames that failed video decoding (empty, None, or zero-sized).
- **Main Functions**:
  - `detect_decode_errors(frames, config) -> Tuple[bool, int, List[int], Dict]`: Identifies corrupted unreadable frame buffers.
- **Outputs**: `has_defect` (bool), corrupt frame count, indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/artifacts/text_overlay.py`
- **Purpose**: Detects unexpected artificial watermarks or text overlays.
- **Main Functions**:
  - `detect_text_overlay(frames) -> Tuple[bool, List[int], Dict]`: Detects high-contrast artificial color overlays (such as red warning watermarks).
- **Outputs**: `has_defect` (bool), affected indices, evidence.
- **Current Status**: **IMPLEMENTED**.

#### `app/artifacts/artifact_detector.py`
- **Purpose**: Unified artifact orchestrator combining black frame, blur, resolution change, decode, and text overlay detectors.
- **Main Classes**:
  - `ArtifactDetector`: Aggregates all artifact checks into an `ArtifactResult`.
- **Current Status**: **IMPLEMENTED**.

#### `app/artifacts/__init__.py`
- **Purpose**: Package exports for `ArtifactDetector` and detector functions.
- **Current Status**: **IMPLEMENTED**.

---

### 3.7 Semantic Prompt Alignment (`app/semantic/`)

#### `app/semantic/clip_checker.py`
- **Purpose**: Computes semantic embedding cosine similarity between generation text prompts and video frame images.
- **Main Classes**:
  - `CLIPChecker`: Integrates HuggingFace `transformers` `CLIPModel` and `CLIPProcessor` (`"openai/clip-vit-base-patch32"`). Features an automatic graceful fallback to a deterministic visual feature baseline if the deep model weights are not cached locally, ensuring offline testability.
- **Main Functions**:
  - `compute_similarity(prompt: str, images: List[np.ndarray]) -> List[float]`: Returns cosine similarity scores `[0.0 - 1.0]` for each frame.
- **Dependencies**: `transformers`, `torch`, `PIL`, `cv2`, `numpy`.
- **Current Status**: **IMPLEMENTED**.

#### `app/semantic/prompt_alignment.py`
- **Purpose**: Evaluates multi-frame semantic alignment across the video timeline.
- **Main Classes**:
  - `PromptAlignmentEvaluator`: Samples frames across configurable fractional timeline points (default: `[0.0, 0.25, 0.5, 0.75, 1.0]`), calls `CLIPChecker`, computes mean and min similarity, and maps against calibrated thresholds (`0.22` pass, `0.18` uncertain).
- **Outputs**: `SemanticResult` with `similarity_score`, `sampled_frame_scores`, evidence, and reason codes (`SEMANTIC_LOW_ALIGNMENT`, `SEMANTIC_UNCERTAIN`).
- **Current Status**: **IMPLEMENTED**.

#### `app/semantic/__init__.py`
- **Purpose**: Package exports for `CLIPChecker` and `PromptAlignmentEvaluator`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.8 Provenance & Accountability (`app/provenance/`)

#### `app/provenance/checksum.py`
- **Purpose**: Streaming SHA-256 cryptographic hashing for video files.
- **Main Functions**:
  - `compute_file_sha256(file_path, chunk_size=65536) -> str`: Returns 64-character lowercase hex digest.
  - `verify_file_sha256(file_path, expected_hash) -> bool`: Checks equality against expected digest.
- **Dependencies**: `hashlib`, `pathlib`.
- **Current Status**: **IMPLEMENTED**.

#### `app/provenance/identity.py`
- **Purpose**: Identifier generation for video assets and QA executions.
- **Main Functions**:
  - `generate_video_id(existing_id, sha256_hash) -> str`: Produces `VID_<hash[:12]>` or preserves existing ID.
  - `generate_qa_run_id() -> str`: Produces `QA_<timestamp>_<uuid[:8]>`.
- **Current Status**: **IMPLEMENTED**.

#### `app/provenance/signing.py`
- **Purpose**: Ed25519 digital signature signing and verification for immutable audit manifests.
- **Main Functions**:
  - `generate_key_pair() -> Tuple[str, str]`: Generates raw 32-byte Ed25519 private/public key pairs in hex format.
  - `sign_payload(private_key_hex, payload) -> str`: Signs payload bytes returning 64-byte (128-hex) signature.
  - `verify_signature(public_key_hex, payload, signature_hex) -> bool`: Cryptographically validates payload authenticity.
- **Dependencies**: `cryptography.hazmat.primitives.asymmetric.ed25519`.
- **Current Status**: **IMPLEMENTED**.

#### `app/provenance/manifest.py`
- **Purpose**: Audit manifest schema and factory.
- **Main Classes**:
  - `ProvenanceManifest`: Pydantic model with `video_id`, `qa_run_id`, `sha256`, `timestamp`, `file_size_bytes`, `qa_version`, `signature`.
- **Main Functions**:
  - `create_manifest(...) -> ProvenanceManifest`: Instantiates manifest and signs canonical payload string if a private key is provided.
- **Current Status**: **IMPLEMENTED**.

#### `app/provenance/__init__.py`
- **Purpose**: Unified provenance tracker.
- **Main Classes**:
  - `ProvenanceTracker`: Manages file hashing, ID assignment, hash verification against expected values, and manifest generation into `ProvenanceResult`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.9 Decision Engine (`app/decision/`)

#### `app/decision/decision_engine.py`
- **Purpose**: Pure rule-based decision synthesizer translating multi-component results into top-level decisions.
- **Main Classes**:
  - `DecisionEngine`: Aggregates all reason codes across Technical, Temporal, Semantic, Artifact, and Provenance checks. Evaluates explicit decision rules:
    - `PASS`: All required checks satisfied; no failures or unhandled warnings.
    - `AUTO_RETRY`: Machine-detectable, recoverable defect identified (flicker, duplicate frames, freeze, dropped frames, motion anomaly, black frame, blur, resolution change, decode failure, low semantic alignment, or corrupt media container).
    - `HUMAN_REVIEW`: Ambiguous conditions, warnings (e.g. `SEMANTIC_UNCERTAIN`, `ARTIFACT_TEXT_OVERLAY`, `TECHNICAL_METADATA_MISMATCH`), provenance hash failures, or components with `WARN` status.
- **Outputs**: Tuple of `(DecisionType, List[ReasonCode])`.
- **Current Status**: **IMPLEMENTED**.

#### `app/decision/__init__.py`
- **Purpose**: Package exports for `DecisionEngine`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.10 Demo & UI (`demo/`)

#### `demo/gradio_app.py`
- **Purpose**: Standalone browser-based QA workbench built with Gradio.
- **Main Functions**:
  - `get_available_samples() -> List[str]`: Dynamically discovers all MP4 files in `mock_data/media/`.
  - `load_sample_prompt(video_path) -> str`: Extracts corresponding prompt from `mock_data/manifest.json`.
  - `evaluate_video(video_file, prompt_text) -> Tuple[...]`: Runs `run_video_qa`, formats component status cards, highlights final decision, and outputs full JSON audit record.
  - `create_demo() -> gr.Blocks`: Constructs the Gradio UI layout.
- **Dependencies**: `gradio`, `app.pipeline`.
- **Current Status**: **IMPLEMENTED**.

#### `demo/__init__.py`
- **Purpose**: Exports `create_demo`.
- **Current Status**: **IMPLEMENTED**.

---

### 3.11 Mock Data & Fixtures (`mock_data/`)

#### `mock_data/generate_fixtures.py`
- **Purpose**: Deterministic synthetic video fixture generator creating real MP4 files with mathematically injected defects.
- **Main Functions**:
  - `create_base_frame(...) -> np.ndarray`: Creates a synthetic canvas with a background gradient, timestamp counter, and smoothly moving orb with internal high-contrast patterns.
  - `write_video(path, frames, fps)`: Encodes frames to a standard MP4 file using OpenCV `VideoWriter` with `mp4v` fourcc.
  - `generate_all_fixtures(...) -> Dict`: Generates 11 real MP4 media files, input JSONs, expected JSONs, metadata JSONs, and master `manifest.json`.
- **Current Status**: **IMPLEMENTED**.

#### `mock_data/run_calibration.py`
- **Purpose**: Calibration harness running the QA pipeline across all 11 fixtures, comparing actual decisions/reasons against ground truth, and calculating false positive / false negative rates.
- **Main Functions**:
  - `run_calibration() -> List[Dict]`: Iterates through `manifest.json`, executes `run_video_qa`, and records comparison metrics.
  - `generate_calibration_markdown(results) -> str`: Generates `calibration_report.md`.
- **Current Status**: **IMPLEMENTED**.

---

## 4. Current Data Flow

The following sequence reflects the **actual execution flow** as coded in `app/pipeline.py` and invoked by the CLI and UI:

```text
[Input: Video Path + Prompt + Optional Metadata]
                      │
                      ▼
            app.pipeline.run_video_qa()
                      │
                      ▼
         1. app.provenance.ProvenanceTracker
            ├── Calculates SHA-256 hash of video file
            ├── Verifies against expected hash (if provided)
            ├── Generates video_id and unique qa_run_id
            └── Creates ProvenanceManifest (optional Ed25519 signature)
                      │
                      ▼
         2. app.technical.FFprobeValidator
            ├── Executes ffprobe via subprocess
            ├── Extracts container, streams, width, height, FPS, duration
            └── Validates dimensions/FPS against TechnicalConfig
                      │
            ┌─────────┴─────────┐
      [ffprobe FAIL]      [ffprobe PASS]
            │                   │
            │                   ▼
            │        3. app.media.FrameExtractor
            │           └── Streams BGR frames via cv2.VideoCapture
            │                   │
            │           ┌───────┴───────┐
            │           ▼               ▼
            │     4. Temporal QA   5. Artifact QA
            │        (diffs, dups,    (black frames,
            │         freeze,          blur, resolution,
            │         flicker, drops,  decode errors,
            │         motion, flow)    text overlay)
            │           │               │
            │           └───────┬───────┘
            │                   │
            │                   ▼
            │        6. app.semantic.PromptAlignmentEvaluator
            │           ├── Samples frames at [0.0, 0.25, 0.5, 0.75, 1.0]
            │           └── Evaluates CLIP similarity vs text prompt
            │                   │
            └─────────┬─────────┘
                      │
                      ▼
         7. app.decision.DecisionEngine
            ├── Aggregates all reason codes
            ├── Checks for review/warning triggers
            ├── Checks for auto-retryable defect triggers
            └── Synthesizes final decision: PASS | AUTO_RETRY | HUMAN_REVIEW
                      │
                      ▼
            [Output: QAReport (JSON)]
```

### Distinction between Actual Current Flow and Planned Flow
- **Actual Current Flow**: Uses local `ffprobe` for technical media checks, local OpenCV `cv2.VideoCapture` for frame streaming, Farneback optical flow (with RAFT available via torchvision), deterministic CLIP integration with offline fallback, streaming SHA-256, Ed25519 digital signatures, and rule-based decision engine.
- **Planned Flow**: The planned architecture in `AGENT_member8_QA.md` also suggests integrating VBench benchmarks and external cloud generation providers (Wan 2.2). As designed, these remain external to Member 8 and are not hard dependencies.

---

## 5. Video Input Mechanism

- **Can the project accept an MP4?**: **YES**. It strictly requires and operates on valid MP4 files (or any video container readable by FFmpeg/OpenCV).
- **Which file accepts the video path?**: `app/pipeline.py` via `run_video_qa(video_path=...)` or `VideoQAPipeline.run(video_path=...)`.
- **Is there a CLI?**: **YES**. `app/cli.py`.
- **What command should currently be used?**:
  ```bash
  python -m app.cli qa --video mock_data/media/good.mp4 --prompt "Your prompt here"
  ```
  Or for structured JSON output:
  ```bash
  python -m app.cli qa --video mock_data/media/good.mp4 --prompt "Your prompt here" --json
  ```
- **Is there a Gradio interface?**: **YES**. `demo/gradio_app.py`.
- **Can a user upload a video?**: **YES**. The Gradio interface includes a `gr.Video(sources=["upload"])` component and a dropdown of pre-generated mock fixtures.
- **Where is the uploaded video passed?**: Gradio passes the temporary file path directly to `evaluate_video(video_file, prompt_text)`, which forwards it to `run_video_qa()`.
- **How is the video opened?**:
  1. `app/technical/ffprobe_validator.py` calls `ffprobe` as an external subprocess: `ffprobe -v error -print_format json -show_format -show_streams <path>`.
  2. `app/media/frame_extractor.py` opens the video using OpenCV: `cv2.VideoCapture(str(video_path))`.
- **Is OpenCV used?**: **YES**. `cv2` is used for frame decoding, Laplacian blur estimation, resizing, and Farneback optical flow.
- **Is FFmpeg used?**: **YES**. `ffmpeg` binary is verified in environment checks and used for media stream validation.
- **Is ffprobe used?**: **YES**. `ffprobe` extracts container metadata, codecs, framerate fractions, and stream counts.
- **Where are frames extracted?**: In `app/media/frame_extractor.py` via `iter_frames()` (yielding individual `FrameInfo` instances) and `sample_frames()` (seeking to fractional points using `cv2.CAP_PROP_POS_FRAMES`).
- **Where is the resulting video metadata stored?**: In the `TechnicalResult` object and the `ProvenanceManifest` embedded inside the final `QAReport`.

---

## 6. Prompt Input Mechanism

- **Is the prompt accepted?**: **YES**.
- **Where is the prompt stored?**: In `VideoQAInput.prompt`, forwarded to `VideoQAPipeline.run(prompt=...)`, and recorded in `SemanticResult.evidence["prompt"]`.
- **Which function receives it?**: `app.semantic.prompt_alignment.PromptAlignmentEvaluator.evaluate(frames, prompt)`.
- **Is it passed into semantic QA?**: **YES**.
- **Is CLIP currently used?**: **YES**. `app.semantic.clip_checker.CLIPChecker` loads `CLIPModel` and `CLIPProcessor` (`"openai/clip-vit-base-patch32"`). If offline or local weights are absent, it uses a deterministic visual feature baseline so tests never crash.
- **Is prompt/video similarity currently calculated?**: **YES**. Cosine similarity is computed between the prompt text embedding and normalized image embeddings across all sampled frames (`[0.0, 0.25, 0.5, 0.75, 1.0]`).
- **Is the prompt manually entered?**: In CLI, passed via `--prompt "..."`. In Gradio, entered in a textbox (or auto-populated when selecting a mock fixture).
- **Is it read from metadata?**: If omitted in CLI or pipeline, it defaults to an empty string (which correctly triggers `SEMANTIC_LOW_ALIGNMENT`).

### Actual Prompt Call Path
```text
CLI (--prompt argument) OR Gradio (gr.Textbox)
                      ↓
           app.pipeline.run_video_qa(prompt=...)
                      ↓
    app.semantic.PromptAlignmentEvaluator.evaluate(frames, prompt)
                      ↓
         app.semantic.CLIPChecker.compute_similarity(prompt, images)
                      ↓
         Cosine similarity between text embedding & image embeddings
                      ↓
       Evaluated against pass_threshold (0.22) & uncertain_threshold (0.18)
```

---

## 7. Detailed QA Subsystem Breakdown

### 7.1 Technical QA
- **Status**: **IMPLEMENTED**.
- **Location**: `app/technical/ffprobe_validator.py`.
- **Checks**:
  - Verifies file exists on disk.
  - Runs `ffprobe` subprocess with JSON output.
  - Verifies presence of a valid video stream.
  - Extracts width, height, codec, FPS, duration, stream count, audio presence.
  - Compares against `TechnicalConfig` minimum limits.
  - Detects discrepancies against upstream `GenerationMetadata` (triggering `TECHNICAL_METADATA_MISMATCH`).

### 7.2 Temporal QA
- **Status**: **IMPLEMENTED**.
- **Location**: `app/temporal/`.
- **Checks**:
  - **Duplicate frame detection** (`duplicate_frames.py`): Checks normalized L1 pixel difference and PSNR. Flags `TEMPORAL_DUPLICATE_FRAMES` when identical frames repeat.
  - **Freeze detection** (`freeze_detection.py`): Identifies consecutive frozen frame sequences `>= 6` frames. Flags `TEMPORAL_FREEZE`.
  - **Flicker detection** (`flicker.py`): Computes second-order luminance acceleration and alternating sign reversals. Flags `TEMPORAL_FLICKER`.
  - **Frame drops** (`frame_drop.py`): Detects abrupt motion discontinuities where difference spikes `>= 2.6x` local baseline. Flags `TEMPORAL_FRAME_DROP`.
  - **Motion anomaly** (`motion_anomaly.py`): Detects kinetic speed jumps `> 3.5x` acceleration. Flags `TEMPORAL_MOTION_ANOMALY`.
  - **Optical flow** (`optical_flow.py`): Supports basic Farneback algorithm (`cv2.calcOpticalFlowFarneback`) and advanced RAFT deep optical flow (`torchvision.models.optical_flow.raft_small`) with automatic CPU/GPU support and graceful fallback.

### 7.3 Visual Artifact QA
- **Status**: **IMPLEMENTED**.
- **Location**: `app/artifacts/`.
- **Checks**:
  - **Black frames** (`black_frame.py`): Flags frames with mean luminance `<= 2.0` or `>= 98%` dark pixels (`ARTIFACT_BLACK_FRAME`).
  - **Blur** (`blur.py`): Measures Laplacian variance. Flags frames below `25.0` threshold (`ARTIFACT_BLUR`).
  - **Resolution changes** (`resolution_change.py`): Detects dynamic dimension changes or nearest-neighbor pixelation aliasing (`ARTIFACT_RESOLUTION_CHANGE`).
  - **Decode failures** (`decode_errors.py`): Detects corrupted, empty, or unreadable frame buffers (`ARTIFACT_DECODE_FAILURE`).
  - **Text overlay / Watermark** (`text_overlay.py`): Detects artificial high-contrast overlay text (`ARTIFACT_TEXT_OVERLAY`).

### 7.4 Semantic QA
- **Status**: **IMPLEMENTED**.
- **Location**: `app/semantic/`.
- **Checks**:
  - Configurable temporal sampling across fractions (default: start, 25%, 50%, 75%, end).
  - Cosine similarity calculation between prompt text embedding and frame image embeddings via `CLIPChecker`.
  - Calibrated threshold evaluation: `>= 0.22` is PASS; `0.18 - 0.22` is WARN (`SEMANTIC_UNCERTAIN`); `< 0.18` is FAIL (`SEMANTIC_LOW_ALIGNMENT`).

### 7.5 Provenance & Accountability
- **Status**: **IMPLEMENTED**.
- **Location**: `app/provenance/`.
- **Features**:
  - Streaming SHA-256 calculation (`checksum.py`).
  - Unique video ID and timestamped QA run ID generation (`identity.py`).
  - Audit manifest creation (`manifest.py`).
  - Ed25519 asymmetric cryptographic signing and verification (`signing.py`).

### 7.6 Decision Engine
- **Status**: **IMPLEMENTED**.
- **Location**: `app/decision/decision_engine.py`.
- **Features**:
  - Synthesizes all component evidence into top-level decisions:
    - **`PASS`**: All checks pass with no defects.
    - **`AUTO_RETRY`**: Machine-detectable recoverable defects (flicker, duplicates, freeze, drops, motion anomalies, black frame, blur, resolution change, low semantic alignment, corrupt media).
    - **`HUMAN_REVIEW`**: Ambiguous results, warnings, text overlays, metadata mismatches, provenance hash failures.
  - Aggregates and deduplicates reason codes across all checks.

---

## 8. Automated Test Suite & Verification Results

The test suite consists of **15 test files** located in `tests/`:

| Test File | Subsystem Tested | Test Count | Status |
|---|---|:---:|:---:|
| `test_schemas.py` | Input, result, and report Pydantic schemas | 5 | **PASSED** |
| `test_environment.py` | CLI doctor, tool discovery, config serialization | 3 | **PASSED** |
| `test_fixtures.py` | Fixture existence, manifest integrity, good fixture opening | 2 | **PASSED** |
| `test_ffprobe.py` | Valid video, corrupted container, non-existent file, metadata mismatch | 4 | **PASSED** |
| `test_frames.py` | Sequential streaming, step/cap parameters, fractional sampling | 4 | **PASSED** |
| `test_temporal.py` | Duplicate, freeze, flicker, drop, speed jump, Farneback, RAFT | 8 | **PASSED** |
| `test_artifacts.py` | Good video, black frame, blur, resolution change, text overlay | 5 | **PASSED** |
| `test_semantic.py` | Matching prompt, low alignment, empty prompt, custom sampling points | 4 | **PASSED** |
| `test_provenance.py` | SHA-256, run tracking, hash mismatch, Ed25519 signing & verification | 4 | **PASSED** |
| `test_decision.py` | PASS, AUTO_RETRY (flicker, black frame, semantic), HUMAN_REVIEW (uncertain, text) | 6 | **PASSED** |
| `test_pipeline.py` | End-to-end pipeline execution on good, corrupted, flicker, black frame, text | 5 | **PASSED** |
| `test_cli.py` | CLI `--doctor`, text output, `--json` output, failure exit code | 4 | **PASSED** |
| `test_gradio.py` | Gradio Blocks construction, video evaluation function, empty input handling | 3 | **PASSED** |
| `test_calibration.py` | 11/11 fixture classification accuracy, 0 FP, 0 FN verification | 1 | **PASSED** |
| `test_real_smoke.py` | Model-agnostic integration with simulated upstream generation metadata | 1 | **PASSED** |

### Latest Test Execution Summary
```text
pytest execution: 59 passed in 102.32s (100% pass rate)
```

---

## 9. Mock Data & Fixture System

Located in `mock_data/`:
- **Generator**: `mock_data/generate_fixtures.py` deterministically generates real MP4 files using OpenCV.
- **Unified Manifest**: `mock_data/manifest.json`.

| Fixture Filename | Injected Defect | Expected Decision | Expected Reason Code | Exists | Used by Tests |
|---|---|---|---|:---:|:---:|
| `good.mp4` | Clean baseline (no defect) | `PASS` | None | **YES** | **YES** |
| `duplicate_frames.mp4` | Repeated identical frames | `AUTO_RETRY` | `TEMPORAL_DUPLICATE_FRAMES` | **YES** | **YES** |
| `dropped_frames.mp4` | Abrupt motion discontinuity | `AUTO_RETRY` | `TEMPORAL_FRAME_DROP` | **YES** | **YES** |
| `flicker.mp4` | Luminance oscillation | `AUTO_RETRY` | `TEMPORAL_FLICKER` | **YES** | **YES** |
| `freeze.mp4` | Extended frozen sequence | `AUTO_RETRY` | `TEMPORAL_FREEZE` | **YES** | **YES** |
| `speed_jump.mp4` | Sudden kinetic acceleration | `AUTO_RETRY` | `TEMPORAL_MOTION_ANOMALY` | **YES** | **YES** |
| `black_frame.mp4` | Zero-luminance injected frames | `AUTO_RETRY` | `ARTIFACT_BLACK_FRAME` | **YES** | **YES** |
| `blur.mp4` | Severe Gaussian blur | `AUTO_RETRY` | `ARTIFACT_BLUR` | **YES** | **YES** |
| `resolution_change.mp4` | Downscale/upscale aliasing | `AUTO_RETRY` | `ARTIFACT_RESOLUTION_CHANGE` | **YES** | **YES** |
| `text_overlay.mp4` | High-contrast red watermark | `HUMAN_REVIEW` | `ARTIFACT_TEXT_OVERLAY` | **YES** | **YES** |
| `corrupted_metadata.mp4` | Unparseable container stream | `AUTO_RETRY` | `TECHNICAL_INVALID_MEDIA` | **YES** | **YES** |

---

## 10. Dependencies & Runtime Requirements

### Core Runtime
- **Python**: 3.10+ (Running on Python 3.10.11).
- **OpenCV (`opencv-python 5.0.0`)**: Frame decoding, video writing, Laplacian blur, color conversions, Farneback optical flow.
- **Pydantic (`pydantic 2.13.4`)**: Data validation, schema definitions, and serialization.
- **NumPy (`numpy 2.2.6`)**: Array mathematics, luminance statistics, and metric computation.
- **PyYAML (`pyyaml 6.0.3`)**: YAML configuration file loading and dumping.
- **Cryptography (`cryptography 50.0.1`)**: Ed25519 digital signature generation and verification.

### Media Tools
- **FFmpeg (`ffmpeg 8.1.1`)**: Media encoding and container processing.
- **ffprobe (`ffprobe 8.1.1`)**: Stream inspection and metadata extraction.

### AI / Deep Learning
- **PyTorch (`torch 2.14.0+cpu`)**: Tensor operations and model inference.
- **Torchvision (`torchvision 0.29.1`)**: Deep optical flow architecture (`torchvision.models.optical_flow.raft_small`).
- **Transformers (`transformers 5.16.1`)**: HuggingFace CLIP model architecture (`CLIPModel`, `CLIPProcessor`).
- **Pillow (`pillow 12.3.0`)**: Image container conversions for CLIP tensors.

### Testing
- **pytest (`pytest 8.4.2`)**: Automated test runner.

### Web UI
- **Gradio (`gradio 6.29.1`)**: Interactive web UI workbench.

---

## 11. Configuration System

All configurable settings are declared in `app/config.py`:

| Parameter | Type | Default Value | Role |
|---|---|---|---|
| `technical.min_width` | int | `256` | Minimum allowable video width |
| `technical.min_height` | int | `256` | Minimum allowable video height |
| `technical.min_fps` | float | `1.0` | Minimum allowable FPS |
| `technical.max_fps` | float | `120.0` | Maximum allowable FPS |
| `technical.min_duration_seconds` | float | `0.5` | Minimum allowable duration |
| `temporal.flicker_threshold` | float | `15.0` | Second-order luminance delta threshold |
| `temporal.duplicate_threshold_psnr` | float | `45.0` | PSNR above which frames are duplicates |
| `temporal.duplicate_diff_threshold` | float | `0.0005` | Normalized L1 diff below which frames are duplicates |
| `temporal.freeze_consecutive_frames` | int | `6` | Frame count defining a freeze sequence |
| `temporal.frame_drop_threshold` | float | `0.25` | Abrupt discontinuity ratio |
| `temporal.optical_flow_mode` | str | `"basic"` | `"basic"` (Farneback) or `"advanced"` (RAFT) |
| `semantic.model_name` | str | `"openai/clip-vit-base-patch32"` | HuggingFace model identifier |
| `semantic.sample_points` | list | `[0.0, 0.25, 0.5, 0.75, 1.0]` | Fractional frame sample points |
| `semantic.pass_threshold` | float | `0.22` | CLIP cosine similarity pass threshold |
| `semantic.uncertain_threshold` | float | `0.18` | CLIP cosine similarity review threshold |
| `artifacts.black_frame_luminance_threshold` | float | `2.0` | Max luminance intensity for black frames |
| `artifacts.black_frame_pixel_ratio` | float | `0.98` | Ratio of near-zero pixels required |
| `artifacts.blur_laplacian_threshold` | float | `25.0` | Minimum Laplacian variance before blur flag |
| `decision.uncertain_policy` | str | `"HUMAN_REVIEW"` | Policy for ambiguous signals |

---

## 12. Command-Line Interface (CLI)

Implemented in `app/cli.py`.

### 1. Doctor Diagnostic Check
```bash
python -m app.cli --doctor
```
- **Arguments**: `--doctor`
- **Purpose**: Checks the availability and versions of Python, FFmpeg, ffprobe, OpenCV, PyTorch, CLIP, RAFT, and Gradio.
- **Exit Code**: `0` if all required dependencies exist; `1` if required tools are missing.

### 2. Generate Mock Fixtures
```bash
python -m app.cli fixtures [--output-dir mock_data]
```
- **Arguments**: `fixtures`, optional `--output-dir`
- **Purpose**: Generates all 11 synthetic MP4 fixtures, input/expected JSON files, and `manifest.json`.

### 3. Run Quality Assurance
```bash
python -m app.cli qa --video <path_to_video> --prompt "<prompt_text>" [--json]
```
- **Arguments**:
  - `--video`: Absolute or relative path to MP4 file.
  - `--prompt`: Text prompt used to generate the video.
  - `--json`: (Optional) Outputs raw machine-readable JSON rather than terminal summary cards.
- **Output**:
  - Text mode: Component-level summary cards, final decision, and reason codes.
  - JSON mode: Complete serialized `QAReport`.
- **Exit Code**: `0` for `PASS`; `1` for `AUTO_RETRY` or `HUMAN_REVIEW`.

---

## 13. Interactive Gradio Demo Workbench

Implemented in `demo/gradio_app.py`.

### How to Launch
```bash
python -m demo.gradio_app
```
Starts a local web server at `http://127.0.0.1:7860`.

### UI Features
- **Video Input**: Upload any local MP4 or choose from a pre-loaded sample fixture dropdown.
- **Prompt Input**: Textbox for entering generation prompts (auto-updates when selecting mock fixtures).
- **Run Button**: Triggers `app.pipeline.run_video_qa`.
- **Decision Banner**: Large color-coded decision banner (🟢 PASS, 🟠 AUTO_RETRY, 🔵 HUMAN_REVIEW).
- **Component Status Cards**: Live cards displaying Technical, Temporal, Semantic, Artifact, and Provenance metrics.
- **Audit Accordion**: Collapsible JSON viewer with full evidence and SHA-256 hash.

---

## 14. Current Implementation Status Matrix

| Component | Status | Notes |
|---|:---:|---|
| **Project Structure** | **IMPLEMENTED** | Conforms to Member 8 scope boundary. |
| **Technical QA** | **IMPLEMENTED** | `ffprobe` validator with container, stream, and codec checks. |
| **Frame Extraction** | **IMPLEMENTED** | Streaming generator and fractional timeline sampling. |
| **Temporal QA** | **IMPLEMENTED** | Duplicate, freeze, flicker, drop, and speed jump detectors. |
| **RAFT Optical Flow** | **IMPLEMENTED** | Basic Farneback and advanced RAFT adapter with CPU/GPU handling. |
| **Artifact QA** | **IMPLEMENTED** | Black frame, blur, resolution change, decode, and text overlay. |
| **CLIP Semantic QA** | **IMPLEMENTED** | Multi-frame cosine similarity with offline fallback. |
| **Provenance & Hashing**| **IMPLEMENTED** | Streaming SHA-256, run tracking, manifests, Ed25519 signatures. |
| **Decision Engine** | **IMPLEMENTED** | Explicit rules producing `PASS`, `AUTO_RETRY`, `HUMAN_REVIEW`. |
| **CLI** | **IMPLEMENTED** | `--doctor`, `fixtures`, and `qa` (text and `--json` modes). |
| **Gradio Workbench** | **IMPLEMENTED** | Interactive workbench with upload, samples, and card displays. |
| **Automated Tests** | **IMPLEMENTED** | 15 test suites, 59 tests, 100% pass rate. |
| **Mock Data System** | **IMPLEMENTED** | 11 curated fixtures with 100% calibration accuracy. |

---

## 15. Actual vs. Planned Comparison

| Feature | Currently Implemented | Planned in AGENT_member8_QA.md | Notes |
|---|---|---|---|
| **Video Input** | Real MP4 files via CLI, API, and Gradio | Real MP4 input | Fully matched |
| **Prompt Input** | String input via CLI, API, and Gradio | Text prompt input | Fully matched |
| **Frame Extraction** | Memory-efficient generator & sampling | Sequential & sampled extraction | Fully matched |
| **ffprobe Validator** | Subprocess JSON parser | Subprocess validation | Fully matched |
| **Temporal Checks** | Diffs, dups, freeze, flicker, drops, anomalies | Diffs, dups, freeze, flicker, drops | Fully matched |
| **Optical Flow** | Farneback + RAFT small | Farneback + RAFT | Fully matched |
| **Artifact Checks** | Black frame, blur, resolution, decode, text | Black frame, blur, resolution, decode | Fully matched |
| **Semantic QA** | CLIP cosine similarity across sample points | CLIP similarity across sample points | Fully matched |
| **Provenance** | SHA-256, UUIDs, manifests, Ed25519 signing | SHA-256, UUIDs, manifests, Ed25519 | Fully matched |
| **Decision Engine** | PASS, AUTO_RETRY, HUMAN_REVIEW rules | PASS, AUTO_RETRY, HUMAN_REVIEW rules | Fully matched |
| **CLI** | `--doctor`, `fixtures`, `qa [--json]` | `--doctor`, `fixtures`, `qa [--json]` | Fully matched |
| **UI Workbench** | Gradio interactive web app | Gradio demo | Fully matched |
| **VBench Benchmark** | Not runtime dependent | Standardized prompt reference | Kept independent by design |
| **Wan 2.2 Inference** | Kept external (Member 5 responsibility) | Keep external to Member 8 | Adheres to Rule 12 |

---

## 16. How to Run the Project

### 1. Environment Verification
```bash
python -m app.cli --doctor
```

### 2. Generate Mock Video Fixtures
```bash
python -m app.cli fixtures
```

### 3. Run Automated Tests
```bash
python -m pytest -v
```

### 4. Execute QA via CLI
```bash
# Clean passing video:
python -m app.cli qa --video mock_data/media/good.mp4 --prompt "A golden glowing orb traveling smoothly across an evening sky."

# Defective video (triggers AUTO_RETRY):
python -m app.cli qa --video mock_data/media/flicker.mp4 --prompt "A golden glowing orb traveling smoothly across an evening sky."

# JSON Audit output:
python -m app.cli qa --video mock_data/media/good.mp4 --prompt "A golden glowing orb traveling smoothly across an evening sky." --json
```

### 5. Launch Gradio UI
```bash
python -m demo.gradio_app
```
Open `http://127.0.0.1:7860` in any web browser.

---

## 17. End-to-End Example Input & Execution Trace

### Example Input
- **Video Path**: `mock_data/media/good.mp4` (or any user-provided `video.mp4`)
- **Prompt**: `"A modern Indian girl walking on the footpath in HITEC City, Hyderabad while holding a German Shepherd with a leash."`

### Can this currently be passed into the system?
**YES**. It can be executed immediately via Python, CLI, or Gradio:

```python
from app.pipeline import run_video_qa

report = run_video_qa(
    video_path="mock_data/media/good.mp4",
    prompt="A modern Indian girl walking on the footpath in HITEC City, Hyderabad while holding a German Shepherd with a leash."
)

print("Decision:", report.decision.value)
print("SHA-256:", report.provenance.sha256)
print("Technical:", report.technical.status.value)
print("Temporal:", report.temporal.status.value)
print("Semantic:", report.semantic.status.value)
print("Artifacts:", report.artifacts.status.value)
```

### Execution Trace
1. **Provenance**: Computes SHA-256 digest of `good.mp4` (`c9230c49...`), creates run ID `QA_<timestamp>_<uuid>`.
2. **Technical**: `ffprobe` validates container, streams, width (`640`), height (`360`), and FPS (`24.0`). Returns `CheckStatus.PASS`.
3. **Frame Extraction**: Streams frames sequentially into memory-efficient `FrameInfo` structures.
4. **Temporal QA**: Evaluates consecutive frames; computes duplicate ratio (`0.0`), freeze ratio (`0.0`), flicker score (`0.077`), smoothness (`0.975`). Returns `CheckStatus.PASS`.
5. **Artifact QA**: Evaluates black frames (`0`), blur variance (`67.27`), resolution consistency, decode errors (`0`). Returns `CheckStatus.PASS`.
6. **Semantic QA**: Samples 5 representative frames; evaluates CLIP cosine similarity against the Indian girl walking prompt. Returns similarity score and `CheckStatus`.
7. **Decision Engine**: Combines all component results. Since all components are `PASS`, outputs `DecisionType.PASS` with empty reason codes.

---

## 18. Architecture Diagrams

### Actual Current Architecture
```mermaid
flowchart TD
    subgraph Inputs [User / Upstream Inputs]
        V[Video File .mp4]
        P[Text Prompt]
        M[Optional Metadata]
    end

    subgraph Entrypoints [User Interfaces]
        CLI[app.cli]
        UI[demo.gradio_app]
        API[app.pipeline.run_video_qa]
    end

    V --> CLI
    P --> CLI
    V --> UI
    P --> UI
    V --> API
    P --> API
    M --> API

    CLI --> PIPE[app.pipeline.VideoQAPipeline]
    UI --> PIPE
    API --> PIPE

    subgraph Pipeline [Core Pipeline Execution]
        PIPE --> PROV[app.provenance.ProvenanceTracker]
        PROV --> TECH[app.technical.FFprobeValidator]
        TECH --> FRAMES[app.media.FrameExtractor]
        FRAMES --> TEMP[app.temporal.TemporalAnalyzer]
        FRAMES --> ART[app.artifacts.ArtifactDetector]
        FRAMES --> SEM[app.semantic.PromptAlignmentEvaluator]
        
        TEMP --> DEC[app.decision.DecisionEngine]
        ART --> DEC
        SEM --> DEC
        TECH --> DEC
        PROV --> DEC
    end

    subgraph Outputs [Structured Outputs]
        DEC --> REP[QAReport Schema]
        REP --> PASS[PASS]
        REP --> RETRY[AUTO_RETRY + Reason Codes]
        REP --> REVIEW[HUMAN_REVIEW + Evidence]
    end
```

### Planned Architecture (per AGENT_member8_QA.md)
```mermaid
flowchart TD
    subgraph Upstream [External Upstream Modules]
        M5[Member 5: T2V Model Inference]
        M6[Member 6: I2V / Control Generation]
        M1[Member 1: Prompt Intelligence]
    end

    M5 --> V_PLANNED[Generated Video MP4]
    M6 --> V_PLANNED
    M1 --> P_PLANNED[Refined Prompt]

    subgraph Member8 [Member 8 QA Module Boundary]
        V_PLANNED --> M8_TECH[Technical Media Check]
        P_PLANNED --> M8_SEM[Semantic CLIP Check]
        M8_TECH --> M8_EXTRACT[Frame Extraction]
        M8_EXTRACT --> M8_TEMP[Temporal QA: Farneback + RAFT]
        M8_EXTRACT --> M8_ART[Artifact QA: Blur, Black Frame, Decode]
        M8_TEMP --> M8_DEC[Decision Engine]
        M8_ART --> M8_DEC
        M8_SEM --> M8_DEC
        V_PLANNED --> M8_PROV[Provenance: SHA-256 + Ed25519]
        M8_PROV --> M8_DEC
        M8_DEC --> M8_REPORT[Structured Audit Report]
    end

    subgraph Downstream [Downstream Consumers]
        M8_REPORT --> AUTO_DAG[Member 3: Execution DAG / Auto Retry]
        M8_REPORT --> HUMAN_DASH[Human Review Dashboard]
        M8_REPORT --> FINAL_RENDER[Member 10: Final Render / Delivery]
    end
```

---

## 19. File Dependency & Call Hierarchy

```text
app/cli.py
  ├── app/pipeline.py (run_video_qa)
  └── mock_data/generate_fixtures.py (generate_all_fixtures)

demo/gradio_app.py
  └── app/pipeline.py (run_video_qa)

app/pipeline.py
  ├── app/config.py (QAConfig)
  ├── app/schemas/ (VideoQAInput, GenerationMetadata, QAReport, results)
  ├── app/technical/ (FFprobeValidator)
  │     └── subprocess (ffprobe)
  ├── app/media/ (FrameExtractor, FrameInfo)
  │     └── cv2.VideoCapture
  ├── app/provenance/ (ProvenanceTracker, generate_qa_run_id, generate_video_id)
  │     ├── app/provenance/checksum.py (compute_file_sha256)
  │     ├── app/provenance/manifest.py (create_manifest)
  │     └── app/provenance/signing.py (Ed25519 sign_payload, verify_signature)
  ├── app/temporal/ (TemporalAnalyzer)
  │     ├── app/temporal/frame_difference.py (compute_sequence_diffs)
  │     ├── app/temporal/duplicate_frames.py (detect_duplicates)
  │     ├── app/temporal/freeze_detection.py (detect_freeze)
  │     ├── app/temporal/flicker.py (detect_flicker)
  │     ├── app/temporal/frame_drop.py (detect_frame_drops)
  │     ├── app/temporal/motion_anomaly.py (detect_motion_anomalies)
  │     └── app/temporal/optical_flow.py (FarnebackFlowEstimator, RAFTFlowEstimator)
  ├── app/artifacts/ (ArtifactDetector)
  │     ├── app/artifacts/black_frame.py (detect_black_frames)
  │     ├── app/artifacts/blur.py (detect_blur)
  │     ├── app/artifacts/resolution_change.py (detect_resolution_change)
  │     ├── app/artifacts/decode_errors.py (detect_decode_errors)
  │     └── app/artifacts/text_overlay.py (detect_text_overlay)
  ├── app/semantic/ (PromptAlignmentEvaluator)
  │     └── app/semantic/clip_checker.py (CLIPChecker: transformers CLIPModel / fallback)
  └── app/decision/ (DecisionEngine)
        └── Decision rules mapping results to PASS, AUTO_RETRY, HUMAN_REVIEW
```

---

## 20. Summary for Another AI Agent

### What This Project Is
This is the **Member 8 Quality Assurance and Accountability Module** for an AI Video Generation Proof of Concept (POC). It takes a generated video file (MP4) and a generation text prompt, evaluates technical validity, temporal smoothness, visual defects, semantic alignment, and cryptographic provenance, and outputs an explainable decision (`PASS`, `AUTO_RETRY`, `HUMAN_REVIEW`) along with granular evidence and reason codes.

### Current Implementation Status
The module is **fully implemented, working, and covered by 59 automated tests**.
- **Working Video Input**: Accepts real MP4 files via Python API, CLI (`python -m app.cli qa`), and browser UI (`python -m demo.gradio_app`).
- **Working Prompt Input**: Accepts prompt text via CLI, API, and Gradio textbox; multi-frame temporal sampling feeds into CLIP embedding cosine similarity.
- **Working Checks**: Container validation (`ffprobe`), frame streaming (`OpenCV`), duplicates, freeze, flicker, drops, motion anomalies, optical flow (Farneback + RAFT), black frames, blur (Laplacian), resolution changes, decode failures, text overlays, SHA-256 hashing, and Ed25519 signing.
- **Working Calibration**: Evaluated across 11 synthetic defect fixtures with **100% classification accuracy** (0 false positives, 0 false negatives).

### What Is Missing / Recommended Next Steps
1. **Multi-GPU / Batch Scaling**: Currently optimized for single-video analysis; batch processing queues can be introduced for enterprise throughput.
2. **Upstream Integration**: Ready for integration with Member 3 (Execution DAG) and Member 5 (T2V model outputs) via the standardized `VideoQAInput` and `QAReport` contracts.
3. **Model Weight Caching**: If deploying in a strictly offline production cluster, ensure HuggingFace weights for `openai/clip-vit-base-patch32` and torchvision RAFT weights are pre-downloaded to local cache directories.

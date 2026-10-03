# Member 8 QA Module — AI Video Quality Assurance & Accountability

Production-grade, automated quality assurance and cryptographic provenance verification module for AI-generated video pipelines.

---

## Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Scope Boundaries](#2-scope-boundaries)
3. [Complete Project File Structure](#3-complete-project-file-structure)
4. [Installation & Environment Setup](#4-installation--environment-setup)
5. [Quick Start](#5-quick-start)
6. [Comprehensive Usage Guide (All Components)](#6-comprehensive-usage-guide-all-components)
   - [A. End-to-End Pipeline API](#a-end-to-end-pipeline-api)
   - [B. Technical Media Validator (`app.technical`)](#b-technical-media-validator-apptechnical)
   - [C. Temporal Continuity & Shot Boundaries (`app.temporal`)](#c-temporal-continuity--shot-boundaries-apptemporal)
   - [D. Visual Artifact & Glitch Detector (`app.artifacts`)](#d-visual-artifact--glitch-detector-appartifacts)
   - [E. Semantic Alignment with CLIP ViT-B/32 (`app.semantic`)](#e-semantic-alignment-with-clip-vit-b32-appsemantic)
   - [F. Provenance Tracker & Ed25519 Signer (`app.provenance`)](#f-provenance-tracker--ed25519-signer-appprovenance)
   - [G. Frame Extractor (`app.media`)](#g-frame-extractor-appmedia)
   - [H. Deterministic Decision Engine (`app.decision`)](#h-deterministic-decision-engine-appdecision)
   - [I. Command-Line Interface (`app.cli`)](#i-command-line-interface-appcli)
   - [J. Interactive Gradio QA Workbench (`demo.gradio_app`)](#j-interactive-gradio-qa-workbench-demogradio_app)
   - [K. Mock Fixture Generation & Calibration (`mock_data`)](#k-mock-fixture-generation--calibration-mock_data)
7. [Configuration Reference (`QAConfig`)](#7-configuration-reference-qaconfig)
8. [Machine-Readable Reason Codes](#8-machine-readable-reason-codes)
9. [Testing & Test Suite Breakdown](#9-testing--test-suite-breakdown)
10. [Validation Reports & Empirical Benchmarks](#10-validation-reports--empirical-benchmarks)

---

## 1. System Overview & Architecture

The **Member 8 QA Module** provides automated, model-agnostic evaluation of AI-generated video assets. It operates between video generation/rendering engines and downstream delivery pipelines, performing automated multi-dimensional quality checks, visual defect detection, semantic prompt alignment, and cryptographic tamper-evident signing.

```
                      ┌────────────────────────────────────────┐
                      │    AI Video Input (.mp4) + Prompt      │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │                      VideoQAPipeline Orchestrator                      │
     ├────────────────────────────────────────────────────────────────────────┤
     │  1. Technical Validation (ffprobe container, streams, codec, FPS)      │
     │  2. Frame Extraction     (uniform / step / fractional sampling)        │
     │  3. Temporal QA          (shot boundaries, optical flow, flicker, drop)│
     │  4. Visual Artifacts     (black frames, blur, text overlay, decode)    │
     │  5. Semantic Alignment   (OpenAI CLIP ViT-B/32 prompt-image similarity)│
     │  6. Provenance Tracker   (SHA-256 hashing, unique IDs, Ed25519 signing)│
     └────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │                      Deterministic Decision Engine                     │
     ├────────────────────────────────────────────────────────────────────────┤
     │  Evaluates component evidence and machine-readable reason codes        │
     │  Outputs: PASS  │  AUTO_RETRY  │  HUMAN_REVIEW                         │
     └────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │      Structured JSON QAReport          │
                      └────────────────────────────────────────┘
```

---

## 2. Scope Boundaries

### Owned Responsibilities (Member 8)
- **Technical Media Validation:** Container structure, stream integrity, codec compatibility, duration, FPS, and dimension checks via `ffprobe`/FFmpeg.
- **Temporal Quality Assurance:** Optical flow continuity (Farneback & RAFT), shot-boundary aware frame drop detection, flicker variance, duplicate frame detection, freeze frame detection, and motion anomalies.
- **Visual Artifact Detection:** Black frame detection, blur estimation (Laplacian variance), resolution inconsistency, text overlay detection, and frame decode failure detection.
- **Semantic Prompt Alignment:** Semantic similarity between user prompt and representative sampled video frames using OpenAI CLIP (`openai/clip-vit-base-patch32`).
- **Provenance & Accountability:** Cryptographic SHA-256 media hashing, QA execution run tracking, unique identification (`video_id`, `qa_run_id`), and audit manifests (with Ed25519 digital signing support).
- **Decision Engine:** Deterministic rule-based evaluation translating component evidence and reason codes into top-level decisions: `PASS`, `AUTO_RETRY`, or `HUMAN_REVIEW`.
- **Diagnostic CLI & Workbench:** Standalone execution CLI (`python -m app.cli`) and interactive Gradio workbench (`python -m demo.gradio_app`).

### Non-Owned Responsibilities (Other Team Members)
- Prompt Intelligence & Expansion / NLP (Member 1 / 2)
- Story & Scene Planning / Scriptwriting (Member 2)
- Execution Blueprint / DAG Orchestration (Member 3)
- Reference Image / Keyframe Generation (Member 4)
- Text-to-Video (T2V) Generation Model Inference (Member 5)
- Image-to-Video (I2V) / Animation / Control Generation (Member 6)
- Character Identity & Multi-Scene Visual Consistency QA (Member 7)
- Timeline / Montage / Audio / Subtitle Composition (Member 9)
- Final Render / Encoding / Platform Delivery Validation (Member 10)

---

## 3. Complete Project File Structure

```
c:/Video Accountobilty/
├── README.md                           # Main architecture, usage guide, and reference documentation
├── pyproject.toml                      # Build system, package metadata, and pytest configuration
├── requirements.txt                    # Project Python dependencies (OpenCV, Torch, Transformers, Gradio, etc.)
├── calibration_report.md               # Empirical detector calibration report across 11 test fixtures
├── PROJECT_STRUCTURE.md                # System structure and architectural baseline inventory
│
├── app/                                # Core Member 8 QA package
│   ├── __init__.py                     # Package export: VideoQAPipeline, run_video_qa, __version__
│   ├── config.py                       # Pydantic configuration schemas (QAConfig, TemporalConfig, etc.)
│   ├── pipeline.py                     # VideoQAPipeline orchestrator & run_video_qa entrypoint
│   ├── cli.py                          # Command-line interface (doctor, fixtures, qa subcommands)
│   │
│   ├── artifacts/                      # Visual defect & artifact detection
│   │   ├── __init__.py                 # Exports ArtifactDetector, detect_black_frames, detect_blur, detect_decode_glitches
│   │   ├── artifact_detector.py        # ArtifactDetector orchestrating black frame, blur, decode checks
│   │   ├── black_frame.py              # Luminance & zero-pixel ratio black frame detector
│   │   ├── blur_detection.py           # Laplacian variance blur estimation
│   │   └── decode_glitch.py            # Stream corruption and decode failure detection
│   │
│   ├── decision/                       # Deterministic decision engine
│   │   ├── __init__.py                 # Exports DecisionEngine, evaluate_decision
│   │   └── decision_engine.py          # Policy routing to PASS, AUTO_RETRY, HUMAN_REVIEW
│   │
│   ├── media/                          # Media loading and frame extraction
│   │   ├── __init__.py                 # Exports FrameExtractor
│   │   └── frame_extractor.py          # FrameExtractor (sequential, stepped, fractional sampling via OpenCV)
│   │
│   ├── provenance/                     # Cryptographic audit & accountability
│   │   ├── __init__.py                 # Exports ProvenanceTracker, compute_sha256, signer functions
│   │   ├── hasher.py                   # Chunked SHA-256 file hashing
│   │   ├── id_generator.py             # Unique video_id and qa_run_id generation
│   │   ├── signer.py                   # Optional Ed25519 digital signature signing & verification
│   │   └── tracker.py                  # ProvenanceTracker orchestrating hashes and audit records
│   │
│   ├── schemas/                        # Pydantic data models & result schemas
│   │   ├── __init__.py                 # Schema exports
│   │   ├── input.py                    # VideoQAInput and GenerationMetadata schemas
│   │   ├── report.py                   # Top-level QAReport schema
│   │   └── results.py                  # ComponentResult, CheckStatus, DecisionType, ReasonCode
│   │
│   ├── semantic/                       # Semantic prompt alignment
│   │   ├── __init__.py                 # Exports PromptAlignmentEvaluator, CLIPChecker
│   │   ├── clip_checker.py             # CLIPChecker (OpenAI CLIP ViT-B/32, prompt templates, tensor caching)
│   │   └── prompt_alignment.py         # PromptAlignmentEvaluator (fractional sampling, threshold routing)
│   │
│   ├── technical/                      # Technical container & stream integrity
│   │   ├── __init__.py                 # Exports FFprobeValidator
│   │   └── ffprobe_validator.py        # FFprobeValidator (dimensions, fps, duration, codecs)
│   │
│   └── temporal/                       # Temporal stability & continuity
│       ├── __init__.py                 # Exports TemporalAnalyzer, ShotBoundaryDetector, individual detectors
│       ├── duplicate_frames.py         # PSNR and L1 pixel duplicate detector
│       ├── flicker.py                  # Second-order luminance acceleration flicker detector
│       ├── frame_difference.py         # Pairwise L1 diff, MSE, PSNR, luminance delta
│       ├── frame_drop.py               # Shot-boundary aware frame drop detection
│       ├── freeze_detection.py         # Consecutive identical frame freeze detector
│       ├── motion_anomaly.py           # Sudden velocity jump & speed surge detector
│       ├── optical_flow.py             # OpticalFlowEstimator (Farneback basic & RAFT advanced)
│       └── shot_boundary.py            # ShotBoundaryDetector (HSV histograms, ORB feature matching)
│
├── demo/                               # Interactive demonstration workbench
│   ├── __init__.py
│   └── gradio_app.py                   # Gradio visual workbench with multi-tab QA breakdown
│
├── mock_data/                          # Test media and expected outcomes
│   ├── __init__.py
│   ├── generate_fixtures.py            # Deterministic synthetic fixture generator
│   ├── run_calibration.py              # Calibration test runner across all fixtures
│   ├── manifest.json                   # Ground-truth fixture registry
│   ├── media/                          # Test video fixtures (.mp4)
│   │   ├── good.mp4                    # Clean baseline video (all checks PASS)
│   │   ├── black_frame.mp4             # Injected black frames (triggers ARTIFACT_BLACK_FRAME)
│   │   ├── blur.mp4                    # Severe blur artifact (triggers ARTIFACT_BLUR)
│   │   ├── corrupted_metadata.mp4      # Invalid container/metadata fixture (triggers TECHNICAL_INVALID_MEDIA)
│   │   ├── dropped_frames.mp4          # Intra-shot dropped frames (triggers TEMPORAL_FRAME_DROP)
│   │   ├── duplicate_frames.mp4        # Repeated identical frames (triggers TEMPORAL_DUPLICATE_FRAMES)
│   │   ├── flicker.mp4                 # Rapid luminance flicker (triggers TEMPORAL_FLICKER)
│   │   ├── freeze.mp4                  # Frozen frame sequence >= 6 frames (triggers TEMPORAL_FREEZE)
│   │   ├── hitech_girl.mp4             # Real AI-generated multi-shot video (240 frames, clean camera cuts)
│   │   ├── resolution_change.mp4       # Video with dynamic resolution shift (triggers ARTIFACT_RESOLUTION_CHANGE)
│   │   ├── speed_jump.mp4              # Unnatural velocity jump (triggers TEMPORAL_MOTION_ANOMALY)
│   │   └── text_overlay.mp4            # Overlaid subtitle/watermark text (triggers ARTIFACT_TEXT_OVERLAY)
│   ├── expected/                       # Expected JSON evaluation outcomes per fixture
│   ├── inputs/                         # Default input metadata per fixture
│   ├── metadata/                       # Fixture generation metadata
│   └── failures/                       # Recorded defect diagnostic snapshots
│
├── tests/                              # Pytest test suite (74 tests)
│   ├── test_artifacts.py               # Visual artifact detector unit tests
│   ├── test_cli.py                     # CLI commands (doctor, qa, fixtures) tests
│   ├── test_decision.py                # Deterministic decision engine policy tests
│   ├── test_ffprobe.py                 # Technical container validator tests
│   ├── test_fixtures.py                # Media fixture integrity tests
│   ├── test_frames.py                  # Frame extractor unit tests
│   ├── test_gradio.py                  # Gradio UI integration tests
│   ├── test_pipeline.py                # End-to-end VideoQAPipeline tests
│   ├── test_provenance.py              # SHA-256 and Ed25519 signing tests
│   ├── test_real_smoke.py              # Smoke test on real multi-shot AI video
│   ├── test_semantic.py                # CLIP semantic alignment & model-unavailable tests
│   └── test_temporal.py                # Temporal QA & shot-boundary classification tests
│
└── validation/                         # Validation reports and empirical benchmarks
    ├── REAL_CLIP_SEMANTIC_VALIDATION.md# Real OpenAI CLIP ViT-B/32 integration report
    ├── TEMPORAL_SHOT_BOUNDARY_FIX.md   # Shot-boundary aware frame drop fix report
    ├── REAL_VIDEO_QA_VALIDATION.md     # Baseline real video validation report
    └── temporal_frames_contact_sheet.png# Visual contact sheet of camera cuts
```

---

## 4. Installation & Environment Setup

### System Prerequisites
- **Python:** 3.10, 3.11, or 3.12
- **FFmpeg & ffprobe:** Required on system `PATH` for technical container inspection.

### 1. Install Python Dependencies
```bash
# Navigate to the project root
cd "C:\Video Accountobilty"

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Environment Health
Run the built-in diagnostic doctor:
```bash
python -m app.cli --doctor
```

Expected output:
```text
========================================
MEMBER 8 QA ENVIRONMENT DIAGNOSTIC
========================================
Python         OK         (3.10.11)
FFmpeg         OK         (available)
ffprobe        OK         (available)
OpenCV         OK         (4.10.0)
PyTorch        OK         (2.6.0+cpu)
CLIP           OK         (transformers)
RAFT           OK         (torchvision)
Gradio         OK         (4.44.1)
========================================
Status: Environment ready for QA execution.
```

---

## 5. Quick Start

Run complete QA on a video in just 3 lines of Python:

```python
from app import run_video_qa

report = run_video_qa(
    video_path="mock_data/media/good.mp4",
    prompt="a yellow circle moving on a dark background",
)

print(f"Decision: {report.decision.value}")  # PASS
print(f"Reason Codes: {[r.value for r in report.reason_codes]}")  # []
```

Or run via the CLI:
```bash
python -m app.cli qa --video mock_data/media/good.mp4 --prompt "a yellow circle moving on a dark background"
```

---

## 6. Comprehensive Usage Guide (All Components)

### A. End-to-End Pipeline API

The `VideoQAPipeline` class coordinates all six QA pillars and passes component results to the `DecisionEngine`.

#### Basic Usage:
```python
from app.pipeline import VideoQAPipeline

pipeline = VideoQAPipeline()
report = pipeline.run(
    video_path="mock_data/media/hitech_girl.mp4",
    prompt="a girl in hyderabad is walking with her dog",
    video_id="VID_HITECH_001",
)

# Access individual check results
print("Technical :", report.technical.status.value)
print("Temporal  :", report.temporal.status.value, f"(Score: {report.temporal.score})")
print("Semantic  :", report.semantic.status.value, f"(Score: {report.semantic.score})")
print("Artifacts :", report.artifacts.status.value)
print("Provenance:", report.provenance.status.value)
print("DECISION  :", report.decision.value)
```

#### Customized Pipeline with Overridden Thresholds:
```python
from app.config import QAConfig, TemporalConfig, SemanticConfig, ArtifactConfig
from app.pipeline import VideoQAPipeline

custom_config = QAConfig(
    temporal=TemporalConfig(
        optical_flow_mode="basic",           # "basic" (Farneback) or "advanced" (RAFT)
        shot_boundary_diff_threshold=0.08,   # Frame diff threshold for camera cuts
        flicker_threshold=15.0,              # Max acceptable flicker variance
    ),
    semantic=SemanticConfig(
        model_name="openai/clip-vit-base-patch32",
        pass_threshold=0.22,                 # Minimum cosine similarity for PASS
        uncertain_threshold=0.18,            # Score below which alignment FAILS
    ),
    artifacts=ArtifactConfig(
        blur_threshold=25.0,                 # Laplacian variance threshold
        black_frame_threshold=2.0,           # Max luminance for black frame
    )
)

pipeline = VideoQAPipeline(config=custom_config)
report = pipeline.run("path/to/my_video.mp4", prompt="A futuristic cyberpunk city in rain.")

# Export full structured JSON
import json
print(json.dumps(report.model_dump(), indent=2))
```

---

### B. Technical Media Validator (`app.technical`)

Inspects video container, bitstream streams, codec compliance, resolution, FPS, and duration using `ffprobe`.

```python
from app.technical import FFprobeValidator
from app.config import TechnicalConfig

validator = FFprobeValidator(config=TechnicalConfig())
result = validator.validate("mock_data/media/good.mp4")

print("Status   :", result.status.value)        # CheckStatus.PASS
print("Score    :", result.score)               # 1.0
print("Codec    :", result.evidence.get("video_codec"))  # h264
print("Duration :", result.evidence.get("duration"))     # 4.0
print("FPS      :", result.evidence.get("fps"))          # 24.0
print("Resolution:", f"{result.evidence.get('width')}x{result.evidence.get('height')}")
```

---

### C. Temporal Continuity & Shot Boundaries (`app.temporal`)

Evaluates inter-frame motion, detects camera cuts, flags dropped frames, and detects flicker, freezes, and duplicate frames.

#### 1. Full Temporal Analysis:
```python
from app.temporal import TemporalAnalyzer
from app.media import FrameExtractor
from app.config import TemporalConfig

# Extract frames
extractor = FrameExtractor()
frames, fps = extractor.extract_frames("mock_data/media/hitech_girl.mp4")

# Run analyzer
analyzer = TemporalAnalyzer(config=TemporalConfig())
result = analyzer.analyze(frames, fps=fps)

print("Temporal Status :", result.status.value)
print("Temporal Score  :", result.score)
print("Flicker Score   :", result.evidence.get("flicker_score"))
print("Duplicate Ratio :", result.evidence.get("duplicate_ratio"))
print("Freeze Runs     :", result.evidence.get("freeze_runs"))
print("Dropped Frames  :", result.evidence.get("dropped_frame_candidates"))
```

#### 2. Standalone Shot Boundary Classification:
Distinguish between legitimate camera cuts and accidental dropped frames:
```python
from app.temporal import ShotBoundaryDetector
from app.config import TemporalConfig

detector = ShotBoundaryDetector(config=TemporalConfig())

# Classify discontinuity at candidate frame index 65
# (prev_frame = frame 64, curr_frame = frame 65, next_frame = frame 66)
classification, details = detector.classify_discontinuity(
    prev_frame=frames[64],
    curr_frame=frames[65],
    next_frame=frames[66],
)

print("Classification:", classification)  # "SHOT_BOUNDARY", "DROPPED_FRAME", or "AMBIGUOUS"
print("L1 Difference :", details["diff_prev_curr"])
print("HSV Hist Corr :", details["hist_prev_curr"])
print("ORB Matches   :", details["orb_matches_prev_curr"])
```

#### 3. Standalone Modular Detectors:
```python
from app.temporal import (
    detect_flicker,
    detect_duplicates,
    detect_freeze,
    detect_motion_anomalies,
)

# Detect flicker (second-order luminance acceleration)
flicker_score, flicker_frames = detect_flicker(frames, threshold=15.0)

# Detect duplicate frames (PSNR > 45 dB)
dup_count, dup_ratio, dup_runs = detect_duplicates(frames, psnr_threshold=45.0)

# Detect frozen sequences (consecutive identical frames >= 6)
freeze_runs, freeze_ratio = detect_freeze(frames, min_consecutive=6)

# Detect sudden velocity surges via optical flow
anomalies, anomaly_frames = detect_motion_anomalies(frames, threshold_ratio=3.5)
```

---

### D. Visual Artifact & Glitch Detector (`app.artifacts`)

Detects black/blank frames, severe defocus blur, decode corruptions, and text overlays.

```python
from app.artifacts import ArtifactDetector
from app.config import ArtifactConfig
from app.media import FrameExtractor

extractor = FrameExtractor()
frames, _ = extractor.extract_frames("mock_data/media/blur.mp4")

detector = ArtifactDetector(config=ArtifactConfig())
result = detector.detect(frames)

print("Status      :", result.status.value)
print("Blur Score  :", result.evidence.get("blur_score"))
print("Black Frames:", result.evidence.get("black_frame_count"))
print("Text Overlay:", result.evidence.get("has_text_overlay"))
print("Reason Codes:", [r.value for r in result.reason_codes])
```

Direct module functions:
```python
from app.artifacts import detect_black_frames, detect_blur, detect_decode_glitches

# Blur detection via Laplacian variance
blur_score, is_blurry = detect_blur(frames[0], threshold=25.0)

# Black frame detection
black_count, black_indices = detect_black_frames(frames, luminance_threshold=2.0)
```

---

### E. Semantic Alignment with CLIP ViT-B/32 (`app.semantic`)

Measures image-text prompt alignment using OpenAI CLIP (`openai/clip-vit-base-patch32`) with model caching, automatic CUDA/CPU selection, and prompt ensembling.

#### 1. High-Level Semantic Alignment Evaluator:
```python
from app.semantic import PromptAlignmentEvaluator
from app.media import FrameExtractor
from app.config import SemanticConfig

extractor = FrameExtractor()
frames, _ = extractor.extract_frames("mock_data/media/hitech_girl.mp4")

evaluator = PromptAlignmentEvaluator(config=SemanticConfig())
result = evaluator.evaluate(
    frames=frames,
    prompt="a girl in hyderabad is walking with her dog",
)

print("Status       :", result.status.value)          # PASS
print("Score        :", result.score)                 # ~0.316
print("Model Backend:", result.evidence["model_backend"]) # "clip-vit-base-patch32"
print("Device       :", result.evidence["device"])        # "cuda" or "cpu"

# Per-frame breakdown
for detail in result.evidence["frame_details"]:
    print(f"  Frame {detail['frame_idx']} ({detail['timestamp']:.2f}s): {detail['score']:.4f}")
```

#### 2. Direct Low-Level CLIP Similarity:
```python
from app.semantic import CLIPChecker

clip = CLIPChecker(model_name="openai/clip-vit-base-patch32")

# Compare prompt against an array of BGR frames
similarity = clip.compute_similarity(
    frames=[frames[0], frames[60], frames[120]],
    prompt="a girl in hyderabad walking her dog",
)
print("Mean Alignment Score:", similarity)
```

---

### F. Provenance Tracker & Ed25519 Signer (`app.provenance`)

Generates cryptographic SHA-256 media checksums, execution run UUIDs, and audit manifests with optional Ed25519 digital signatures.

```python
from app.provenance import ProvenanceTracker, compute_sha256, generate_video_id

# 1. Direct SHA-256 calculation
sha256_hash = compute_sha256("mock_data/media/good.mp4")
print("SHA-256:", sha256_hash)

# 2. Complete provenance tracking
tracker = ProvenanceTracker()
result = tracker.track(
    video_path="mock_data/media/good.mp4",
    video_id=generate_video_id("mock_data/media/good.mp4"),
)
print("Video ID   :", result.evidence["video_id"])
print("QA Run ID  :", result.evidence["qa_run_id"])
print("Timestamp  :", result.evidence["timestamp"])

# 3. Cryptographic Ed25519 digital signing
from app.provenance.signer import generate_keypair, sign_manifest, verify_signature

private_key, public_key = generate_keypair()
manifest_data = {"video_id": "VID_001", "sha256": sha256_hash}
signature = sign_manifest(manifest_data, private_key)

is_valid = verify_signature(manifest_data, signature, public_key)
print("Signature Valid:", is_valid)  # True
```

---

### G. Frame Extractor (`app.media`)

Robust OpenCV-based frame extraction with support for full sequential, stepped, or fractional sampling.

```python
from app.media import FrameExtractor
from app.config import FrameExtractorConfig

extractor = FrameExtractor(config=FrameExtractorConfig(max_frames=300))

# 1. Sequential extraction (returns list of BGR numpy arrays, fps)
frames, fps = extractor.extract_frames("mock_data/media/good.mp4")
print(f"Extracted {len(frames)} frames at {fps} FPS")

# 2. Fractional sampling (e.g., sample at 10%, 30%, 50%, 70%, 90% of duration)
sample_points = [0.10, 0.30, 0.50, 0.70, 0.90]
sampled_indices = [int(p * (len(frames) - 1)) for p in sample_points]
sampled_frames = [frames[i] for i in sampled_indices]
```

---

### H. Deterministic Decision Engine (`app.decision`)

Evaluates aggregated component results and machine-readable reason codes to produce a single deterministic decision: `PASS`, `AUTO_RETRY`, or `HUMAN_REVIEW`.

```python
from app.decision import DecisionEngine
from app.schemas.results import ComponentResult, CheckStatus, ReasonCode

engine = DecisionEngine()

decision, active_reasons = engine.evaluate(
    technical=ComponentResult(status=CheckStatus.PASS, score=1.0),
    temporal=ComponentResult(status=CheckStatus.FAIL, score=0.4, reason_codes=[ReasonCode.TEMPORAL_FRAME_DROP]),
    semantic=ComponentResult(status=CheckStatus.PASS, score=0.3),
    artifacts=ComponentResult(status=CheckStatus.PASS, score=1.0),
    provenance=ComponentResult(status=CheckStatus.PASS, score=1.0),
)

print("Decision:", decision.value)  # AUTO_RETRY
print("Reasons :", [r.value for r in active_reasons])  # ['TEMPORAL_FRAME_DROP']
```

---

### I. Command-Line Interface (`app.cli`)

#### 1. Run Environment Diagnostic (`--doctor`):
```bash
python -m app.cli --doctor
```

#### 2. Run Video Quality Assurance (`qa` subcommand):
```bash
# Standard console evaluation
python -m app.cli qa --video mock_data/media/good.mp4 --prompt "a yellow circle moving on a dark background"

# Evaluate real AI-generated video
python -m app.cli qa --video mock_data/media/hitech_girl.mp4 --prompt "a girl in hyderabad is walking with her dog"

# Output structured JSON
python -m app.cli qa --video mock_data/media/good.mp4 --prompt "a yellow circle" --json

# Pipe JSON output directly to file (Windows PowerShell)
python -m app.cli qa --video mock_data/media/good.mp4 --prompt "a yellow circle" --json | Out-File -Encoding utf8 report.json
```

#### 3. CLI Exit Codes:
- `0`: Evaluation produced `PASS` (or non-fatal review)
- `1`: Evaluation produced `AUTO_RETRY` (machine-detectable defect flagged) or invalid input

---

### J. Interactive Gradio QA Workbench (`demo.gradio_app`)

Launch the local interactive visual workbench:
```bash
python -m demo.gradio_app
```
Then open: **`http://127.0.0.1:7860`**

#### Workbench Capabilities:
1. **Video Player & Prompt Input:** Upload any `.mp4` video or select from pre-loaded test fixtures.
2. **Top-Level Decision Banner:** Prominent color-coded outcome indicator (`PASS` [green], `AUTO_RETRY` [red], `HUMAN_REVIEW` [amber]).
3. **Tabbed Component Breakdowns:**
   - **Technical Tab:** Dimensions, duration, FPS, container format, and video codec.
   - **Temporal Tab:** Motion smoothness score, flicker score, freeze runs, duplicate ratio, and dropped frame counts.
   - **Semantic Tab:** Per-frame CLIP similarity scores, timestamps, and model backend reporting.
   - **Artifacts Tab:** Blur score (Laplacian variance), black frame counts, and text overlay detection.
   - **Provenance Tab:** SHA-256 cryptographic digest, video ID, and QA run UUID.

---

### K. Mock Fixture Generation & Calibration (`mock_data`)

The repository includes a suite of 11 deterministic synthetic video fixtures with mathematically injected defects.

#### 1. Regenerate Mock Fixtures:
```bash
python -m app.cli fixtures --output-dir mock_data
```

#### 2. Run Comprehensive Calibration Matrix:
```bash
python -m mock_data.run_calibration
```
This runs the full QA pipeline against all 11 fixtures and validates 100% classification accuracy against expected reason codes.

---

## 7. Configuration Reference (`QAConfig`)

All pipeline behavior is governed by strongly typed Pydantic models defined in `app/config.py`:

```python
from app.config import QAConfig

config = QAConfig()
```

### Complete Configuration Schema

| Config Group | Field | Default | Description |
|:---|:---|:---:|:---|
| **`TechnicalConfig`** | `allowed_codecs` | `["h264", "hevc", "vp9", "av1", "mp4v-20"]` | Acceptable video stream codecs |
| | `min_duration` | `0.5` | Minimum acceptable video duration in seconds |
| | `max_duration` | `60.0` | Maximum acceptable video duration in seconds |
| | `min_fps` | `10.0` | Minimum acceptable frame rate |
| | `min_width` / `min_height` | `128` | Minimum video dimensions in pixels |
| **`TemporalConfig`** | `optical_flow_mode` | `"basic"` | `"basic"` (Farneback) or `"advanced"` (RAFT) |
| | `shot_boundary_diff_threshold` | `0.08` | Mean L1 pixel difference for camera cut identification |
| | `shot_boundary_hist_threshold` | `0.92` | HSV 2D histogram correlation threshold for cut confirmation |
| | `shot_boundary_min_feature_matches` | `25` | ORB feature match count below which a cut is indicated |
| | `flicker_threshold` | `15.0` | Max acceptable second-order luminance acceleration |
| | `duplicate_psnr_threshold` | `45.0` | PSNR in dB above which adjacent frames are duplicates |
| | `max_freeze_frames` | `6` | Consecutive identical frames before flagging freeze |
| | `drop_spike_ratio` | `2.6` | Motion delta spike ratio required to flag dropped frame |
| | `motion_surge_ratio` | `3.5` | Velocity jump multiplier required to flag motion anomaly |
| **`SemanticConfig`** | `model_name` | `"openai/clip-vit-base-patch32"` | HuggingFace CLIP model identifier |
| | `pass_threshold` | `0.22` | Minimum cosine similarity score for `PASS` |
| | `uncertain_threshold` | `0.18` | Score below which semantic alignment `FAILS` |
| | `sample_points` | `[0.1, 0.3, 0.5, 0.7, 0.9]` | Fractional timeline points sampled for evaluation |
| **`ArtifactConfig`** | `black_frame_threshold` | `2.0` | Max average luminance to qualify as a black frame |
| | `blur_threshold` | `25.0` | Laplacian variance below which frame is flagged blurry |
| | `text_edge_density_threshold` | `0.08` | Horizontal edge density threshold for text overlay |
| **`ProvenanceConfig`** | `hash_algorithm` | `"sha256"` | Cryptographic hashing algorithm |
| | `enable_signing` | `False` | Enable Ed25519 digital signing of audit manifests |
| **`DecisionConfig`** | `auto_retry_reasons` | `[TEMPORAL_*, ARTIFACT_*, ...]` | Reason codes routed to `AUTO_RETRY` |
| | `human_review_reasons` | `[SEMANTIC_UNCERTAIN, ...]` | Reason codes routed to `HUMAN_REVIEW` |
| **`FrameExtractorConfig`**| `max_frames` | `1000` | Maximum number of frames to load into memory |

---

## 8. Machine-Readable Reason Codes

Deterministic machine-readable reason codes emitted by component checks:

| Reason Code | Category | Default Action | Operational Meaning |
|:---|:---:|:---:|:---|
| `TECHNICAL_INVALID_MEDIA` | Technical | `AUTO_RETRY` | Unreadable, corrupted, or invalid media container. |
| `TECHNICAL_METADATA_MISMATCH` | Technical | `HUMAN_REVIEW` | Actual media properties differ from generation manifest metadata. |
| `TECHNICAL_FILE_NOT_FOUND` | Technical | `AUTO_RETRY` | Media file path does not exist on disk. |
| `TECHNICAL_EXECUTION_ERROR` | Technical | `AUTO_RETRY` | Internal inspection error during ffprobe extraction. |
| `TEMPORAL_FLICKER` | Temporal | `AUTO_RETRY` | Rapid luminance variance exceeds acceptable threshold. |
| `TEMPORAL_DUPLICATE_FRAMES` | Temporal | `AUTO_RETRY` | Excessive consecutive duplicate frames detected (stutter). |
| `TEMPORAL_FREEZE` | Temporal | `AUTO_RETRY` | Video motion freezes for more than 6 consecutive frames. |
| `TEMPORAL_FRAME_DROP` | Temporal | `AUTO_RETRY` | Abrupt intra-shot motion discontinuity (isolated drop or skip). |
| `TEMPORAL_MOTION_ANOMALY` | Temporal | `AUTO_RETRY` | Optical flow velocity surges abruptly (unnatural speed jump). |
| `SEMANTIC_LOW_ALIGNMENT` | Semantic | `AUTO_RETRY` | CLIP prompt-frame cosine similarity falls below `0.18`. |
| `SEMANTIC_UNCERTAIN` | Semantic | `HUMAN_REVIEW` | Similarity falls between `0.18` and `0.22` (ambiguous prompt alignment). |
| `SEMANTIC_MODEL_UNAVAILABLE` | Semantic | `HUMAN_REVIEW` | CLIP weights missing/offline; prevents false automated PASS. |
| `ARTIFACT_BLACK_FRAME` | Artifacts | `AUTO_RETRY` | Unrendered or black frames detected. |
| `ARTIFACT_BLUR` | Artifacts | `AUTO_RETRY` | Laplacian variance falls below threshold (defocus/motion blur). |
| `ARTIFACT_RESOLUTION_CHANGE` | Artifacts | `AUTO_RETRY` | Video stream resolution dynamically alters mid-stream. |
| `ARTIFACT_DECODE_FAILURE` | Artifacts | `AUTO_RETRY` | Bitstream decoding errors detected during frame extraction. |
| `ARTIFACT_TEXT_OVERLAY` | Artifacts | `HUMAN_REVIEW` | Unintended subtitles, watermarks, or text artifacts present. |
| `PROVENANCE_HASH_FAILURE` | Provenance | `HUMAN_REVIEW` | SHA-256 hash does not match expected generation checksum. |
| `PROVENANCE_METADATA_FAILURE` | Provenance | `HUMAN_REVIEW` | Provenance audit metadata is missing or corrupted. |
| `PROVENANCE_SIGNATURE_INVALID` | Provenance | `HUMAN_REVIEW` | Ed25519 digital signature failed cryptographic verification. |

---

## 9. Testing & Test Suite Breakdown

The repository contains 74 automated unit, integration, and regression tests.

### Run Full Test Suite:
```bash
python -m pytest -q
```
Expected output:
```text
74 passed in 207.08s (0:03:27)
```

### Module-Specific Test Suites:
```bash
# 1. Temporal QA & Shot Boundary Tests (13 tests)
python -m pytest tests/test_temporal.py -v

# 2. Real CLIP Semantic Alignment Tests (14 tests)
python -m pytest tests/test_semantic.py -v

# 3. End-to-End Pipeline Tests (5 tests)
python -m pytest tests/test_pipeline.py -v

# 4. Visual Artifact Detector Tests (6 tests)
python -m pytest tests/test_artifacts.py -v

# 5. Technical FFprobe Validator Tests (4 tests)
python -m pytest tests/test_ffprobe.py -v

# 6. Provenance & Cryptographic Signing Tests (6 tests)
python -m pytest tests/test_provenance.py -v

# 7. Decision Engine Policy Tests (6 tests)
python -m pytest tests/test_decision.py -v

# 8. Command-Line Interface Tests (4 tests)
python -m pytest tests/test_cli.py -v

# 9. Real Multi-Shot AI Video Smoke Test (1 test)
python -m pytest tests/test_real_smoke.py -v
```

---

## 10. Validation Reports & Empirical Benchmarks

Comprehensive validation reports documenting detector calibration on real-world AI-generated video and synthetic fixtures:

1. **[validation/TEMPORAL_SHOT_BOUNDARY_FIX.md](file:///c:/Video%20Accountobilty/validation/TEMPORAL_SHOT_BOUNDARY_FIX.md):**
   - Documents the resolution of false-positive `TEMPORAL_FRAME_DROP` flags on multi-shot AI video (`hitech_girl.mp4`).
   - Details HSV 2D histogram correlation and ORB feature matching algorithms that distinguish legitimate scene cuts at frames 65, 103, and 170 from true dropped frames on `dropped_frames.mp4`.

2. **[validation/REAL_CLIP_SEMANTIC_VALIDATION.md](file:///c:/Video%20Accountobilty/validation/REAL_CLIP_SEMANTIC_VALIDATION.md):**
   - Documents the integration of real OpenAI CLIP ViT-B/32 semantic evaluation, replacing the silent `0.25` deterministic baseline.
   - Demonstrates 138% empirical score separation between matching Prompt A (`0.3161`, `PASS`) and negative Prompt B (`0.1327`, `FAIL`).

3. **[calibration_report.md](file:///c:/Video%20Accountobilty/calibration_report.md):**
   - Full 11-fixture calibration matrix measuring 100% classification accuracy across all injected defect types.

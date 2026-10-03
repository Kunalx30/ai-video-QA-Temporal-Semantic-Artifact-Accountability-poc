# Temporal QA — Phase 1: Shot-Boundary Aware Frame Drop Detection

## 1. Executive Summary & Original Problem

On real multi-shot AI-generated videos (such as `hitech_girl.mp4`), the temporal QA detector previously raised a false-positive defect:
```
TEMPORAL: FAIL
reason_code: TEMPORAL_FRAME_DROP
dropped_frame_candidates: [65, 103, 170]
spike_ratios: [6.65, 5.03, 7.32]
Final Decision: AUTO_RETRY
```

Visual frame-by-frame inspection revealed that these frames were legitimate camera/shot transitions in a multi-shot sequence:
- **Frame 64 -> 65**: Cut from close-up walking to wide tracking shot.
- **Frame 102 -> 103**: Cut from wide shot to medium side-angle tracking shot.
- **Frame 169 -> 170**: Cut from side tracking shot to low-angle forward tracking shot.

Because the previous detector treated any large frame difference spike as a frame drop, legitimate cinematic cuts triggered `TEMPORAL_FRAME_DROP` and caused unnecessary `AUTO_RETRY` failures.

---

## 2. Why the Old Detector Produced a False Positive

The original `detect_frame_drops` algorithm in `app/temporal/frame_drop.py`:
1. Computed normalized L1 grayscale differences between consecutive frames `(i, i+1)`.
2. Estimated a local motion baseline as `max(0.005, (prev_val + next_val) / 2.0)`.
3. Evaluated whether `spike_ratio = val / baseline >= 2.6` (or `val > 0.15 and spike_ratio >= 2.0`).
4. If a spike exceeded this threshold, it directly classified the frame as a `dropped_frame_candidate` and flagged `TEMPORAL_FRAME_DROP`.

### The Fundamental Flaw
A camera cut inherently creates a large visual difference `diff(N-1, N)` relative to continuous intra-shot motion. The previous detector lacked any contextual inspection of neighboring frames `(N-1, N, N+1)` and multi-cue visual evidence (color histograms and feature correspondence). It conflated:
- **Shot cut:** Scene changes permanently from shot A to shot B.
- **Dropped frame / isolated anomaly:** Frame N is corrupted or missing while surrounding frames remain within the same scene.

---

## 3. New Architecture & Detection Logic

The pipeline has been upgraded from:
```
large frame difference  -->  TEMPORAL_FRAME_DROP
```
to a multi-stage validation architecture:
```
large frame difference
        ↓
candidate temporal discontinuity
        ↓
neighboring frame inspection (N-1, N, N+1)
        ↓
multi-cue visual classification:
  - DROPPED_FRAME (isolated glitch or intra-shot motion skip)
  - SHOT_BOUNDARY (camera / scene transition)
  - UNCERTAIN (ambiguous evidence; does NOT cause false defect)
        ↓
only confirmed DROPPED_FRAME candidates trigger TEMPORAL_FRAME_DROP
```

### Components Added/Updated:
1. **`app/config.py` (`TemporalConfig`)**:
   - `shot_boundary_diff_threshold: float = 0.08`: Threshold indicating potential shot transition.
   - `shot_boundary_hist_threshold: float = 0.92`: 2D HSV color histogram correlation below which a shot cut is indicated.
   - `shot_boundary_min_feature_matches: int = 25`: Minimum ORB feature matches across a boundary.
   - `dropped_frame_isolation_ratio: float = 0.50`: Ratio threshold for isolated dropped frame validation.

2. **`app/temporal/shot_boundary.py` (`ShotBoundaryDetector`)**:
   - Computes 2D HSV color histogram correlation across candidate frame pairs.
   - Computes ORB feature detection and Hamming distance matching.
   - Computes pairwise normalized differences: `diff(N-1, N)`, `diff(N, N+1)`, `diff(N-1, N+1)`.
   - Exposes `ShotBoundaryDetector.classify_discontinuity(...)` and sequence scanner `detect_shot_boundaries(...)`.

3. **`app/temporal/frame_drop.py` (`detect_frame_drops`)**:
   - Preserves candidate detection as the underlying spike detector.
   - Passes candidate frames to `ShotBoundaryDetector.classify_discontinuity`.
   - Only candidates classified as `DROPPED_FRAME` are marked as defects.
   - Emits structured diagnostic evidence containing full pairwise differences and classification rationales.

4. **`app/temporal/__init__.py` (`TemporalAnalyzer`)**:
   - Passes `frames=frames` to `detect_frame_drops`.
   - Exports `ShotBoundaryDetector` and `detect_shot_boundaries`.

---

## 4. How Shot Boundaries Are Distinguished From Dropped Frames

For candidate discontinuity at frame $N$:

### Case A — Isolated Dropped / Glitched Frame:
- $N-1$ and $N+1$ belong to the same scene, while $N$ is corrupted or anomalous:
  $$\text{diff}(N-1, N) \text{ HIGH}, \quad \text{diff}(N, N+1) \text{ HIGH}, \quad \text{diff}(N-1, N+1) \text{ LOW}$$
- Surrounding frame correlation $\text{hist\_sim}(N-1, N+1) \ge 0.92$.
- **Classification:** `DROPPED_FRAME`.

### Case B — Legitimate Shot Boundary (Camera Transition):
- Frame $N-1$ belongs to Shot 1; Frames $N$ and $N+1$ belong to Shot 2:
  $$\text{diff}(N-1, N) \text{ HIGH}, \quad \text{diff}(N-1, N+1) \text{ HIGH}, \quad \text{diff}(N, N+1) \text{ NORMAL}$$
- Scene change cues:
  - Color distribution shifts significantly: $\text{hist\_sim}(N-1, N) < 0.92$ or $\text{hist\_sim}(N-1, N+1) < 0.92$.
  - Feature matches collapse across boundary ($\text{ORB\_matches}(N-1, N) < 25$) while intra-shot matches are high ($\text{ORB\_matches}(N, N+1) \ge 100$).
- **Classification:** `SHOT_BOUNDARY`.

### Case C — Intra-Shot Multi-Frame Drop / Stutter (e.g. `mock_data/media/dropped_frames.mp4`):
- Motion jumps forward abruptly within the same camera shot:
  $$\text{diff}(N-1, N) \text{ is a spike above local baseline}, \quad \text{diff}(N-1, N) < 0.08$$
- Color histogram correlation remains near-identical:
  $$\text{hist\_sim}(N-1, N) \ge 0.95$$
- The scene composition and background are identical, but temporal progress stuttered.
- **Classification:** `DROPPED_FRAME`.

### Case D — Ambiguous Evidence:
- If visual cues are conflicting or borderline (e.g. fast whip-pan motion or partial occlusion without clear shot cut or isolation):
- **Classification:** `UNCERTAIN`.
- Per requirements, ambiguous discontinuities do **not** trigger `TEMPORAL_FRAME_DROP`.

---

## 5. Empirical Measurements & Verification

### A. Real Video: `hitech_girl.mp4` (240 frames)

| Candidate Frame | diff(N-1, N) | diff(N, N+1) | diff(N-1, N+1) | Hist Sim (HSV) | ORB Matches (across / intra) | Classification | Confirmed Defect? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **65** | 0.1575 | 0.0207 | 0.1605 | 0.8849 | 26 / 280 | `SHOT_BOUNDARY` | No |
| **103** | 0.2220 | 0.0608 | 0.2232 | 0.8331 | 3 / 131 | `SHOT_BOUNDARY` | No |
| **170** | 0.2813 | 0.0312 | 0.2804 | 0.5796 | 2 / 269 | `SHOT_BOUNDARY` | No |

### B. Standard Test Fixtures

| Video Fixture | Defect Type | Previous Result | New Result | Frame Drop Reason Code Present? |
|:---|:---|:---:|:---:|:---:|
| `good.mp4` | Clean baseline | PASS | PASS | No |
| `dropped_frames.mp4` | Frame 25 dropped | FAIL | FAIL | **Yes (`TEMPORAL_FRAME_DROP`)** |
| `freeze.mp4` | Frozen frames | FAIL | FAIL | No (`TEMPORAL_FREEZE` preserved) |
| `flicker.mp4` | Luminance flicker | FAIL | FAIL | No (`TEMPORAL_FLICKER` preserved) |
| `speed_jump.mp4` | Velocity surge | FAIL | FAIL | No (`TEMPORAL_MOTION_ANOMALY` preserved) |

---

## 6. End-to-End Before vs After Results (`hitech_girl.mp4`)

Prompt: `"a girl in hyderabad is walking with her dog"`

| Evaluation Metric | Before Fix | After Fix |
|:---|:---|:---|
| **Top-Level Decision** | `AUTO_RETRY` | **`PASS`** |
| **Technical Status** | `PASS` | `PASS` |
| **Temporal Status** | `FAIL` | **`PASS`** |
| **Temporal Reason Codes** | `[TEMPORAL_FRAME_DROP]` | **`[]`** |
| **Dropped Frame Candidates** | `[65, 103, 170]` | **`[]`** |
| **Shot Boundary Candidates** | N/A (unsupported) | **`[65, 103, 170]`** |
| **Semantic QA Status** | `PASS` (0.25) | `PASS` (0.25) |
| **Artifact QA Status** | `PASS` | `PASS` |
| **Provenance Status** | `PASS` | `PASS` |

---

## 7. Test Results

### Temporal Unit Tests
Command: `python -m pytest tests/test_temporal.py -v`
```
tests/test_temporal.py::test_good_fixture_passes_temporal PASSED
tests/test_temporal.py::test_duplicate_frames_detected PASSED
tests/test_temporal.py::test_freeze_frames_detected PASSED
tests/test_temporal.py::test_flicker_detected PASSED
tests/test_temporal.py::test_dropped_frames_detected PASSED
tests/test_temporal.py::test_speed_jump_detected PASSED
tests/test_temporal.py::test_optical_flow_farneback_and_raft PASSED
tests/test_temporal.py::test_temporal_analyzer_modes PASSED
tests/test_temporal.py::test_classify_isolated_dropped_frame_pattern PASSED
tests/test_temporal.py::test_classify_shot_boundary_pattern PASSED
tests/test_temporal.py::test_classify_ambiguous_case PASSED
tests/test_temporal.py::test_hitech_girl_shot_boundaries_not_flagged_as_drops PASSED
tests/test_temporal.py::test_detect_shot_boundaries_helper PASSED

13 passed in 41.73s
```

### Full Regression Suite
Command: `python -m pytest -q`
```
64 passed in 191.68s (0:03:11)
```

---

## 8. Remaining Limitations & Phase 2 Recommendations

1. **Gradual Transitions (Cross-dissolves / Fades):**
   - The current Phase 1 implementation targets hard cuts (`diff(N-1, N)` spikes). Gradual transitions spread frame difference over 10-30 frames, which rarely trigger single-frame spike detectors but may affect flicker or optical flow smoothness.
2. **Extreme Fast Whip Pans:**
   - A rapid camera whip pan inside a single shot can produce elevated L1 differences and lower feature matches. In such cases, the classifier appropriately marks them as `UNCERTAIN` rather than false drops.
3. **Flicker Interaction:**
   - Per requirements, flicker detection thresholds were kept independent. If shot cut frames produce high second-order variance in luminance in future models, shot-boundary masking can be applied to flicker analysis in Phase 2.

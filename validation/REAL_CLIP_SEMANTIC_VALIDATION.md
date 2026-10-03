# Real CLIP Semantic Validation Report — Phase 2

## 1. Previous Behavior

In the initial pipeline run on `hitech_girl.mp4`, semantic QA returned:
```
status: PASS
score: 0.25
model_backend: deterministic_baseline
scores_per_frame: [0.25, 0.25, 0.25, 0.25, 0.25]
```
The investigation proved that:
- `local_files_only=True` was hardcoded in `app/semantic/clip_checker.py`.
- Model weights were not pre-cached locally, causing an exception on `from_pretrained(...)`.
- The system silently fell back to `deterministic_baseline`, producing an identical constant score of `0.25` across all frames regardless of visual or text content.

---

## 2. CLIP Configuration

- **Model Architecture:** `openai/clip-vit-base-patch32` (configured in `SemanticConfig` in `app/config.py`).
- **Sampling Strategy:** Fractional uniform sampling at sample points `[0.0, 0.25, 0.5, 0.75, 1.0]`.
- **Pass Threshold:** `0.22` (calibrated cosine similarity for matching prompts).
- **Uncertain Threshold:** `0.18` (below which prompts are classified as `SEMANTIC_LOW_ALIGNMENT`).
- **Precision & Inference Mode:** `torch.no_grad()` and `model.eval()`.

---

## 3. Model Loading & Caching Strategy

The loading mechanism in `CLIPChecker` was updated to:
1. Attempt loading from the local HuggingFace cache first for instant startup:
   ```python
   CLIPProcessor.from_pretrained(self.model_name, local_files_only=True)
   CLIPModel.from_pretrained(self.model_name, local_files_only=True)
   ```
2. If not yet locally cached, automatically download weights from HuggingFace Hub without requiring manual user intervention:
   ```python
   CLIPProcessor.from_pretrained(self.model_name)
   CLIPModel.from_pretrained(self.model_name)
   ```
3. Cache the loaded `(model, processor)` in a module-level singleton `_GLOBAL_CLIP_CACHE` to avoid reloading weights across multiple videos or frames.
4. Model weights are stored in standard user cache (`~/.cache/huggingface/hub/`) and are never committed to the repository.

---

## 4. Device Used

- **Detected Environment:** CPU (`torch.cuda.is_available() == False`).
- **Selected Device:** `cpu`.
- **Diagnostics Reporting:** The active device is surfaced in `SemanticResult.evidence["device"]`.

---

## 5. Negative Test Comparison: Prompt A vs Prompt B on `hitech_girl.mp4`

Both prompts were evaluated on the exact same 240-frame video `hitech_girl.mp4`:

### Prompt A (Aligned):
`"a girl in hyderabad is walking with her dog"`
- **Semantic Status:** `PASS`
- **Mean Similarity Score:** `0.3161`
- **Top-Level Pipeline Decision:** `PASS`
- **Reason Codes:** `[]`

### Prompt B (Negative / Unrelated):
`"a red airplane flying over a snowy mountain while a robot is playing football"`
- **Semantic Status:** `FAIL`
- **Mean Similarity Score:** `0.1327`
- **Top-Level Pipeline Decision:** `AUTO_RETRY`
- **Reason Codes:** `['SEMANTIC_LOW_ALIGNMENT']`

---

## 6. Frame-by-Frame Scores on `hitech_girl.mp4`

Total video frames: 240 (10.0 seconds at 24.0 fps).

| Sample Point | Frame Index | Timestamp | Prompt A Score | Prompt B Score | Visual Scene Description |
|:---:|:---:|:---:|:---:|:---:|:---|
| **0.00** | 0 | 0.000s | **0.3354** | 0.1363 | Close-up shot of girl walking dog on sunny street |
| **0.25** | 60 | 2.500s | **0.3094** | 0.1226 | Transition into wide shot walking near buildings |
| **0.50** | 120 | 5.000s | **0.3433** | 0.1606 | Side angle shot showing dog and girl walking |
| **0.75** | 179 | 7.458s | **0.2505** | 0.1169 | Wide low-angle street perspective |
| **1.00** | 239 | 9.958s | **0.3418** | 0.1272 | Final tracking shot of girl walking dog |
| **Mean** | — | — | **0.3161** | **0.1327** | Difference $\Delta = 0.1834$ |

---

## 7. Proof That Scores Are Dynamic (Not Hardcoded 0.25)

1. **Prompt Sensitivity:** Changing the prompt from a girl walking a dog to an airplane/robot drops the similarity from `0.3161` down to `0.1327` (a drop of 58%).
2. **Frame Sensitivity:** Prompt A scores fluctuate across camera angles (`0.3354`, `0.3094`, `0.3433`, `0.2505`, `0.3418`), proving that individual frame visual features drive the similarity.
3. **No 0.25 Constants:** None of the 5 sampled frames return `0.25`.
4. **Backend Verified:** `SemanticResult.evidence["model_backend"]` reports `"real_clip"`.

---

## 8. Model Fallback Behavior

When real CLIP is unavailable (simulated via offline error or missing weights):
- **Old Behavior:** Reported `PASS` with fake `0.25` score.
- **New Behavior:**
  - `status`: `CheckStatus.WARN` (or `FAIL` if strict).
  - `reason_codes`: `[ReasonCode.SEMANTIC_MODEL_UNAVAILABLE, ReasonCode.SEMANTIC_UNCERTAIN]`.
  - `evidence["model_backend"]`: `"clip_unavailable"`.
  - `evidence["error"]`: Exact initialization / loading exception string.
  - `score`: `None`.
  - **Decision Engine Outcome:** Consumes `SEMANTIC_UNCERTAIN` and routes to `HUMAN_REVIEW` instead of producing a false automated `PASS`.

---

## 9. Unit & Integration Test Results

### Semantic Unit Test Suite
Command: `python -m pytest tests/test_semantic.py -v`
```
tests/test_semantic.py::test_matching_prompt_passes PASSED               [  7%]
tests/test_semantic.py::test_low_alignment_prompt PASSED                 [ 14%]
tests/test_semantic.py::test_empty_prompt_fails PASSED                   [ 21%]
tests/test_semantic.py::test_custom_sampling_points PASSED               [ 28%]
tests/test_semantic.py::test_clip_model_initialization PASSED            [ 35%]
tests/test_semantic.py::test_text_embedding PASSED                       [ 42%]
tests/test_semantic.py::test_image_embedding PASSED                      [ 50%]
tests/test_semantic.py::test_cosine_similarity PASSED                    [ 57%]
tests/test_semantic.py::test_different_prompts_produce_different_scores PASSED [ 64%]
tests/test_semantic.py::test_multiple_frames_produce_valid_scores PASSED [ 71%]
tests/test_semantic.py::test_model_unavailable_behavior PASSED           [ 78%]
tests/test_semantic.py::test_fallback_does_not_return_fake_pass PASSED   [ 85%]
tests/test_semantic.py::test_existing_semantic_threshold_behavior PASSED [ 92%]
tests/test_semantic.py::test_real_clip_integration_on_hitech_girl PASSED [100%]

14 passed in 22.83s
```

### Full Regression Suite
Command: `python -m pytest -q`
```
74 passed in 207.08s (0:03:27)
```
All 74 tests pass across all QA modules (technical, temporal, semantic, artifact, decision, provenance, pipeline, CLI).

### Temporal Non-Regression Confirmation
On `hitech_girl.mp4`:
- Temporal Status: **`PASS`**
- Reason codes: **`[]`**
- Confirmed dropped frames: **`[]`**
- Shot boundary candidates: **`[65, 103, 170]`**
- Verified: `hitech_girl.mp4` did **not** regress to `TEMPORAL_FRAME_DROP`.

---

## 10. Remaining Limitations & Phase 3 Recommendations

1. **Complex Negations in Prompts:**
   CLIP ViT-B/32 has known limitations with syntactic negations (e.g. "a girl without a dog"). If negative prompting or fine-grained exclusion is required, negative prompt penalties or bounding box detectors can be added.
2. **Device Acceleration:**
   In environments with an NVIDIA GPU, installing CUDA-enabled PyTorch will automatically switch `device: "cpu"` to `device: "cuda"` via the existing auto-detection logic, speeding up batch inference ~5-10x.

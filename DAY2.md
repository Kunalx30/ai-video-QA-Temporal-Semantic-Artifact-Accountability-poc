# DAY 2 — MEMBER 8 IMPLEMENTATION TASK
## Temporal / Semantic / Artifact QA + Accountability
### Antigravity Agent Instructions

> **Purpose:** This file is the implementation specification for the Antigravity coding agent.
> Drop `DAY2.md` into the project root and execute the work from this specification.
>
> **Primary source of truth:** the Day 2 assignment document and the existing Member 8 `README.md`.
> **Important:** inspect the existing repository before changing anything. Reuse Day 1 code wherever it already satisfies the requirement. Do not blindly rewrite or replace working components.

---

# 1. YOUR ROLE

You are implementing:

**Member 8 — Kunal — QA: Temporal, Semantic, Artifact and Accountability**

Required branch:

```text
feature/member8-temporal-semantic-qa
```

Day 2 is **not** a production deployment task.

Do NOT add:

- AWS deployment
- GPU deployment
- Wan 2.2 deployment
- H100/H200/B200 infrastructure
- Kubernetes
- production API gateway
- authentication
- database
- production frontend
- real-model inference as a test prerequisite
- unrelated work belonging to other members

The module must run locally on deterministic mock data.

---

# 2. DAY 2 OBJECTIVE

Day 1 already contains most of the actual QA algorithms.

Day 2 must turn those algorithms into a:

1. deterministic QA test harness
2. labelled regression suite
3. clean-control validation system
4. shared `ClipMetadata` input flow
5. shared `QAResult` output flow
6. metadata/ffprobe validation layer
7. SHA-256/provenance result flow
8. threshold calibration system
9. QA report
10. repeatable automated test suite

The final flow should be:

```text
ClipMetadata + MP4 + shot description
                |
                v
         QA Test Harness
                |
      +---------+---------+----------------+
      |         |         |                |
      v         v         v                v
 Technical   Temporal   Artifact       Semantic
   QA          QA         QA             QA
      |         |         |                |
      +---------+---------+----------------+
                          |
                          v
                    Provenance
                    SHA-256
                          |
                          v
                  Decision Engine
                          |
             +------------+-------------+
             |            |             |
             v            v             v
           PASS      AUTO_RETRY    HUMAN_REVIEW
                          |
                          v
                    QAResult JSON
                          |
                          v
               Compare with expected
                          |
                          v
                 Regression result
```

---

# 3. FIRST ACTION — INSPECT THE REPOSITORY

Before writing or deleting code:

1. Inspect the complete project tree.
2. Read the existing `README.md`.
3. Inspect `pyproject.toml`.
4. Inspect `requirements.txt`.
5. Inspect `app/`.
6. Inspect `mock_data/`.
7. Inspect `tests/`.
8. Inspect `validation/`.
9. Inspect all existing Member 8 QA modules.
10. Inspect the current CLI.
11. Inspect existing fixture generation.
12. Inspect existing calibration code.
13. Run the existing tests.
14. Run the existing doctor/diagnostic command if available.

DO NOT assume that a file exists just because it is described in the README.

Create an internal implementation map:

```text
Requirement
    -> existing file
    -> current behavior
    -> KEEP / MODIFY / CREATE
```

Do not rewrite a working Day 1 implementation unless necessary.

---

# 4. GIT / BRANCH

If the requested branch does not exist:

```powershell
git checkout <existing-day1-branch>
git pull
git checkout -b feature/member8-temporal-semantic-qa
```

If it already exists:

```powershell
git checkout feature/member8-temporal-semantic-qa
git pull
```

Do not commit unrelated changes.

Before implementation:

```powershell
git status
```

At the end:

```powershell
git status
git diff
```

---

# 5. DAY 1 COMPONENTS TO REUSE

The Day 2 assignment says these are Day 1 components to reuse:

- FFmpeg defect-video generators
- duplicate-frame generator/detector
- dropped-frame generator/detector
- brightness flicker generator/detector
- speed-jump generator/detector
- freeze-frame generator/detector
- resolution-change generator/detector
- blur generator/detector
- black-frame generator/detector
- text-overlay generator/detector
- corrupted-metadata generator/detector
- temporal detectors
- artifact detectors
- semantic checker
- ffprobe validation
- checksum/provenance
- PASS / AUTO_RETRY / HUMAN_REVIEW decision engine

The existing README may contain more components than this. Reuse those too when appropriate.

The Day 2 README must explicitly contain a section:

```markdown
## Reuse from Day 1
```

and list the actual files/components found in the repository.

Do not claim something is reused unless it actually exists and works.

---

# 6. SHARED CONTRACTS — DO NOT RENAME REQUIRED FIELDS

The Day 2 shared contract says `ClipMetadata` contains:

```text
clip_id
shot_id
mode
source_type
file
duration_s
fps
width
height
aspect_ratio
codec
model
settings{}
reference_ids[]
motion_controls{}   # I2V only
seed
status
failure_reason
checksum_sha256
```

`mode`:

```text
T2V
I2V
```

`source_type`:

```text
MOCK
REAL
```

`status`:

```text
OK
FAILED
```

The shared `QAResult` shape is:

```text
qa_id
clip_id
qa_type
component_scores{}
reason_codes[]
decision
evidence_files[]
```

For Member 8:

```text
qa_type = TEMPORAL_SEMANTIC
```

Decision vocabulary:

```text
PASS
AUTO_RETRY
HUMAN_REVIEW
```

IMPORTANT:

- Do not rename required fields.
- Do not remove required fields.
- Existing Day 1 fields may remain.
- If the existing schema uses different names, prefer an adapter such as `to_contract()` instead of destroying the Day 1 schema.

Use the assignment's ID conventions:

```text
shot_id:
S01_SH02

clip_id:
CLIP_S01_SH02_T2V_01

fixture_id:
M8_001
```

---

# 7. INPUT CONTRACT

Member 8 consumes:

```text
ClipMetadata
+
MP4
+
prompt / shot description
```

The semantic check must use the shot description/prompt together with the actual clip.

Do not make the harness depend on another member's live implementation.

For Day 2, build local mock `ClipMetadata` fixtures.

Example:

```json
{
  "clip_id": "CLIP_S01_SH01_T2V_01",
  "shot_id": "S01_SH01",
  "mode": "T2V",
  "source_type": "MOCK",
  "file": "mock_data/media/M8_CLEAN_001.mp4",
  "duration_s": 4.0,
  "fps": 24,
  "width": 1280,
  "height": 720,
  "aspect_ratio": "16:9",
  "codec": "h264",
  "model": "mock-engine",
  "settings": {},
  "reference_ids": [],
  "motion_controls": {},
  "seed": 42,
  "status": "OK",
  "failure_reason": null,
  "checksum_sha256": ""
}
```

The exact fixture values must come from the generated media/ffprobe output, not hard-coded guesses.

---

# 8. OUTPUT CONTRACT — QAResult

Every evaluated clip must produce a machine-readable `QAResult`.

Example shape:

```json
{
  "qa_id": "QA_S01_SH01_001",
  "clip_id": "CLIP_S01_SH01_T2V_01",
  "qa_type": "TEMPORAL_SEMANTIC",
  "component_scores": {
    "technical": 1.0,
    "temporal": 1.0,
    "artifacts": 1.0,
    "semantic": 0.84,
    "provenance": 1.0
  },
  "reason_codes": [],
  "decision": "PASS",
  "evidence_files": []
}
```

For a defect:

```json
{
  "qa_id": "QA_S01_SH01_002",
  "clip_id": "CLIP_S01_SH01_T2V_02",
  "qa_type": "TEMPORAL_SEMANTIC",
  "component_scores": {
    "technical": 1.0,
    "temporal": 0.21,
    "artifacts": 1.0,
    "semantic": 0.82,
    "provenance": 1.0
  },
  "reason_codes": [
    "TEMPORAL_DUPLICATE_FRAMES"
  ],
  "decision": "AUTO_RETRY",
  "evidence_files": []
}
```

Do not invent fake scores. Scores must be produced by the actual implementation.

---

# 9. TECHNICAL MEDIA VALIDATION

Reuse the existing ffprobe validator.

For every fixture, validate the actual MP4 against `ClipMetadata`.

Check at minimum:

- decodability
- codec
- duration
- FPS
- width
- height
- aspect ratio where supported
- relevant stream/container metadata
- zero-byte/invalid media conditions

Flow:

```text
ClipMetadata
      +
MP4
      |
      v
   ffprobe
      |
      v
Actual media properties
      |
      v
Compare expected metadata
      |
      v
PASS / mismatch reason
```

If metadata does not match, record a clear reason code.

Do not silently overwrite expected metadata with actual metadata.

---

# 10. TEMPORAL QA

Reuse the existing temporal components.

At minimum preserve support for the Day 1 defect categories:

- duplicate frames
- dropped frames
- brightness/luminance flicker
- freeze frame
- speed/motion jump
- shot-boundary-aware behavior
- optical-flow based continuity where already implemented

The existing README may contain additional temporal detectors. Reuse them rather than replacing them.

Each detector must return machine-readable evidence.

Example:

```json
{
  "detector": "duplicate_frames",
  "status": "FAIL",
  "score": 0.22,
  "reason_code": "TEMPORAL_DUPLICATE_FRAMES",
  "evidence": {
    "frame_start": 45,
    "frame_end": 49
  }
}
```

The exact schema may follow the existing implementation if it already has one.

---

# 11. ARTIFACT QA

Reuse existing artifact detectors.

At minimum preserve:

- black frames
- blur
- resolution inconsistency/change
- text overlay
- decode failure/corruption

The Day 1 README may contain additional artifact checks. Preserve them.

Each failure must have a clear machine-readable reason code.

Examples:

```text
ARTIFACT_BLACK_FRAME
ARTIFACT_BLUR
ARTIFACT_RESOLUTION_CHANGE
ARTIFACT_TEXT_OVERLAY
ARTIFACT_DECODE_FAILURE
```

Use the repository's existing reason-code names when they already exist.

Do not create duplicate reason codes for the same condition.

---

# 12. SEMANTIC QA

Reuse the existing semantic checker.

The required Day 2 semantic flow is:

```text
ClipMetadata
+
shot description / prompt
+
MP4
      |
      v
deterministic frame sampling
      |
      v
CLIP semantic evaluation
      |
      v
aggregate score
      |
      v
semantic decision/evidence
```

Use the existing CLIP implementation if already present.

Do not replace the existing semantic implementation with a dummy score.

Do not make GPU inference mandatory.

If the repository has a model-unavailable fallback, preserve it and make the behavior explicit in the report/tests.

The semantic check must be repeatable.

---

# 13. PROVENANCE / ACCOUNTABILITY

Reuse the existing checksum/provenance implementation.

For every fixture:

```text
MP4
 |
 v
SHA-256
 |
 v
ClipMetadata.checksum_sha256
 |
 v
QAResult / evidence / report
```

The checksum must be computed from the actual input file.

Do not use a hard-coded checksum.

If Ed25519/signing already exists, preserve it as an existing Day 1 capability, but do not make signing mandatory unless the existing project already requires it.

---

# 14. DECISION ENGINE

Reuse the existing deterministic decision engine.

Final decision must be one of:

```text
PASS
AUTO_RETRY
HUMAN_REVIEW
```

Document the reason-code mapping.

Example structure:

```markdown
| Reason Code | Decision |
|---|---|
| TEMPORAL_DUPLICATE_FRAMES | AUTO_RETRY |
| TEMPORAL_FRAME_DROP | AUTO_RETRY |
| TEMPORAL_FLICKER | AUTO_RETRY |
| TEMPORAL_FREEZE | AUTO_RETRY |
| TEMPORAL_MOTION_ANOMALY | AUTO_RETRY |
| ARTIFACT_BLACK_FRAME | AUTO_RETRY |
| ARTIFACT_BLUR | AUTO_RETRY |
| ARTIFACT_RESOLUTION_CHANGE | AUTO_RETRY |
| ARTIFACT_TEXT_OVERLAY | HUMAN_REVIEW |
| SEMANTIC_LOW_ALIGNMENT | AUTO_RETRY |
| SEMANTIC_UNCERTAIN | HUMAN_REVIEW |
| PROVENANCE_HASH_FAILURE | HUMAN_REVIEW |
```

IMPORTANT:

This table is an implementation target/example, not permission to overwrite an existing validated project policy blindly.

First inspect the existing decision engine and reason codes. Reuse them if already correct.

---

# 15. DETERMINISTIC FIXTURE REGRESSION SUITE

This is the main new Day 2 work.

Build a harness that:

1. loads fixture manifest
2. loads ClipMetadata
3. loads MP4
4. loads prompt/shot description
5. runs every applicable QA check
6. generates QAResult
7. compares actual result to expected result
8. records PASS/FAIL for the test
9. stores evidence
10. produces a final regression report

Suggested command:

```powershell
python -m app.cli regression
```

If the existing CLI architecture makes another command name more appropriate, keep the CLI consistent with the project.

The command must run deterministically.

---

# 16. FIXTURE REQUIREMENT

Create:

**20+ defect fixtures plus matching clean controls.**

Every defect type must have at least one labelled fixture.

Each defect fixture must have:

```text
MP4
ClipMetadata JSON
prompt/shot-description fixture
expected JSON
fixture manifest entry
```

Each defect fixture must have a matching clean control generated from the same source where practical.

The clean control is important because the goal is not only:

```text
detect defects
```

but also:

```text
do not reject clean clips
```

---

# 17. RECOMMENDED FIXTURE CATEGORIES

Use the Day 1 generator capabilities already present.

Aim for more than the minimum 20 defect fixtures.

A good target is approximately:

### Temporal

```text
M8_TEMP_001 duplicate frames
M8_TEMP_002 duplicate frames
M8_TEMP_003 frame drop
M8_TEMP_004 frame drop
M8_TEMP_005 flicker
M8_TEMP_006 flicker
M8_TEMP_007 freeze
M8_TEMP_008 freeze
M8_TEMP_009 motion/speed jump
M8_TEMP_010 motion/speed jump
```

### Artifact

```text
M8_ART_001 black frame
M8_ART_002 black frame
M8_ART_003 blur
M8_ART_004 blur
M8_ART_005 resolution change
M8_ART_006 resolution change
M8_ART_007 text overlay
M8_ART_008 text overlay
M8_ART_009 decode/corruption
M8_ART_010 decode/corruption
```

### Technical / metadata

```text
M8_TECH_001 wrong FPS
M8_TECH_002 wrong resolution
M8_TECH_003 wrong codec/metadata condition
M8_TECH_004 wrong duration/metadata condition
```

This gives approximately 24 defect fixtures.

The actual number can be higher if generation remains deterministic and the test suite stays manageable.

---

# 18. CLEAN CONTROLS

For each defect fixture, provide a clean control.

Example:

```text
source_001_clean.mp4
source_001_duplicate.mp4

source_002_clean.mp4
source_002_blur.mp4

source_003_clean.mp4
source_003_flicker.mp4
```

The control must use the same underlying source whenever practical.

Expected result:

```text
clean control -> PASS
defect fixture -> expected failure decision
```

Do not make clean controls artificially perfect in a way that makes the comparison meaningless.

---

# 19. FIXED SEEDS / DETERMINISM

Fixture generation must be reproducible.

Use:

- fixed seeds
- deterministic FFmpeg transformations
- deterministic OpenCV transformations where used
- deterministic frame sampling
- deterministic ordering
- stable fixture IDs
- stable manifest ordering

Running:

```powershell
python mock_data/generate_fixtures.py
```

twice should not produce logically different fixture definitions.

If timestamps are stored, do not allow them to make the regression comparison fail.

---

# 20. MANIFEST

Use or extend:

```text
mock_data/manifest.json
```

Each fixture should contain enough information to reproduce and evaluate it.

Recommended shape:

```json
{
  "fixture_id": "M8_TEMP_001",
  "module": "member8_qa",
  "video": "media/M8_TEMP_001.mp4",
  "input_metadata": "inputs/M8_TEMP_001.json",
  "expected": "expected/M8_TEMP_001.json",
  "prompt": "inputs/M8_TEMP_001_prompt.json",
  "expected_decision": "AUTO_RETRY",
  "expected_reason_codes": [
    "TEMPORAL_DUPLICATE_FRAMES"
  ],
  "control_fixture_id": "M8_CLEAN_001",
  "failure_reason": "duplicate_frames",
  "seed": 42
}
```

If the repository already has a manifest schema, extend it instead of replacing it.

---

# 21. EXPECTED RESULT FILES

Create one expected result per fixture.

Example:

```json
{
  "fixture_id": "M8_TEMP_001",
  "expected_decision": "AUTO_RETRY",
  "expected_reason_codes": [
    "TEMPORAL_DUPLICATE_FRAMES"
  ]
}
```

Expected data must contain labels, not fake measured scores.

Measured scores come from the actual QA run.

The comparison layer should support:

```text
expected decision == actual decision
expected reason code present in actual reason codes
```

and appropriate component-level checks.

---

# 22. CALIBRATION

After the fixture set exists, run the QA engine against:

1. defect fixtures
2. clean controls

Calculate at minimum:

### Detection rate

```text
detected expected defects / total defect fixtures
```

### False-reject rate

```text
clean controls incorrectly rejected / total clean controls
```

Write the result to:

```text
calibration_report.md
```

Do not invent numbers.

Numbers must come from the actual run.

If thresholds need adjustment:

1. record old threshold
2. record new threshold
3. explain why
4. rerun regression
5. rerun clean controls
6. verify improvement
7. record final threshold

Do not tune thresholds until every defect is simply forced to pass.

The objective is balanced detection and clean-control behavior.

---

# 23. REGRESSION TESTS

Add automated tests for:

### Contract

- ClipMetadata can be loaded
- required fields are preserved
- QAResult can be serialized
- decision is valid

### Success

```text
clean fixture -> PASS
```

### Temporal failure

```text
duplicate fixture -> expected temporal reason
freeze fixture -> expected temporal reason
flicker fixture -> expected temporal reason
frame-drop fixture -> expected temporal reason
motion-jump fixture -> expected temporal reason
```

### Artifact failure

```text
black frame -> expected artifact reason
blur -> expected artifact reason
resolution change -> expected artifact reason
text overlay -> expected artifact reason
corruption -> expected artifact/technical reason
```

### Technical

```text
wrong FPS -> mismatch
wrong resolution -> mismatch
wrong duration -> mismatch
invalid metadata -> mismatch
```

### Semantic

```text
matching prompt -> acceptable semantic result
negative/wrong prompt -> expected semantic behavior
```

### Provenance

```text
SHA-256 is generated
SHA-256 is recorded
```

### Determinism

Run the same fixture twice and compare:

- decision
- reason codes
- fixture identity
- checksum
- deterministic detector outputs where applicable

Do not compare generated timestamps.

---

# 24. QA REPORT

Create:

```text
QA_REPORT.md
```

It should contain:

```markdown
# Member 8 QA Report

## Executive Summary

## Fixture Summary

- total defect fixtures
- total clean controls
- total executed
- total passed
- total failed

## Technical QA

## Temporal QA

## Artifact QA

## Semantic QA

## Provenance / Accountability

## Decision Distribution

- PASS
- AUTO_RETRY
- HUMAN_REVIEW

## Detection Rates

## False Reject Rate

## Failed Fixtures

## Threshold Calibration

## Known Limitations

## Final Acceptance Status
```

All numbers must be generated from actual test output.

---

# 25. TEST_REPORT.md

Create or update:

```text
TEST_REPORT.md
```

Use this table structure:

```markdown
| Test ID | Input Fixture | Input Type | Expected | Actual | Status | Output | Reason | Notes |
|---|---|---|---|---|---|---|---|---|
```

For each executed test include:

- Test ID
- input fixture
- MOCK/REAL
- expected result
- actual result
- PASS/FAIL
- output/evidence
- reason
- notes

Do not manually claim tests passed.

Generate this report from the actual test/harness output where practical.

---

# 26. EVIDENCE FILES

The `QAResult.evidence_files[]` field must point to actual files when evidence is generated.

Examples:

```text
evidence/
    M8_TEMP_001_temporal.json
    M8_TEMP_001_frames.jpg
    M8_ART_001_artifact.json
    M8_SEM_001_semantic.json
```

Do not put nonexistent paths into `evidence_files`.

If the existing implementation already stores evidence elsewhere, reuse that location.

---

# 27. DEMO

Keep the existing Gradio workbench if it exists.

Also provide a simple CLI demonstration.

Minimum demonstration:

### Success

```text
clean MP4
    -> QA
    -> PASS
```

### Failure

```text
defective MP4
    -> QA
    -> reason code
    -> AUTO_RETRY or HUMAN_REVIEW
```

The demo must use actual generated fixtures.

Do not use hard-coded fake output.

---

# 28. README UPDATES

Update the existing README without destroying the Day 1 documentation.

Add:

```markdown
## Reuse from Day 1
```

Add:

```markdown
## Day 2 Implementation
```

Include:

- Day 2 objective
- ClipMetadata input
- QAResult output
- regression harness
- fixture strategy
- clean controls
- semantic evaluation
- ffprobe validation
- SHA-256 provenance
- decision mapping
- threshold calibration
- test commands
- report locations
- known limitations

Also update the project structure if new files are created.

---

# 29. COMMANDS TO SUPPORT

Preserve existing commands.

If compatible with the current architecture, support:

```powershell
# Environment
python -m app.cli --doctor

# Single-video QA
python -m app.cli qa --video <video> --prompt "<prompt>"

# Generate deterministic fixtures
python mock_data/generate_fixtures.py

# Run complete regression suite
python -m app.cli regression

# Run calibration
python mock_data/run_calibration.py

# Run tests
python -m pytest -q
```

If the current project already uses different commands, do not break them just to match this example. Add aliases/subcommands where appropriate.

---

# 30. IMPORTANT: NO GPU DEPENDENCY

Normal Day 2 testing must run locally without a GPU.

Do not make Wan 2.2 or any real video-generation model a prerequisite.

The fixture videos must be produced with deterministic FFmpeg/OpenCV transformations.

The semantic model may use the existing project implementation and existing fallback behavior.

Document model availability clearly.

---

# 31. IMPORTANT: DO NOT FABRICATE RESULTS

Never write:

```text
100% detection
0% false reject
74 tests passed
```

unless the command actually produced those results.

Every report number must come from the real test run.

If something fails:

```text
FAILED
```

and explain why.

Do not weaken tests merely to obtain green output.

Do not delete failing fixtures just because a detector cannot detect them.

If a threshold needs tuning, document the calibration.

---

# 32. FAILURE HANDLING

When a detector cannot classify a fixture confidently:

- return the appropriate existing reason code
- use `HUMAN_REVIEW` if the existing decision policy says the result is borderline
- do not silently convert uncertainty into PASS
- record the evidence
- include the case in the report

If a fixture itself is malformed intentionally, distinguish:

```text
fixture generation failure
```

from:

```text
QA correctly detected malformed media
```

---

# 33. EXPECTED PROJECT ADDITIONS

Do not force these exact filenames if the existing architecture has equivalent files, but the final project should contain equivalents of:

```text
qa_harness/
    runner.py
    comparator.py
    report.py

mock_data/
    manifest.json
    generate_fixtures.py
    run_calibration.py
    media/
    inputs/
    expected/
    failures/
    metadata/

tests/
    test_qa_harness.py
    test_qa_result.py
    test_contract.py
    test_clean_controls.py
    test_calibration.py

QA_REPORT.md
TEST_REPORT.md
calibration_report.md
```

Reuse existing `mock_data` and test files when possible.

---

# 34. IMPLEMENTATION ORDER

Follow this exact order.

## Phase 1 — Inspect

- inspect repository
- inspect Day 1 code
- run existing tests
- document reuse map

## Phase 2 — Contract

- implement/verify ClipMetadata adapter
- implement/verify QAResult
- preserve existing QAReport if needed
- add conversion adapter if needed

## Phase 3 — Fixture system

- inspect existing generators
- preserve existing fixtures
- add deterministic fixtures
- add matching clean controls
- create manifest
- create metadata/input/expected files

## Phase 4 — Harness

- build fixture loader
- run all checks
- collect component results
- generate QAResult
- compare expected vs actual
- store evidence

## Phase 5 — Technical + provenance

- validate ClipMetadata vs ffprobe
- compute SHA-256
- store checksum
- preserve provenance

## Phase 6 — Semantic

- connect prompt/shot description
- run existing semantic checker
- record score/evidence
- preserve deterministic behavior

## Phase 7 — Decision

- connect existing decision engine
- verify reason-code mapping
- verify PASS/AUTO_RETRY/HUMAN_REVIEW

## Phase 8 — Calibration

- run defects
- run clean controls
- calculate detection rate
- calculate false-reject rate
- tune thresholds only if necessary
- rerun regression

## Phase 9 — Tests

```powershell
python -m pytest -q
```

Fix actual failures.

## Phase 10 — Reports

Generate:

```text
TEST_REPORT.md
QA_REPORT.md
calibration_report.md
```

## Phase 11 — Demo

Show:

```text
clean -> PASS
defect -> failure decision
```

## Phase 12 — Final verification

Run everything from a clean terminal.

---

# 35. FINAL ACCEPTANCE CRITERIA

Do not mark Day 2 complete until all of the following are true:

### Repository

- [ ] correct branch
- [ ] existing Day 1 functionality preserved
- [ ] no unrelated changes

### Contract

- [ ] ClipMetadata supported
- [ ] QAResult supported
- [ ] required fields not renamed/removed
- [ ] decision vocabulary is correct

### Fixtures

- [ ] 20+ defect fixtures
- [ ] every required Day 1 defect type represented
- [ ] matching clean controls
- [ ] prompt fixtures
- [ ] metadata fixtures
- [ ] expected result fixtures
- [ ] deterministic generation
- [ ] fixed seeds
- [ ] manifest

### QA

- [ ] technical validation
- [ ] temporal validation
- [ ] artifact validation
- [ ] semantic validation
- [ ] SHA-256
- [ ] provenance
- [ ] decision engine

### Regression

- [ ] every fixture automatically executed
- [ ] actual vs expected comparison
- [ ] evidence files
- [ ] repeatable results

### Calibration

- [ ] defect detection rate calculated
- [ ] clean-control false-reject rate calculated
- [ ] threshold changes documented if any

### Reports

- [ ] QA_REPORT.md
- [ ] TEST_REPORT.md
- [ ] calibration_report.md
- [ ] README updated

### Demo

- [ ] success case
- [ ] failure case

### Testing

- [ ] existing tests still pass
- [ ] new tests pass
- [ ] no fake test results
- [ ] no GPU required for normal test execution

---

# 36. FINAL COMMAND SEQUENCE

At the end, run the actual commands supported by the project.

Recommended sequence:

```powershell
git status

python -m app.cli --doctor

python mock_data/generate_fixtures.py

python -m app.cli regression

python mock_data/run_calibration.py

python -m pytest -q
```

Then inspect:

```text
TEST_REPORT.md
QA_REPORT.md
calibration_report.md
mock_data/manifest.json
```

Then:

```powershell
git diff
git status
```

Do not commit until the final diff has been reviewed.

---

# 37. FINAL RESPONSE FROM THE AGENT

When implementation is complete, report:

```text
DAY 2 MEMBER 8 STATUS

Branch:
<actual branch>

Day 1 components reused:
<list>

New files:
<list>

Modified files:
<list>

Defect fixtures:
<number>

Clean controls:
<number>

Regression tests:
<number passed / failed>

Detection rate:
<actual result>

False reject rate:
<actual result>

Decision distribution:
PASS:
AUTO_RETRY:
HUMAN_REVIEW:

QA report:
<path>

Calibration report:
<path>

TEST_REPORT:
<path>

Known limitations:
<list>

Git status:
<clean/changes remaining>
```

Do not claim completion if acceptance criteria are not actually satisfied.

---

# 38. MOST IMPORTANT RULE

**Do not rebuild Member 8 from scratch.**

The Day 2 assignment explicitly expects the existing Day 1 defect generators, detectors, semantic checker, ffprobe validation, checksum/provenance and decision engine to be reused.

The main Day 2 change is:

```text
DAY 1
Individual QA components
        |
        v
DAY 2
Deterministic project-style QA harness
        |
        +--> labelled fixtures
        +--> clean controls
        +--> ClipMetadata
        +--> QAResult
        +--> expected-result comparison
        +--> calibration
        +--> regression tests
        +--> reports
```

Implement incrementally and preserve working behavior.

**Start by inspecting the repository. Do not start by creating new files blindly.**

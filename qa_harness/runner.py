"""QA Harness Runner.

Loads manifest, executes QA checks against fixtures, generates evidence files,
produces QAResult contracts, and performs regression verification against expected outcomes.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.pipeline import VideoQAPipeline
from app.schemas.contract import ClipMetadata, QAResult
from app.schemas.report import QAReport
from qa_harness.comparator import ComparisonResult, QAComparator


class QAFixtureRunResult(BaseModel):
    """Result of running QA harness on an individual fixture."""
    fixture_id: str
    clip_id: str
    video_path: str
    is_control: bool
    source_type: str
    report: QAReport
    qa_result: QAResult
    comparison: ComparisonResult
    evidence_files: List[str]


class QAHarnessRunResult(BaseModel):
    """Aggregated outcome of running the full regression harness across fixtures."""
    total_fixtures: int
    total_passed: int
    total_failed: int
    defect_fixtures_total: int
    defect_fixtures_detected: int
    detection_rate: float
    clean_controls_total: int
    clean_controls_passed: int
    clean_controls_rejected: int
    false_reject_rate: float
    decision_distribution: Dict[str, int]
    fixture_results: List[QAFixtureRunResult]


class QAHarnessRunner:
    """Orchestrates regression execution across mock fixtures."""

    def __init__(
        self,
        base_dir: str | Path = "mock_data",
        evidence_dir: str | Path = "evidence",
        pipeline: Optional[VideoQAPipeline] = None,
    ):
        self.base_dir = Path(base_dir)
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = pipeline or VideoQAPipeline()

    def run_fixture(
        self,
        fixture_id: str,
        fixture_meta: Dict[str, Any],
    ) -> QAFixtureRunResult:
        """Run QA on a single fixture and record evidence and comparison result."""
        # 1. Resolve media path
        video_path_str = fixture_meta.get("video_path") or fixture_meta.get("video")
        if not video_path_str:
            video_path = self.base_dir / "media" / f"{fixture_id}.mp4"
        else:
            video_path = Path(video_path_str)

        # 2. Resolve prompt
        prompt = fixture_meta.get("prompt_text") or fixture_meta.get("prompt")
        if not prompt or prompt.endswith(".json"):
            prompt_file = self.base_dir / (fixture_meta.get("prompt") or f"inputs/{fixture_id}_prompt.json")
            if prompt_file.exists():
                try:
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        p_data = json.load(f)
                    prompt = p_data.get("prompt", "A golden glowing orb traveling smoothly across an evening sky.")
                except Exception:
                    prompt = "A golden glowing orb traveling smoothly across an evening sky."
            else:
                prompt = "A golden glowing orb traveling smoothly across an evening sky."

        # 3. Resolve ClipMetadata
        input_meta_path = self.base_dir / (fixture_meta.get("input_metadata") or f"inputs/{fixture_id}.json")
        clip_metadata: Optional[ClipMetadata] = None
        if input_meta_path.exists():
            try:
                with open(input_meta_path, "r", encoding="utf-8") as f:
                    in_data = json.load(f)
                if "clip_id" in in_data:
                    clip_metadata = ClipMetadata(**in_data)
            except Exception:
                clip_metadata = None

        clip_id = (
            clip_metadata.clip_id
            if clip_metadata
            else f"CLIP_{fixture_id.upper()}"
        )
        source_type = clip_metadata.source_type if clip_metadata else "MOCK"
        is_control = (
            fixture_meta.get("control_fixture_id") == fixture_id
            or "CLEAN" in fixture_id
            or fixture_id == "good"
        )

        # 4. Execute VideoQAPipeline
        report = self.pipeline.run(
            video_path=video_path,
            prompt=prompt,
            video_id=clip_id,
            metadata=clip_metadata,
        )

        # 5. Save machine-readable evidence files
        evidence_json_path = self.evidence_dir / f"{fixture_id}_evidence.json"
        evidence_payload = {
            "fixture_id": fixture_id,
            "clip_id": clip_id,
            "video_path": str(video_path.as_posix()),
            "decision": report.decision.value,
            "reason_codes": [r.value for r in report.reason_codes],
            "technical": {
                "status": report.technical.status.value,
                "width": report.technical.width,
                "height": report.technical.height,
                "fps": report.technical.fps,
                "duration_seconds": report.technical.duration_seconds,
                "codec": report.technical.video_codec,
                "evidence": report.technical.evidence,
            },
            "temporal": {
                "status": report.temporal.status.value,
                "score": report.temporal.score,
                "evidence": report.temporal.evidence,
            },
            "artifacts": {
                "status": report.artifacts.status.value,
                "score": report.artifacts.score,
                "evidence": report.artifacts.evidence,
            },
            "semantic": {
                "status": report.semantic.status.value,
                "score": report.semantic.score,
                "evidence": report.semantic.evidence,
            },
            "provenance": {
                "sha256": report.provenance.sha256,
                "video_id": report.video_id,
                "qa_run_id": report.qa_run_id,
            },
        }
        with open(evidence_json_path, "w", encoding="utf-8") as f:
            json.dump(evidence_payload, f, indent=2)

        evidence_files = [str(evidence_json_path.as_posix())]

        # 6. Build QAResult contract
        qa_result = QAResult.from_qa_report(
            report=report,
            clip_id=clip_id,
            evidence_files=evidence_files,
        )

        # 7. Resolve Expected Outcome & Compare
        expected_meta_path = self.base_dir / (fixture_meta.get("expected") or f"expected/{fixture_id}.json")
        expected_dict: Dict[str, Any] = {}
        if expected_meta_path.exists():
            try:
                with open(expected_meta_path, "r", encoding="utf-8") as f:
                    expected_dict = json.load(f)
            except Exception:
                expected_dict = {}

        if not expected_dict:
            expected_dict = {
                "expected_decision": fixture_meta.get("expected_decision", "PASS"),
                "expected_reason_codes": fixture_meta.get("expected_reason_codes", []),
            }

        comparison = QAComparator.compare(
            actual=qa_result,
            expected=expected_dict,
            fixture_id=fixture_id,
        )

        return QAFixtureRunResult(
            fixture_id=fixture_id,
            clip_id=clip_id,
            video_path=str(video_path.as_posix()),
            is_control=is_control,
            source_type=source_type,
            report=report,
            qa_result=qa_result,
            comparison=comparison,
            evidence_files=evidence_files,
        )

    def run_all(
        self,
        manifest_path: Optional[str | Path] = None,
        fixture_filter: Optional[List[str]] = None,
    ) -> QAHarnessRunResult:
        """Run QA across all registered fixtures and produce aggregated summary."""
        m_path = Path(manifest_path) if manifest_path else self.base_dir / "manifest.json"
        with open(m_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        fixtures: Dict[str, Any] = manifest.get("fixtures", {})
        results: List[QAFixtureRunResult] = []

        for fix_id, meta in fixtures.items():
            if fixture_filter and fix_id not in fixture_filter:
                continue
            item_res = self.run_fixture(fix_id, meta)
            results.append(item_res)

        total_fixtures = len(results)
        total_passed = sum(1 for r in results if r.comparison.passed)
        total_failed = total_fixtures - total_passed

        # Defect fixtures metrics
        defect_results = [r for r in results if not r.is_control]
        defect_total = len(defect_results)
        defect_detected = sum(
            1 for r in defect_results
            if r.qa_result.decision != "PASS" and r.comparison.passed
        )
        detection_rate = (defect_detected / defect_total * 100.0) if defect_total > 0 else 100.0

        # Clean control metrics
        clean_results = [r for r in results if r.is_control]
        clean_total = len(clean_results)
        clean_passed = sum(1 for r in clean_results if r.qa_result.decision == "PASS")
        clean_rejected = clean_total - clean_passed
        false_reject_rate = (clean_rejected / clean_total * 100.0) if clean_total > 0 else 0.0

        # Decision distribution
        dist = {"PASS": 0, "AUTO_RETRY": 0, "HUMAN_REVIEW": 0}
        for r in results:
            d = r.qa_result.decision
            dist[d] = dist.get(d, 0) + 1

        return QAHarnessRunResult(
            total_fixtures=total_fixtures,
            total_passed=total_passed,
            total_failed=total_failed,
            defect_fixtures_total=defect_total,
            defect_fixtures_detected=defect_detected,
            detection_rate=round(detection_rate, 2),
            clean_controls_total=clean_total,
            clean_controls_passed=clean_passed,
            clean_controls_rejected=clean_rejected,
            false_reject_rate=round(false_reject_rate, 2),
            decision_distribution=dist,
            fixture_results=results,
        )

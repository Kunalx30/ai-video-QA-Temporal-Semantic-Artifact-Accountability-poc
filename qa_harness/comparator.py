"""QA Harness Comparator.

Compares actual QAResult against expected outcomes for regression verification.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.contract import QAResult


class ComparisonResult(BaseModel):
    """Structured result of comparing actual QA evaluation against expected outcome."""
    fixture_id: str
    passed: bool
    decision_matched: bool
    reasons_matched: bool
    expected_decision: str
    actual_decision: str
    expected_reasons: List[str]
    actual_reasons: List[str]
    notes: str = ""


class QAComparator:
    """Evaluates whether an actual QAResult satisfies labelled ground truth expectations."""

    @staticmethod
    def compare(
        actual: QAResult,
        expected: Dict[str, Any],
        fixture_id: Optional[str] = None,
    ) -> ComparisonResult:
        fix_id = fixture_id or actual.clip_id
        expected_decision = expected.get("expected_decision", "PASS")

        # Extract expected reason codes
        exp_reasons: List[str] = []
        if "expected_reason_codes" in expected and expected["expected_reason_codes"]:
            exp_reasons = [str(r) for r in expected["expected_reason_codes"]]
        elif "reason_code" in expected and expected["reason_code"]:
            exp_reasons = [str(expected["reason_code"])]

        actual_decision = actual.decision
        actual_reasons = actual.reason_codes

        # 1. Decision match
        decision_matched = (actual_decision == expected_decision)

        # 2. Reason codes match
        reasons_matched = True
        notes = []

        if expected_decision == "PASS":
            # Clean controls should have 0 active failure reason codes
            if actual_reasons:
                reasons_matched = False
                notes.append(f"Unexpected reason codes on clean control: {actual_reasons}")
        else:
            # Defect fixture: expected reason code(s) must be present in actual reasons
            if exp_reasons:
                matched_any = any(r in actual_reasons for r in exp_reasons)
                if not matched_any:
                    reasons_matched = False
                    notes.append(f"Expected reason code(s) {exp_reasons} not found in actual {actual_reasons}")

        if not decision_matched:
            notes.append(f"Decision mismatch: expected {expected_decision}, got {actual_decision}")

        passed = decision_matched and reasons_matched
        notes_str = "; ".join(notes) if notes else "Evaluation matches ground truth expectation."

        return ComparisonResult(
            fixture_id=fix_id,
            passed=passed,
            decision_matched=decision_matched,
            reasons_matched=reasons_matched,
            expected_decision=expected_decision,
            actual_decision=actual_decision,
            expected_reasons=exp_reasons,
            actual_reasons=actual_reasons,
            notes=notes_str,
        )

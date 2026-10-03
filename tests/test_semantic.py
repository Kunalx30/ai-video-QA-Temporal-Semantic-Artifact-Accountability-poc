"""Tests for semantic prompt alignment and CLIP integration (Phase 8)."""

import numpy as np
import pytest
from app.config import SemanticConfig
from app.media.frame_extractor import FrameExtractor
from app.schemas.results import CheckStatus, ReasonCode
from app.semantic import CLIPChecker, PromptAlignmentEvaluator


@pytest.fixture
def extractor():
    return FrameExtractor()


def test_matching_prompt_passes(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4"))
    evaluator = PromptAlignmentEvaluator()
    prompt = "A golden glowing orb traveling smoothly across an evening sky."
    result = evaluator.evaluate(frames, prompt)

    assert result.status == CheckStatus.PASS
    assert result.similarity_score is not None
    assert result.similarity_score >= 0.20
    assert len(result.sampled_frame_scores) == 5  # default 5 sample points
    assert len(result.reason_codes) == 0


def test_low_alignment_prompt(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4"))
    # Highly restrictive threshold to simulate misaligned semantic evaluation
    strict_config = SemanticConfig(pass_threshold=0.85, uncertain_threshold=0.60)
    evaluator = PromptAlignmentEvaluator(config=strict_config)
    result = evaluator.evaluate(frames, "A submerged submarine under polar ice.")

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.SEMANTIC_LOW_ALIGNMENT in result.reason_codes


def test_empty_prompt_fails(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=5))
    evaluator = PromptAlignmentEvaluator()
    result = evaluator.evaluate(frames, "")

    assert result.status == CheckStatus.FAIL
    assert ReasonCode.SEMANTIC_LOW_ALIGNMENT in result.reason_codes


def test_custom_sampling_points(extractor):
    frames = list(extractor.iter_frames("mock_data/media/good.mp4"))
    config = SemanticConfig(sample_points=[0.1, 0.9])
    evaluator = PromptAlignmentEvaluator(config=config)
    result = evaluator.evaluate(frames, "A golden glowing orb.")

    assert len(result.sampled_frame_scores) == 2
    assert result.evidence["sample_points"] == [0.1, 0.9]


def test_clip_model_initialization():
    """Test 1: Real CLIP model initializes with correct metadata."""
    clip = CLIPChecker()
    assert clip.model_name == "openai/clip-vit-base-patch32"
    assert clip.device in ["cpu", "cuda"]
    assert clip.is_real_model is True
    assert clip.model is not None
    assert clip.processor is not None


def test_text_embedding():
    """Test 2: Text embedding produces normalized vector of expected shape."""
    clip = CLIPChecker()
    embed = clip.get_text_embedding("a girl in hyderabad is walking with her dog")
    assert embed is not None
    assert embed.shape == (1, 512)
    # Norm should be approximately 1.0
    norm = float(embed.norm(dim=-1).item())
    assert abs(norm - 1.0) < 1e-4


def test_image_embedding():
    """Test 3: Image embedding produces normalized vector of expected shape."""
    clip = CLIPChecker()
    dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
    embeds = clip.get_image_embeddings([dummy_img])
    assert embeds is not None
    assert embeds.shape == (1, 512)
    norm = float(embeds.norm(dim=-1).item())
    assert abs(norm - 1.0) < 1e-4


def test_cosine_similarity():
    """Test 4: Cosine similarity logic is bounded and consistent."""
    clip = CLIPChecker()
    img_red = np.zeros((100, 100, 3), dtype=np.uint8)
    img_red[:, :, 2] = 255  # Red in BGR

    scores_red = clip.compute_similarity("a red image", [img_red])
    scores_blue = clip.compute_similarity("a blue ocean", [img_red])

    assert len(scores_red) == 1
    assert len(scores_blue) == 1
    # Scores must be bounded [0.0 - 1.0]
    assert 0.0 <= scores_red[0] <= 1.0
    assert 0.0 <= scores_blue[0] <= 1.0
    # Red description must align better to red image than blue description
    assert scores_red[0] > scores_blue[0]


def test_different_prompts_produce_different_scores(extractor):
    """Test 5: Distinct prompts produce distinct non-constant similarity scores."""
    from pathlib import Path
    hitech_path = Path("mock_data/media/hitech_girl.mp4")
    if not hitech_path.exists():
        pytest.skip("hitech_girl.mp4 not found")

    frames = list(extractor.iter_frames(str(hitech_path), max_frames=5))
    evaluator = PromptAlignmentEvaluator()

    prompt_matching = "a girl in hyderabad is walking with her dog"
    prompt_unrelated = "a red airplane flying over a snowy mountain while a robot is playing football"

    res_matching = evaluator.evaluate(frames, prompt_matching)
    res_unrelated = evaluator.evaluate(frames, prompt_unrelated)

    assert res_matching.score != res_unrelated.score
    assert res_matching.score > res_unrelated.score
    assert abs(res_matching.score - res_unrelated.score) > 0.10


def test_multiple_frames_produce_valid_scores(extractor):
    """Test 6: Multi-frame evaluation returns valid, calculated per-frame scores."""
    from pathlib import Path
    hitech_path = Path("mock_data/media/hitech_girl.mp4")
    if not hitech_path.exists():
        pytest.skip("hitech_girl.mp4 not found")

    frames = list(extractor.iter_frames(str(hitech_path)))
    evaluator = PromptAlignmentEvaluator()

    result = evaluator.evaluate(frames, "a girl in hyderabad is walking with her dog")
    assert len(result.sampled_frame_scores) == 5
    assert len(result.evidence["frame_details"]) == 5

    # Check frame details structure
    for d in result.evidence["frame_details"]:
        assert "frame_index" in d
        assert "timestamp_seconds" in d
        assert "similarity_score" in d
        assert 0.0 <= d["similarity_score"] <= 1.0

    # Ensure scores are dynamic, not all an identical hardcoded value
    scores = result.sampled_frame_scores
    assert not all(s == 0.25 for s in scores)


def test_model_unavailable_behavior(extractor):
    """Test 7: When CLIP is unavailable, reports UNCERTAIN with diagnostic error."""
    frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=3))

    # Stub CLIPChecker simulating unavailable model
    stub_clip = CLIPChecker.__new__(CLIPChecker)
    stub_clip.model_name = "openai/clip-vit-base-patch32"
    stub_clip.device = "cpu"
    stub_clip.model = None
    stub_clip.processor = None
    stub_clip.is_real_model = False
    stub_clip.init_error = "Simulated offline network error"

    evaluator = PromptAlignmentEvaluator(clip_checker=stub_clip)
    result = evaluator.evaluate(frames, "a test prompt")

    assert result.status == CheckStatus.WARN
    assert ReasonCode.SEMANTIC_MODEL_UNAVAILABLE in result.reason_codes
    assert ReasonCode.SEMANTIC_UNCERTAIN in result.reason_codes
    assert result.evidence["model_backend"] == "clip_unavailable"
    assert "Simulated offline network error" in result.evidence["error"]


def test_fallback_does_not_return_fake_pass(extractor):
    """Test 8: Model-unavailable state MUST NOT produce a false PASS."""
    frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=3))

    stub_clip = CLIPChecker.__new__(CLIPChecker)
    stub_clip.model_name = "openai/clip-vit-base-patch32"
    stub_clip.device = "cpu"
    stub_clip.model = None
    stub_clip.processor = None
    stub_clip.is_real_model = False
    stub_clip.init_error = "Model weights missing"

    evaluator = PromptAlignmentEvaluator(clip_checker=stub_clip)
    result = evaluator.evaluate(frames, "a test prompt")

    assert result.status != CheckStatus.PASS
    assert result.score is None or result.score == 0.0


def test_existing_semantic_threshold_behavior(extractor):
    """Test 9: Verifies calibrated threshold routing (PASS, WARN, FAIL)."""
    frames = list(extractor.iter_frames("mock_data/media/good.mp4", max_frames=3))

    # Test high threshold causing FAIL
    cfg_strict = SemanticConfig(pass_threshold=0.90, uncertain_threshold=0.80)
    res_fail = PromptAlignmentEvaluator(config=cfg_strict).evaluate(frames, "a test prompt")
    assert res_fail.status == CheckStatus.FAIL
    assert ReasonCode.SEMANTIC_LOW_ALIGNMENT in res_fail.reason_codes

    # Test middle threshold causing WARN
    cfg_warn = SemanticConfig(pass_threshold=0.90, uncertain_threshold=0.10)
    res_warn = PromptAlignmentEvaluator(config=cfg_warn).evaluate(frames, "A golden glowing orb traveling smoothly across an evening sky.")
    assert res_warn.status in [CheckStatus.PASS, CheckStatus.WARN]


def test_real_clip_integration_on_hitech_girl(extractor):
    """Integration Test: Real CLIP validation on hitech_girl.mp4 proves semantic differentiation."""
    from pathlib import Path
    hitech_path = Path("mock_data/media/hitech_girl.mp4")
    if not hitech_path.exists():
        pytest.skip("hitech_girl.mp4 fixture not found")

    frames = list(extractor.iter_frames(str(hitech_path)))
    evaluator = PromptAlignmentEvaluator()

    # Prompt A: Aligned
    prompt_a = "a girl in hyderabad is walking with her dog"
    res_a = evaluator.evaluate(frames, prompt_a)
    assert res_a.status == CheckStatus.PASS
    assert res_a.score is not None and res_a.score >= 0.22
    assert res_a.evidence["model_backend"] == "real_clip"

    # Prompt B: Unrelated
    prompt_b = "a red airplane flying over a snowy mountain while a robot is playing football"
    res_b = evaluator.evaluate(frames, prompt_b)
    assert res_b.status == CheckStatus.FAIL
    assert ReasonCode.SEMANTIC_LOW_ALIGNMENT in res_b.reason_codes
    assert res_b.score is not None and res_b.score < 0.18

    # Margin check
    assert res_a.score - res_b.score > 0.12

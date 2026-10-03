"""Interactive Gradio Workbench for Member 8 Video QA."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import gradio as gr

from app.pipeline import run_video_qa
from app.schemas.results import DecisionType


def get_available_samples() -> List[str]:
    """List available mock fixtures from mock_data/media."""
    media_dir = Path("mock_data/media")
    if not media_dir.exists():
        return []
    return [str(p.as_posix()) for p in sorted(media_dir.glob("*.mp4"))]


def load_sample_prompt(video_path: str) -> str:
    """Load default prompt associated with fixture if found in manifest."""
    manifest_path = Path("mock_data/manifest.json")
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            fixtures = data.get("fixtures", {})
            name = Path(video_path).stem
            if name in fixtures:
                return fixtures[name].get("prompt", "")
        except Exception:
            pass
    return "A golden glowing orb traveling smoothly across an evening sky."


def evaluate_video(
    video_file: Optional[str],
    prompt_text: str,
) -> Tuple[str, str, str, str, str, str, str, str]:
    """Execute Member 8 QA pipeline and format results for Gradio."""
    if not video_file:
        return (
            "NO VIDEO PROVIDED",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "Please select or upload a video file.",
            "{}",
        )

    prompt = prompt_text.strip() or "A test generated video scene."
    report = run_video_qa(video_path=video_file, prompt=prompt)

    # 1. Decision Styling
    dec = report.decision.value
    if dec == "PASS":
        decision_md = f"## 🟢 FINAL DECISION: **{dec}**\n*All acceptance criteria satisfied.*"
    elif dec == "AUTO_RETRY":
        decision_md = f"## 🟠 FINAL DECISION: **{dec}**\n*Recoverable defect detected. Automated retry recommended.*"
    else:
        decision_md = f"## 🔵 FINAL DECISION: **{dec}**\n*Ambiguous or elevated risk detected. Manual verification recommended.*"

    # 2. Components
    tech_info = f"**Status: {report.technical.status.value}**\n- Res: {report.technical.width}x{report.technical.height}\n- FPS: {report.technical.fps}\n- Codec: {report.technical.video_codec}\n- Duration: {report.technical.duration_seconds}s"
    temp_info = f"**Status: {report.temporal.status.value}**\n- Score: {report.temporal.score}\n- Flicker: {report.temporal.flicker_score}\n- Duplicate Ratio: {report.temporal.duplicate_ratio}\n- Freeze Ratio: {report.temporal.freeze_ratio}\n- Smoothness: {report.temporal.motion_smoothness}"
    sem_info = f"**Status: {report.semantic.status.value}**\n- Similarity: {report.semantic.similarity_score}\n- Sample Scores: {report.semantic.sampled_frame_scores}"
    art_info = f"**Status: {report.artifacts.status.value}**\n- Black Frames: {report.artifacts.black_frame_count}\n- Blur Score: {report.artifacts.blur_score}\n- Decode Errors: {report.artifacts.decode_errors_count}"
    prov_info = f"**Status: {report.provenance.status.value}**\n- Video ID: `{report.video_id}`\n- QA Run ID: `{report.qa_run_id}`\n- SHA-256: `{report.provenance.sha256[:16]}...`"

    reasons = [r.value for r in report.reason_codes]
    reasons_text = ", ".join(reasons) if reasons else "None (Clean)"

    raw_json = report.model_dump_json(indent=2)

    return (
        decision_md,
        tech_info,
        temp_info,
        sem_info,
        art_info,
        prov_info,
        reasons_text,
        raw_json,
    )


def create_demo() -> gr.Blocks:
    """Construct Gradio Workbench interface."""
    samples = get_available_samples()

    with gr.Blocks(title="Member 8 QA Workbench") as demo:
        gr.Markdown(
            """
            # 🎬 AI Video QA Workbench — Member 8
            ### Automated Temporal, Semantic, Visual Artifact, and Provenance Evaluation
            """
        )

        with gr.Row():
            with gr.Column(scale=5):
                video_input = gr.Video(label="Input Video (Upload or Select Sample)", sources=["upload"])
                if samples:
                    sample_dropdown = gr.Dropdown(
                        label="Quick Test Mock Fixtures",
                        choices=samples,
                        value=samples[0] if samples else None,
                    )
                else:
                    sample_dropdown = None

                prompt_input = gr.Textbox(
                    label="Prompt Text",
                    placeholder="Enter generation prompt...",
                    value="A golden glowing orb traveling smoothly across an evening sky.",
                    lines=2,
                )

                run_btn = gr.Button("🚀 RUN VIDEO QA", variant="primary", size="lg")

            with gr.Column(scale=7):
                decision_output = gr.Markdown("### Ready for QA evaluation.")
                reasons_output = gr.Textbox(label="Active Reason Codes", interactive=False)

                with gr.Row():
                    tech_card = gr.Markdown("### Technical\n*Pending*", label="Technical")
                    temp_card = gr.Markdown("### Temporal\n*Pending*", label="Temporal")

                with gr.Row():
                    sem_card = gr.Markdown("### Semantic\n*Pending*", label="Semantic")
                    art_card = gr.Markdown("### Artifacts\n*Pending*", label="Artifacts")

                prov_card = gr.Markdown("### Provenance\n*Pending*", label="Provenance")

                with gr.Accordion("🔍 Full JSON Report & Audit Evidence", open=False):
                    json_output = gr.Code(label="Audit Report", language="json")

        if sample_dropdown:
            def on_select_sample(s):
                prompt = load_sample_prompt(s)
                return s, prompt
            sample_dropdown.change(fn=on_select_sample, inputs=[sample_dropdown], outputs=[video_input, prompt_input])

        run_btn.click(
            fn=evaluate_video,
            inputs=[video_input, prompt_input],
            outputs=[
                decision_output,
                tech_card,
                temp_card,
                sem_card,
                art_card,
                prov_card,
                reasons_output,
                json_output,
            ],
        )

    return demo


if __name__ == "__main__":
    app = create_demo()
    print("Starting Gradio QA Workbench on http://127.0.0.1:7860 ...")
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)

"""Tests for Gradio demo workbench (Phase 14)."""

import pytest
import gradio as gr
from demo.gradio_app import create_demo, evaluate_video, get_available_samples


def test_gradio_demo_creation():
    demo = create_demo()
    assert isinstance(demo, gr.Blocks)


def test_evaluate_video_function():
    samples = get_available_samples()
    assert len(samples) > 0
    good_sample = next((s for s in samples if "good.mp4" in s), samples[0])

    res = evaluate_video(good_sample, "A golden glowing orb.")
    assert len(res) == 8
    decision_md, tech_info, temp_info, sem_info, art_info, prov_info, reasons, raw_json = res

    assert "FINAL DECISION" in decision_md
    assert "PASS" in decision_md
    assert "Status: PASS" in tech_info
    assert "Status: PASS" in temp_info


def test_evaluate_video_empty():
    res = evaluate_video(None, "")
    assert res[0] == "NO VIDEO PROVIDED"

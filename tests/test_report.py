"""The report must render from whatever the pipeline actually produces.

This test exists because it was missing. The linkage stage was revised (the
denominator-free measures replaced forward linkage as the headline) and the
report renderer was not updated with it, so CI failed with a KeyError the first
time it rendered a report. A renderer that is only exercised in CI is a renderer
that is only tested in production.

Marked ``slow`` because it runs the pipeline; keep the draw counts small so it
stays inside a normal test run.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from world_impact import report
from world_impact.data import load_dataset
from world_impact.pipeline import run_analysis

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def payload() -> dict:
    return run_analysis(
        dataset=load_dataset(),
        seed=7,
        smaa_draws=200,
        value_draws=4,
        null_iterations=5,
        pa_iterations=50,
        tensor_null_iterations=2,
        screen_trajectories=2,
        screen_targets=1,
        reference_panel=False,
    )


def test_json_is_serialisable(payload) -> None:
    text = json.dumps(report._jsonable(payload))
    assert len(text) > 1000


def test_report_renders_every_section(payload) -> None:
    text = report.render(payload)
    for heading in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7.", "## 9."):
        assert heading in text, heading
    assert "Limitations" in text


def test_report_carries_the_honest_caveats(payload) -> None:
    text = report.render(payload)
    assert "saturat" in text.lower()
    assert "no claim about acceleration" in text
    assert "Median forward linkage" not in text  # the retracted framing


def test_pipeline_is_deterministic_under_a_fixed_seed() -> None:
    """The property CI enforces across two full runs, asserted here cheaply."""
    dataset = load_dataset()
    settings: dict[str, Any] = {
        "smaa_draws": 100,
        "value_draws": 2,
        "null_iterations": 3,
        "pa_iterations": 50,
        "tensor_null_iterations": 2,
        "screen_trajectories": 2,
        "screen_targets": 1,
        "reference_panel": False,
    }
    first = report._jsonable(run_analysis(dataset=dataset, seed=11, **settings))
    second = report._jsonable(run_analysis(dataset=dataset, seed=11, **settings))
    assert first["structure"] == second["structure"]
    assert first["ranking"]["totals"] == second["ranking"]["totals"]
    assert first["linkage"]["verdict"] == second["linkage"]["verdict"]

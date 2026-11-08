"""Counterexamples behind the aggregation tutorial, on invented metric rows."""

import importlib.util
from pathlib import Path
from statistics import fmean, stdev
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "tutorials/aggregation/aggregation.py"
SPEC = importlib.util.spec_from_file_location("aggregation_tutorial", SCRIPT)
aggregation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aggregation)


def test_floor_is_midpoint_and_better_than_ceiling_is_clipped():
    assert aggregation.skill(1) == 0.5
    assert aggregation.skill(0) == aggregation.skill(-0.5) == 1
    assert 0 < aggregation.skill(4) < aggregation.skill(2) < 0.5


def test_units_and_metric_direction_do_not_change_skill():
    for x in (-0.5, 0, 0.5, 1, 4):
        expected = aggregation.skill(x)
        assert aggregation.skill(7 + 3 * x, 10, 7) == pytest.approx(expected)
        assert aggregation.skill(-x, -1, 0, "higher") == pytest.approx(expected)


@pytest.mark.parametrize("case", aggregation.RANKING_CASES)
def test_aggregation_order_reverses_candidate_comparison(case):
    title, direction, a, b = case
    a = aggregation.compare(a, direction)
    b = aggregation.compare(b, direction)
    assert (a["mean_skill"] - b["mean_skill"]) * (a["skill_of_mean"] - b["skill_of_mean"]) < 0, title


def test_convexity_gap_changes_sign_at_ceiling_clipping():
    away = aggregation.compare((0.1, 1.9))
    crossing = aggregation.compare((-0.5, 0.5))
    assert away["mean_skill"] > away["skill_of_mean"]
    assert crossing["mean_skill"] < crossing["skill_of_mean"]


def test_signed_raw_values_and_signed_anchors_use_absolute_values():
    assert aggregation.skill(-1, -1, 0, "absolute") == 0.5
    assert aggregation.skill(1, -1, 0, "absolute") == 0.5
    assert aggregation.compare((-1, 1), "absolute")["mean_skill"] == 0.5


def test_missing_or_nonfinite_metric_keeps_its_denominator():
    for missing in (None, float("nan"), float("inf"), -float("inf")):
        summary = aggregation.compare((0, missing))
        assert summary["raw_mean"] is summary["skill_of_mean"] is None
        assert summary["mean_skill"] == 0.5
        assert aggregation.panel_scores([(0, missing)], (0.5, 0.5)) == [50]


def test_same_marginals_can_have_different_panel_uncertainty():
    aligned, opposed, weights, independent_sd = aggregation.covariance_example()
    for j in range(2):
        assert sorted(row[j] for row in aligned) == sorted(row[j] for row in opposed)
    aligned_scores = aggregation.panel_scores(aligned, weights)
    opposed_scores = aggregation.panel_scores(opposed, weights)
    assert fmean(aligned_scores) == fmean(opposed_scores) == 75
    assert stdev(aligned_scores) > independent_sd > stdev(opposed_scores) == 0


def test_fixed_linear_weights_commute_with_averaging_skills():
    rows = ((0.1, 1.9), (0.8, None), (2, 0.2))
    weights = (0.25, 0.75)
    panel_mean = fmean(aggregation.panel_scores(rows, weights))
    marginal_mean = 100 * sum(
        w * fmean(aggregation.skill(row[j]) for row in rows)
        for j, w in enumerate(weights)
    )
    assert panel_mean == pytest.approx(marginal_mean)


def test_incomplete_panel_or_invalid_anchors_are_not_silently_repaired():
    with pytest.raises(ValueError):
        aggregation.panel_scores([(0,)], (0.5, 0.5))
    with pytest.raises(ValueError):
        aggregation.panel_scores([(0, 1)], (0.25, 0.25))
    with pytest.raises(ValueError):
        aggregation.skill(1, floor=0, ceiling=0)


def test_cli_runs_without_dependencies():
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT)], capture_output=True, text=True,
        check=True, timeout=10,
    )
    assert "Winner by skill(mean raw): B; by mean(skill raw): A" in result.stdout
    assert "Signed cancellation" in result.stdout
    assert "opposed mean=75.000; sample SD=0.000" in result.stdout
    assert result.stderr == ""

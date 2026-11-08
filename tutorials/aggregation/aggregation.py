#!/usr/bin/env python3
"""Invented repeated-score examples. No files, network, fitting or dependencies."""

import sys
from math import isclose, isfinite, sqrt
from statistics import fmean, stdev


def skill(raw, floor=1.0, ceiling=0.0, direction="lower"):
    """Published hyperbolic conversion, using invented default anchors.

    Missing/nonfinite raw metrics contribute zero. Absolute-value metrics
    are scored on absolute value as lower-is-better terms; the published
    anchor table and the cited local tools also take absolute anchors.
    """
    if direction not in ("lower", "higher", "absolute"):
        raise ValueError("direction must be lower, higher or absolute")
    if not all(isfinite(x) for x in (floor, ceiling)):
        raise ValueError("anchors must be finite")
    if direction == "absolute":
        floor, ceiling = abs(floor), abs(ceiling)
    gap = ceiling - floor if direction == "higher" else floor - ceiling
    if gap <= 0:
        raise ValueError("ceiling must be better than floor")
    if raw is None or not isfinite(raw):
        return 0.0
    if direction == "absolute":
        raw = abs(raw)
    distance = ceiling - raw if direction == "higher" else raw - ceiling
    return 1.0 if distance <= 0 else gap / (gap + distance)


def compare(raw_values, direction="lower"):
    """Two estimands: skill of mean raw value, and mean repeat skill.

    The first is undefined if any repeat is missing. The second retains
    every repeat and applies the published missing-metric penalty.
    """
    values = tuple(raw_values)
    if not values:
        raise ValueError("at least one repeat is required")
    complete = all(x is not None and isfinite(x) for x in values)
    raw_mean = fmean(values) if complete else None
    return {
        "raw_mean": raw_mean,
        "skill_of_mean": skill(raw_mean, direction=direction) if complete else None,
        "mean_skill": fmean(skill(x, direction=direction) for x in values),
    }


def panel_scores(rows, weights):
    """Convert each complete repeat panel, retaining fixed metric weights."""
    weights = tuple(weights)
    if (not weights or not all(isfinite(w) and w >= 0 for w in weights)
            or not isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-12)):
        raise ValueError("finite nonnegative weights must sum to one")
    scores = []
    for row in rows:
        row = tuple(row)
        if len(row) != len(weights):
            raise ValueError("one weight is required per metric")
        scores.append(100 * sum(w * skill(x) for w, x in zip(weights, row)))
    if not scores:
        raise ValueError("at least one panel is required")
    return scores


RANKING_CASES = (
    ("Away from ceiling", "lower", (0.1, 1.9), (0.8, 0.8)),
    ("Crossing ceiling", "lower", (-0.5, 0.5), (0.1, 0.1)),
    ("Signed cancellation", "absolute", (-1.0, 1.0), (0.25, 0.25)),
)


def covariance_example():
    """Same marginal raw metrics, different pairing within each panel."""
    aligned = ((0.0, 0.0), (1.0, 1.0), (0.0, 0.0), (1.0, 1.0))
    opposed = ((0.0, 1.0), (1.0, 0.0), (0.0, 1.0), (1.0, 0.0))
    weights = (0.5, 0.5)
    marginal_sd = stdev(skill(row[0]) for row in aligned)
    independent_sd = 100 * sqrt(sum((w * marginal_sd) ** 2 for w in weights))
    return aligned, opposed, weights, independent_sd


def main():
    print("Synthetic metric rows only. No predictions are fitted or evaluated.")
    print("Invented anchors: floor=1, ceiling=0; lower is better unless marked absolute.")
    print("For distance d >= 0: skill=1/(1+d); d <= 0: skill=1.")
    print("All displayed skills are multiplied by 100. The floor is not a lower clip.")
    print("\n1. The conversion")
    print("raw:    -0.500    0.000    0.500    1.000    2.000    4.000")
    print("skill: " + " ".join(f"{100 * skill(x):8.3f}" for x in (-0.5, 0, 0.5, 1, 2, 4)))
    for index, (title, direction, a, b) in enumerate(RANKING_CASES, 2):
        print(f"\n{index}. {title}")
        print(f"direction={direction}; A raw={a}; B raw={b}")
        print("candidate  mean raw  skill(mean raw)  mean(skill raw)")
        results = []
        for name, values in (("A", a), ("B", b)):
            row = compare(values, direction)
            results.append(row)
            print(f"{name:9s} {row['raw_mean']:9.3f} {100 * row['skill_of_mean']:16.3f}"
                  f" {100 * row['mean_skill']:16.3f}")
        mean_first = "A" if results[0]["skill_of_mean"] > results[1]["skill_of_mean"] else "B"
        repeat_first = "A" if results[0]["mean_skill"] > results[1]["mean_skill"] else "B"
        print(f"Winner by skill(mean raw): {mean_first}; by mean(skill raw): {repeat_first}")
    print("\n5. A missing metric inside one repeat keeps its weight")
    missing = compare((0.0, None))
    print("raw=(0.0, None); skill(mean raw)=undefined")
    print(f"mean repeat skill={100 * missing['mean_skill']:.3f}; dropping missing=100.000")
    print("\n6. Marginal metric spread does not determine panel spread")
    aligned, opposed, weights, independent_sd = covariance_example()
    print(f"weights={weights}")
    for label, rows in (("aligned", aligned), ("opposed", opposed)):
        scores = panel_scores(rows, weights)
        marginal_mean_panel = 100 * sum(
            w * fmean(skill(row[j]) for row in rows) for j, w in enumerate(weights)
        )
        print(f"{label} raw={rows}")
        print(f"{label} panel scores=" + ", ".join(f"{x:.3f}" for x in scores))
        print(f"{label} mean={fmean(scores):.3f}; sample SD={stdev(scores):.3f}; "
              f"weighted marginal skill means={marginal_mean_panel:.3f}")
    print(f"SD if covariance were ignored={independent_sd:.3f} in either case")
    print("Average linear weighted skills in either order; keep whole repeat panels for SD.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(__doc__)
        sys.exit(0 if sys.argv[1] in ("-h", "--help") else 2)
    main()

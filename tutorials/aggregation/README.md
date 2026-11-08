# Average scores in the right order

MIT licensed. A synthetic-only lesson for teams summarising repeated local
scorer calls or resampling panels. Every raw metric, anchor and repeat below
is invented. There are no expression matrices, predictions, challenge files,
real run results or network calls.

The question is specific: are you estimating the mean raw metric, or the
mean score after the board's nonlinear conversion? They can prefer different
candidates. A second question concerns uncertainty: individual metric spreads
do not determine the spread of their weighted total.

## Run it

From the repository root, with Python:

```sh
python tutorials/aggregation/aggregation.py
uv run --with pytest --python 3.12 env PYTHONPATH=src python -m pytest -q tests/test_aggregation.py
```

The script uses the standard library and prints plain text. It reads and
writes no files, fits no predictors and needs no random seed. All cases are
small, explicit vectors. The tests check the counterexamples, unit changes, missing terms and linear averaging identity.

## The conversion and the two summaries

The [published scoring definition](https://virtualembryo.ai/challenge/evaluation?section=scoring&task=1)
converts a raw metric using its distance from the ceiling, measured in units
of the floor-to-ceiling gap. The floor is the midpoint of the skill scale,
not a lower clipping threshold. Better-than-ceiling values receive full
skill. Signed zero-ideal metrics are scored on absolute value as
lower-is-better terms. The page's anchor table adds that two-sided metrics
are compared on absolute value, anchors included; the cited local tools do
the same.
Missing or nonfinite declared metrics contribute zero with their weight kept.

For this lesson only, use the invented lower-is-better anchors printed below.
The conversion reduces to the displayed formula. These are not anchors for
any challenge board. The script also supports higher-is-better and signed
zero-ideal metrics.

For repeated raw values `m_r`, compare:

```text
skill of mean raw = skill(mean_r(m_r))
mean repeat skill = mean_r(skill(m_r))
```

Both summaries have a meaning. The
[published definition](https://virtualembryo.ai/challenge/evaluation?section=scoring&task=1)
converts each raw metric a submission produces. Some metrics use random
sampling, such as random gene pairs or subsampling to a shared cell count.
The page does not describe scorer repeats or converting a raw mean. If your
local repeats model that sampling, the comparable summary is mean repeat
skill; skill of the raw mean is a quantity the page never describes.
If the desired quantity is the average of
repeat board scores, convert within each repeat, then average. Transforming
the raw mean estimates a different quantity. A raw-metric mean remains
useful when that is the scientific quantity being studied. Neither summary
is the score of a new prediction obtained by blending the input predictions.

## Exact output

Every numerical example in this walkthrough is reproduced by the default
command. The following is its complete output, including all input rows.

```text
Synthetic metric rows only. No predictions are fitted or evaluated.
Invented anchors: floor=1, ceiling=0; lower is better unless marked absolute.
For distance d >= 0: skill=1/(1+d); d <= 0: skill=1.
All displayed skills are multiplied by 100. The floor is not a lower clip.

1. The conversion
raw:    -0.500    0.000    0.500    1.000    2.000    4.000
skill:  100.000  100.000   66.667   50.000   33.333   20.000

2. Away from ceiling
direction=lower; A raw=(0.1, 1.9); B raw=(0.8, 0.8)
candidate  mean raw  skill(mean raw)  mean(skill raw)
A             1.000           50.000           62.696
B             0.800           55.556           55.556
Winner by skill(mean raw): B; by mean(skill raw): A

3. Crossing ceiling
direction=lower; A raw=(-0.5, 0.5); B raw=(0.1, 0.1)
candidate  mean raw  skill(mean raw)  mean(skill raw)
A             0.000          100.000           83.333
B             0.100           90.909           90.909
Winner by skill(mean raw): A; by mean(skill raw): B

4. Signed cancellation
direction=absolute; A raw=(-1.0, 1.0); B raw=(0.25, 0.25)
candidate  mean raw  skill(mean raw)  mean(skill raw)
A             0.000          100.000           50.000
B             0.250           80.000           80.000
Winner by skill(mean raw): A; by mean(skill raw): B

5. A missing metric inside one repeat keeps its weight
raw=(0.0, None); skill(mean raw)=undefined
mean repeat skill=50.000; dropping missing=100.000

6. Marginal metric spread does not determine panel spread
weights=(0.5, 0.5)
aligned raw=((0.0, 0.0), (1.0, 1.0), (0.0, 0.0), (1.0, 1.0))
aligned panel scores=100.000, 50.000, 100.000, 50.000
aligned mean=75.000; sample SD=28.868; weighted marginal skill means=75.000
opposed raw=((0.0, 1.0), (1.0, 0.0), (0.0, 1.0), (1.0, 0.0))
opposed panel scores=75.000, 75.000, 75.000, 75.000
opposed mean=75.000; sample SD=0.000; weighted marginal skill means=75.000
SD if covariance were ignored=20.412 in either case
Average linear weighted skills in either order; keep whole repeat panels for SD.
```

## Read the counterexamples

**Away from the ceiling.** Candidate A has a worse mean raw distance, but a
higher mean repeat skill. On the unclipped part of the hyperbolic curve,
convexity makes the mean of converted values at least the converted mean.
This is Jensen's inequality applied to the stated score utility. It does
not establish that A is a better generative model, or justify adding noise
in search of score gains. These deliberately variable inputs demonstrate
what the summary measures. A candidate with high mean repeat skill and wide
repeat spread carries a different risk from a stable one; the
[selection tutorial](../selection/README.md)'s paired-difference advice
resolves the choice.

**Crossing the ceiling.** Some of A's repeats beat the ceiling. Their extra
raw improvement earns no extra skill. The clipping boundary removes the
global convexity argument, and the direction of the averaging gap changes.
A blanket claim that conversion always raises, or always lowers, a repeat
mean is false. Inspect the full repeat values when saturation is possible.

**Signed cancellation.** Opposite signed errors can cancel in a raw mean.
Their absolute errors still count in each repeat. A perfect-looking mean
signed error can therefore coexist with poor mean repeat skill. Keep signed
values for diagnosing systematic bias; convert each absolute value for the
score summary. This example describes separate scorer repeats. It says
nothing about whether combining two prediction files repairs either one.

**Missing terms.** A declared metric is unavailable in one repeat. Removing
it from the denominator rewards the incomplete result. Keep the declared
weight and the published missing-term penalty. This does not prescribe how
to handle a whole scorer call that crashed: report such a failure explicitly
and establish the cause rather than inventing metric values.

**Covariance.** Both panel examples have identical distributions for each
individual metric. The aligned panel's metrics succeed and fail together.
The opposed panel's contributions cancel each other's variation. Their mean
totals agree and their total spreads differ. Treating the metric contributions
as independent gives the same incorrect spread for both:

```text
Var(weighted total) = sum_j w_j^2 Var(skill_j)
                   + sum_{j != k} w_j w_k Cov(skill_j, skill_k)
```

The displayed SD is the sample standard deviation across repeat panel scores.
It is neither a confidence interval nor uncertainty about a future biological
specimen. Whole repeat vectors preserve the covariance. Independent metric
resampling would destroy it. Once conversion has happened, a fixed linear
weighted sum and an arithmetic mean do commute; both orders in the output
produce the same mean. Keep that identity separate from the nonlinear case.

## Use with existing tools

Preserve the raw metric panel for each local repeat. Apply that repeat's
metric directions, absolute values, anchors and fixed weights. Then summarise
the resulting repeat totals and, for a paired comparison, their within-repeat
differences. Do not substitute a table of mean raw metrics for the repeat
panels when the intended estimand is mean repeat score.

The earlier [Local Scoring Wrapper](https://github.com/xxx12e/vec-community-kit/tree/main/vec_local_score)
already provides per-seed skill aggregation, multi-seed summaries and paired
task-score differences. This lesson adds explicit counterexamples to
averaging raw metrics before conversion and an example that changes panel
spread while holding metric marginals fixed.
[VEC BatchRank](https://github.com/random-guy-05/vec-batchrank), filed first,
already converts each scorer repeat before summarising aggregate scores.
Use it for actual candidate batches. This lesson explains why that order
matters; it does not fix or replace BatchRank.
[Task Metric Lab](https://random-guy-05.github.io/vec-participation-workbench/metric-lab/?tool=metric-skill)
provides per-metric conversion and hierarchical weighting calculators for an
individual metric panel. This lesson adds repeated-vector rank reversals and
a covariance counterexample rather than another general score calculator.
[Metric Lens](https://github.com/i-habib/virtual-embryo-community/tree/main/metric-lens)
accounts for points and headroom in one panel.
[VEC Bootstrap](https://github.com/random-guy-05/vec-bootstrap) already covers
cell resampling and paired raw-metric uncertainty; its interpretation limits
also matter here. All five resources are credited as prior work.

For repeated candidate searches, winner's curse and paired comparisons, see
[this repository's selection tutorial](../selection/README.md). For whether
the proxy matches the intended task, see the
[proxy tutorial](../proxy/README.md). Correct arithmetic cannot resolve either
selection bias or a poorly chosen proxy.

## Limits

This is an arithmetic lesson, not a new predictive method or an official
scorer. No predictive-performance claim is made; there is no fitted method
to compare with trivial and simple predictors. Did it find a new scientific
result? No. The contribution is a worked explanation of repeated-score
aggregation, building on existing scoring tools.

The examples specify metric values directly. They do not show that a biological
model can attain those combinations. No actual metric computation, cellular
sampling or biological dependence is simulated. The two-summary difference
depends on the repeat distribution and anchors. No example estimates its size
on real data, predicts a hidden target, or recommends changing a prediction
from returned scores.

Use anchors only for the matching board, target and scorer version. An arbitrary
proxy needs its own justified evaluation definition; borrowing a validation
board's numerical anchors does not turn it into that board. Repeated scorer
seeds measure computational variation, not independent biological replication.
Averaging is a local reporting choice, not a claim that the challenge averages
scorer repeats. Its official ranking rules remain authoritative:
[current rules](https://virtualembryo.ai/challenge/rules),
[task definitions](https://virtualembryo.ai/challenge/tasks).

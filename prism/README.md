# Prism

A learner that is neither a tree nor a network.

Prism covers the input space with soft, overlapping regions, gives each region
its own **linear law**, and blends them. What makes it its own thing is how the
regions are placed: they are moved by the **residuals** of the laws they carry.
A region drifts towards the samples its own line explains well and away from the
ones it gets wrong. Nothing else moves them — switch the steering off and the
regions stay exactly where initialisation dropped them.

Runs unchanged on NumPy (CPU) or CuPy (GPU).

```python
from prism import PrismRegressor, PrismClassifier

model = PrismRegressor(n_experts="auto", device="auto").fit(X_train, y_train)
model.score(X_test, y_test)
```

---

## How it works

Every iteration is three closed-form steps. No learning rate, no line search,
no optimiser state.

**1. Gate.** A linear softmax over `K` experts gives responsibilities
`R = softmax(γ · X̃G)`, with `γ` a sharpness that grows on a schedule. The gate
is linear-softmax and not a density model on purpose: a Gaussian mixture can
only put regions where points are dense, and cannot draw a boundary like
`x₃ > 0` separating two regimes that live inside the same blob. Residual
steering needs a gate that can go where it is told.

**2. Experts.** Fold the responsibilities into the design,
`Z = [r₁·x̃ ‖ r₂·x̃ ‖ … ‖ r_K·x̃]`, and the whole mixture becomes one linear
model in the stacked weights. So:

- **regression** — the M-step is *exact*: one ridge solve of size `K(d+1)` lands
  on the global optimum for the current partition;
- **classification** — blended logits are not linear in the loss, so it takes
  bounded Newton steps instead. Böhning's quadratic bound replaces the Hessian
  with the constant `½ZᵀZ`, which gives guaranteed descent with no step size to
  pick and one factorisation shared across classes.

**3. Steering** — the part that is not standard. Compute what each expert would
have predicted for each sample on its own, turn that into per-sample blame
`ℓᵢₖ` measured against the best expert for that sample, and refit the gate to

```
Q = softmax( γ · ( X̃G − β·ℓ ) )
```

The experts are *never* fitted against `Q`. They only ever see the input-only
gate — exactly what inference will see — so the shipped model never depends on a
quantity unavailable at predict time. `β` (`competition`) is dimensionless:
`ℓ` is rescaled to the gate's own logit spread, so `β = 1` means one expert's
blame is worth the whole range of the gate's current opinion.

### The floor

Before the schedule starts, Prism fits and scores the **zero gate**. Uniform
responsibilities make the exact M-step collapse to plain ridge regression (or
multinomial logistic regression), so the linear model is always candidate zero.

Candidates are then generated simplest-first — linear, then flat gates, then
sharp ones — and the one that ships is the **earliest within one standard error
of the best held-out score**. The standard error is estimated from the
validation residuals themselves, so the rule tightens automatically when the
validation split is small. That is what stops a forty-sample split from talking
the model into something wiggly, and it is why the worst case is a linear model
rather than a mess.

---

## Results

`python benchmarks/bench_prism.py` — everything at library defaults, no
per-dataset tuning for anyone. Three train/test splits, mean reported.

**Regression (R²)**

| model | sine+interaction | piecewise-linear | friedman1 | diabetes |
| --- | --- | --- | --- | --- |
| linear (RidgeCV) | 0.024 | 0.316 | 0.737 | 0.442 |
| RandomForest | 0.765 | 0.981 | 0.866 | 0.316 |
| HistGradientBoosting | 0.908 | 0.980 | 0.928 | 0.310 |
| MLP (100,) | **0.969** | 0.978 | **0.939** | 0.278 |
| **Prism** | 0.841 | **0.982** | 0.916 | **0.445** |

**Classification (accuracy)**

| model | moons | circles | synth-3class | breast-cancer | wine | digits |
| --- | --- | --- | --- | --- | --- | --- |
| linear (LogReg) | 0.848 | 0.496 | 0.695 | 0.961 | 0.988 | 0.965 |
| RandomForest | 0.933 | 0.992 | 0.803 | 0.955 | **1.000** | 0.971 |
| HistGradientBoosting | 0.926 | 0.992 | **0.813** | 0.951 | **1.000** | 0.972 |
| MLP (100,) | **0.941** | **0.996** | 0.792 | 0.963 | 0.988 | **0.975** |
| **Prism** | 0.935 | 0.993 | 0.786 | **0.967** | 0.982 | 0.969 |

The honest summary:

- **It wins where the data really is piecewise linear.** On two linear regimes
  split by a hyperplane it beats every baseline, and on a cleaner version of
  that problem it reaches R² 0.988 where gradient boosting gets 0.940 and the
  *same model with `competition=0`* gets 0.451. That gap is the mechanism, not
  the tuning.
- **It never collapses.** Every other model on this table has a column where it
  falls apart — the forests and the network drop to R² ≈ 0.3 on diabetes, the
  linear model to 0.50 accuracy on circles. Prism is top or within a whisker on
  ten of ten, which is the point of the floor and the selection rule.
- **It does not beat gradient boosting or an MLP on everything**, and it is not
  meant to. Smooth nonlinearity that no small set of lines approximates well
  (`sine+interaction`) is where it gives up the most.
- **It is slower to fit than the baselines** at `n_experts="auto"`, since that
  is a small grid search. Pin `n_experts` to a number and it is one fit.

## `n_experts` is not a capacity dial

This is the one hyperparameter that matters, and it does not behave like the
number of trees in a forest. `K` is a claim about **how many linear regimes you
think the data contains**. More is not safer: with far more regions than
regimes the steering signal diffuses across near-duplicate experts and the fit
gets worse, not slower-but-better. Two well-placed experts beat sixteen badly
placed ones.

`n_experts="auto"` searches a small grid and keeps the best by the held-out
score `fit` already computes. It costs a handful of fits and touches no test
data.

## GPU

There is no separate GPU code path. Every heavy kernel is `matmul`, `einsum` or
`linalg.solve` on dense arrays, spelled identically in NumPy and CuPy, so
`prism.backend` only has to decide which module owns the arrays.

```python
PrismRegressor(device="auto")   # CuPy when a device is usable, NumPy otherwise
PrismRegressor(device="gpu")    # raise if CuPy is missing rather than fall back
PrismRegressor(device="cpu")
```

Install CuPy yourself (`pip install cupy-cuda12x` or whatever matches your
toolkit); Prism does not depend on it. The blended design `Z` is the one large
intermediate and it is accumulated in row chunks, so memory stays bounded by
`chunk_size` rather than by the sample count.

## Reading a prediction

Every prediction has one honest linear equation behind it:

```python
model.expert_weights(X)        # (n, K) responsibilities, rows sum to 1
model.local_coefficients(X)    # (n, d+1) the blended law applied to each row
```

## Parameters worth knowing

| name | default | what it does |
| --- | --- | --- |
| `n_experts` | `8` | number of linear regimes, or `"auto"` |
| `competition` | `1.0` | steering strength β; `0.0` disables it entirely |
| `sharpness_range` | per task | `(flat, sharp)` schedule for the gate |
| `tol` | `1.0` | standard errors of slack in the one-SE selection rule |
| `alpha` | `1e-3` | ridge on the experts, relative to the Gram diagonal |
| `validation_fraction` | `0.15` | held-out split driving selection; `0.0` uses train loss |
| `device` | `"auto"` | `"auto"`, `"cpu"` or `"gpu"` |

## Provenance

Mixtures of experts are Jacobs et al. (1991) and Jordan & Jacobs (1994); the
annealing is in the spirit of Rose (1998); seeding is k-means++ (Arthur &
Vassilvitskii, 2007); the classification bound is Böhning (1992). What is not
off the shelf: residual steering applied to the gate *only*, with the experts
held to the input-only gate, plus the linear-model floor and the one-standard-
error selection rule that make the whole thing hard to lose with.

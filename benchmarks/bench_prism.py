"""Prism against the usual baselines.

Everything runs at library defaults -- no per-dataset tuning for anyone,
including Prism, which picks its own `n_experts` from the held-out split it
already computes during `fit`. Scores are R^2 for regression and accuracy for
classification, averaged over three train/test splits.

    python benchmarks/bench_prism.py [--quick]
"""
from __future__ import annotations

import argparse
import time
import warnings

import numpy as np
from sklearn.datasets import (load_breast_cancer, load_diabetes, load_digits,
                              load_wine, make_circles, make_classification,
                              make_friedman1, make_moons)
from sklearn.ensemble import (HistGradientBoostingClassifier,
                              HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler

from prism import PrismClassifier, PrismRegressor

warnings.filterwarnings("ignore")
SEEDS = (0, 1, 2)


def regression_sets():
    rng = np.random.default_rng(0)

    X = rng.normal(size=(3000, 5))
    yield "sine+interaction", X, np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + \
        0.1 * rng.normal(size=3000)

    # Two linear regimes split by a hyperplane. A tree needs many axis-aligned
    # cuts to approximate that boundary; Prism can place it exactly.
    X = rng.normal(size=(4000, 8))
    y = np.where(X[:, 0] > 0, 2 * X[:, 1] - X[:, 2], -1.5 * X[:, 1] + 3 * X[:, 3])
    yield "piecewise-linear", X, y + 0.2 * rng.normal(size=4000)

    yield "friedman1", *make_friedman1(n_samples=2000, noise=1.0, random_state=0)

    d = load_diabetes()
    yield "diabetes", d.data, d.target


def classification_sets():
    yield "moons", *make_moons(n_samples=2000, noise=0.25, random_state=0)
    yield "circles", *make_circles(n_samples=2000, noise=0.12, factor=0.4,
                                   random_state=0)
    yield "synthetic-3class", *make_classification(
        n_samples=2000, n_features=20, n_informative=8, n_classes=3, random_state=0)
    b = load_breast_cancer()
    yield "breast-cancer", b.data, b.target
    w = load_wine()
    yield "wine", w.data, w.target
    d = load_digits()
    yield "digits", d.data, d.target


def models(kind, quick):
    if kind == "regression":
        out = {
            "linear (RidgeCV)": lambda: RidgeCV(),
            "RandomForest": lambda: RandomForestRegressor(
                n_estimators=100 if quick else 300, random_state=0, n_jobs=-1),
            "HistGradientBoost": lambda: HistGradientBoostingRegressor(random_state=0),
            "MLP (100,)": lambda: MLPRegressor(max_iter=600, random_state=0),
            "Prism": lambda: PrismRegressor(n_experts="auto", random_state=0),
        }
    else:
        out = {
            "linear (LogReg)": lambda: LogisticRegression(max_iter=2000),
            "RandomForest": lambda: RandomForestClassifier(
                n_estimators=100 if quick else 300, random_state=0, n_jobs=-1),
            "HistGradientBoost": lambda: HistGradientBoostingClassifier(random_state=0),
            "MLP (100,)": lambda: MLPClassifier(max_iter=600, random_state=0),
            "Prism": lambda: PrismClassifier(n_experts="auto", random_state=0),
        }
    return out


def evaluate(make_model, X, y, stratify):
    scores, seconds = [], []
    for seed in SEEDS:
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.3, random_state=seed,
            stratify=y if stratify else None)
        scaler = StandardScaler().fit(Xtr)
        Xtr, Xte = scaler.transform(Xtr), scaler.transform(Xte)
        t0 = time.perf_counter()
        model = make_model().fit(Xtr, ytr)
        seconds.append(time.perf_counter() - t0)
        scores.append(model.score(Xte, yte))
    return float(np.mean(scores)), float(np.mean(seconds))


def run(kind, sets, quick):
    zoo = models(kind, quick)
    names = [n for n, _, _ in sets]
    metric = "R^2" if kind == "regression" else "accuracy"
    print(f"\n{'=' * (22 + 18 * len(names))}")
    print(f"{kind.upper()}  ({metric}, mean over {len(SEEDS)} splits)")
    print(f"{'=' * (22 + 18 * len(names))}")
    print(f"{'model':<22}" + "".join(f"{n:>18}" for n in names) + f"{'fit s':>9}")
    table = {}
    for label, make in zoo.items():
        row, secs = [], []
        for _, X, y in sets:
            s, t = evaluate(make, X, y, stratify=(kind != "regression"))
            row.append(s)
            secs.append(t)
        table[label] = row
        print(f"{label:<22}" + "".join(f"{v:>18.4f}" for v in row)
              + f"{np.mean(secs):>9.2f}")
    best = [max(table[m][i] for m in table) for i in range(len(names))]
    wins = sum(abs(table["Prism"][i] - best[i]) < 1e-9 for i in range(len(names)))
    print(f"\nPrism is best on {wins}/{len(names)} datasets.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="smaller forests")
    args = ap.parse_args()
    run("regression", list(regression_sets()), args.quick)
    run("classification", list(classification_sets()), args.quick)


if __name__ == "__main__":
    main()

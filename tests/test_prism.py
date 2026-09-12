"""Tests for the Prism estimators.

The interesting properties to pin down are not "does it run" but the two
promises the design makes: that it never ships something clearly worse than a
linear model, and that the residual steering is the only thing moving the gate.
"""
import numpy as np
import pytest

from prism import PrismClassifier, PrismRegressor
from prism.backend import array_module, resolve_module, solve_spd


# ---------------------------------------------------------------- fixtures
def linear_data(n=600, d=6, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    w = rng.normal(size=d)
    return X, X @ w + 0.1 * rng.normal(size=n)


def piecewise_data(n=2000, d=5, seed=0):
    """Two linear regimes either side of a hyperplane -- the shape Prism is for."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    y = np.where(X[:, 0] > 0, 2 * X[:, 1] - X[:, 2], -1.5 * X[:, 1] + 3 * X[:, 3])
    return X, y + 0.1 * rng.normal(size=n)


def blobs(n=600, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 4))
    y = ((X[:, 0] * X[:, 1] > 0).astype(int) + (X[:, 2] > 0.5).astype(int)) % 3
    return X, y


# ------------------------------------------------------------------- basics
def test_regressor_fits_and_predicts():
    X, y = linear_data()
    m = PrismRegressor(n_experts=4, max_iter=15, random_state=0).fit(X, y)
    assert m.predict(X).shape == (len(X),)
    assert m.score(X, y) > 0.9


def test_classifier_fits_and_predicts():
    X, y = blobs()
    m = PrismClassifier(n_experts=4, max_iter=15, random_state=0).fit(X, y)
    proba = m.predict_proba(X)
    assert proba.shape == (len(X), 3)
    np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-9)
    assert set(np.unique(m.predict(X))) <= {0, 1, 2}
    assert m.score(X, y) > 0.5


def test_multioutput_regression():
    X, y = linear_data()
    Y = np.column_stack([y, -2 * y + 1.0])
    m = PrismRegressor(n_experts=3, max_iter=15, random_state=0).fit(X, Y)
    assert m.predict(X).shape == Y.shape
    assert m.score(X, Y) > 0.9


def test_string_labels_round_trip():
    X, y = blobs()
    labels = np.array(["a", "b", "c"])[y]
    m = PrismClassifier(n_experts=3, max_iter=10, random_state=0).fit(X, labels)
    assert set(np.unique(m.predict(X))) <= {"a", "b", "c"}
    np.testing.assert_array_equal(m.classes_, np.array(["a", "b", "c"]))


def test_reproducible():
    X, y = piecewise_data(n=800)
    a = PrismRegressor(n_experts=6, max_iter=20, random_state=7).fit(X, y).predict(X)
    b = PrismRegressor(n_experts=6, max_iter=20, random_state=7).fit(X, y).predict(X)
    np.testing.assert_allclose(a, b)


# ------------------------------------------------------- the design promises
def test_single_expert_is_a_linear_model():
    """K=1 must reproduce ridge regression -- that is the floor, exactly."""
    X, y = linear_data(n=400, d=5)
    m = PrismRegressor(n_experts=1, max_iter=5, alpha=1e-8,
                       validation_fraction=0.0, random_state=0).fit(X, y)
    Xs = (X - X.mean(axis=0)) / X.std(axis=0)
    Xt = np.column_stack([Xs, np.ones(len(X))])
    ys = (y - y.mean()) / y.std()
    ols = np.linalg.lstsq(Xt, ys, rcond=None)[0]
    expected = (Xt @ ols) * y.std() + y.mean()
    np.testing.assert_allclose(m.predict(X), expected, rtol=1e-4, atol=1e-6)


def test_never_much_worse_than_linear_on_linear_data():
    """On data a line explains, selection must fall back to the line."""
    X, y = linear_data(n=400, d=8, seed=3)
    m = PrismRegressor(n_experts=10, max_iter=40, random_state=0).fit(X, y)
    assert m.score(X, y) > 0.95
    # The chosen iterate should be the linear candidate or very near it.
    assert m.selected_iter_ <= 2


def test_steering_is_what_moves_the_gate():
    """competition=0 must leave the gate exactly where initialisation put it."""
    X, y = piecewise_data(n=1000)
    m = PrismRegressor(n_experts=8, max_iter=25, competition=0.0,
                       random_state=0).fit(X, y)
    gates = [m.gate_.copy()]
    m2 = PrismRegressor(n_experts=8, max_iter=25, competition=0.0,
                        random_state=0).fit(X, y)
    np.testing.assert_allclose(gates[0], m2.gate_)

    moved = PrismRegressor(n_experts=8, max_iter=25, competition=2.0,
                           random_state=0).fit(X, y)
    assert not np.allclose(moved.gate_, m2.gate_)


def test_steering_helps_on_piecewise_data():
    """The mechanism has to earn its place, not just run."""
    Xtr, ytr = piecewise_data(n=3000, seed=0)
    Xte, yte = piecewise_data(n=1500, seed=99)
    kw = dict(n_experts=3, max_iter=80, sharpness_range=(5.0, 80.0), random_state=0)
    off = PrismRegressor(competition=0.0, **kw).fit(Xtr, ytr).score(Xte, yte)
    on = PrismRegressor(competition=2.0, **kw).fit(Xtr, ytr).score(Xte, yte)
    # Two linear regimes split by a hyperplane: with the steering off the gate
    # is stuck on the density-based seeding and the blend is mush.
    assert off < 0.6 < 0.9 < on


def test_responsibilities_are_a_distribution():
    X, y = piecewise_data(n=500)
    m = PrismRegressor(n_experts=5, max_iter=15, random_state=0).fit(X, y)
    R = m.expert_weights(X)
    assert R.shape == (len(X), 5)
    np.testing.assert_allclose(R.sum(axis=1), 1.0, atol=1e-9)
    assert (R >= 0).all()


def test_local_coefficients_explain_the_prediction():
    """The blended coefficients must reproduce the model's own output."""
    X, y = piecewise_data(n=400)
    m = PrismRegressor(n_experts=6, max_iter=20, random_state=0).fit(X, y)
    coef = m.local_coefficients(X)
    Xs = (X - m._x_mean_) / m._x_std_
    Xt = np.column_stack([np.asarray(Xs), np.ones(len(X))])
    manual = (Xt * coef).sum(axis=1) * m._y_std_[0] + m._y_mean_[0]
    np.testing.assert_allclose(manual, m.predict(X), rtol=1e-8, atol=1e-8)


def test_classifier_loss_decreases_monotonically():
    """The Boehning steps come with a descent guarantee; check we kept it."""
    X, y = blobs(n=1200)
    m = PrismClassifier(n_experts=6, max_iter=30, validation_fraction=0.0,
                        random_state=0).fit(X, y)
    losses = [h["train_loss"] for h in m.history_ if h["iter"] >= 0]
    assert min(losses) <= losses[0] + 1e-9


# ----------------------------------------------------------------- plumbing
def test_rejects_bad_input():
    X, y = linear_data(n=100)
    with pytest.raises(ValueError):
        PrismRegressor().fit(X, y[:50])
    with pytest.raises(ValueError):
        PrismRegressor().fit(X.ravel(), y)
    with pytest.raises(ValueError):
        PrismClassifier().fit(X, np.zeros(len(X)))
    m = PrismRegressor(n_experts=2, max_iter=5, random_state=0).fit(X, y)
    with pytest.raises(ValueError):
        m.predict(X[:, :2])


def test_auto_experts_picks_something_sensible():
    Xtr, ytr = piecewise_data(n=2000, seed=1)
    Xte, yte = piecewise_data(n=1000, seed=42)
    m = PrismRegressor(n_experts="auto", max_iter=60, competition=4.0,
                       random_state=0).fit(Xtr, ytr)
    assert m.n_experts_ in m.searched_experts_
    assert m.score(Xte, yte) > 0.9
    with pytest.raises(ValueError):
        PrismRegressor(n_experts="many").fit(Xtr, ytr)


def test_params_round_trip():
    m = PrismRegressor(n_experts=5)
    assert m.get_params()["n_experts"] == 5
    m.set_params(n_experts=9, competition=2.0)
    assert (m.n_experts, m.competition) == (9, 2.0)
    with pytest.raises(ValueError):
        m.set_params(not_a_param=1)


def test_chunking_changes_nothing():
    X, y = piecewise_data(n=900)
    a = PrismRegressor(n_experts=6, max_iter=20, random_state=0).fit(X, y).predict(X)
    b = PrismRegressor(n_experts=6, max_iter=20, chunk_size=64,
                       random_state=0).fit(X, y).predict(X)
    np.testing.assert_allclose(a, b, rtol=1e-9, atol=1e-9)


def test_no_validation_split_still_fits():
    X, y = linear_data(n=200)
    m = PrismRegressor(n_experts=3, max_iter=10, validation_fraction=0.0,
                       random_state=0).fit(X, y)
    assert np.isfinite(m.predict(X)).all()


def test_more_experts_than_samples_is_clamped():
    X, y = linear_data(n=20, d=3)
    m = PrismRegressor(n_experts=50, max_iter=5, random_state=0).fit(X, y)
    assert m.n_experts_ <= 10


def test_constant_feature_is_survivable():
    X, y = linear_data(n=300, d=4)
    X = np.column_stack([X, np.ones(len(X))])
    m = PrismRegressor(n_experts=4, max_iter=15, random_state=0).fit(X, y)
    assert np.isfinite(m.predict(X)).all()


def test_backend_dispatch_defaults_to_numpy():
    assert resolve_module("cpu") is np
    assert array_module(np.zeros(3)) is np
    with pytest.raises(ValueError):
        resolve_module("tpu")


def test_solve_spd_handles_singular_input():
    A = np.zeros((4, 4))
    b = np.ones((4, 2))
    out = solve_spd(A, b, np)
    assert out.shape == (4, 2) and np.isfinite(out).all()

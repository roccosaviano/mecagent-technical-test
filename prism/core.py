"""Prism -- residual-steered mixtures of local linear experts.

The idea in one paragraph
-------------------------
A tree carves the input space with axis-aligned cuts and puts a constant in each
leaf. A neural net warps the space until a linear readout works. Prism keeps a
*soft* partition of the input space, gives every region its own linear law, and
blends them -- and then moves the boundaries using the residuals of the laws
they carry. A region drifts towards the samples its own linear law explains well
and away from the ones it gets wrong, so the partition is decided by error, not
by density or by a greedy purity score. Nothing else moves it: with the steering
switched off the regions stay exactly where initialisation put them.

Why this shape
--------------
Reliability. The gate is annealed from flat to sharp: at the first iteration the
responsibilities are almost uniform and the exact M-step collapses to plain ridge
regression (or, for classification, to multinomial logistic regression).
Specialisation grows from there, and the iterate finally kept is the *earliest*
one within a tolerance of the best held-out score -- the one-standard-error
instinct, which matters because the alternative is letting a small validation
split talk you into a wiggly model. The floor is a linear model; the upside is a
locally linear one.

Every step is closed form -- one exact normal-equation solve for regression,
bounded Newton steps (Boehning majorisation) for the classifier and for the gate
-- so there is no learning rate, no line search, and no optimiser to babysit. The
only heavy kernels are `matmul` and `linalg.solve` on dense arrays, which is
what GPUs are built for; see `prism.backend` for the NumPy/CuPy dispatch.

What is borrowed and what is not
--------------------------------
The skeleton is a mixture of experts (Jacobs et al. 1991; Jordan & Jacobs 1994)
with a linear-softmax gate, and the annealing is deterministic annealing (Rose
1998). What is not standard: the gate is refitted against responsibilities that
have been *tilted by each expert's residual* with an explicit competition
strength, while the experts themselves are always fitted against the untilted,
input-only gate -- so the model that ships never depends on a quantity that is
unavailable at prediction time. Seeding is k-means++ (Arthur & Vassilvitskii
2007); the Boehning bound is from Boehning (1992).
"""
from __future__ import annotations

import numpy as np

from . import _init
from .backend import resolve_module, solve_spd, spd_solver, to_module, to_numpy

__all__ = ["PrismRegressor", "PrismClassifier"]

_EPS = 1e-12


def _softmax(logits, xp, axis=1):
    m = xp.max(logits, axis=axis, keepdims=True)
    e = xp.exp(logits - m)
    return e / xp.maximum(e.sum(axis=axis, keepdims=True), _EPS)


def _log_softmax(logits, xp, axis=1):
    m = xp.max(logits, axis=axis, keepdims=True)
    z = logits - m
    return z - xp.log(xp.maximum(xp.exp(z).sum(axis=axis, keepdims=True), _EPS))


class _PrismBase:
    """Shared machinery. `PrismRegressor` / `PrismClassifier` add the loss."""

    _is_classifier = False
    _default_sharpness = (2.0, 30.0)

    def __init__(
        self,
        n_experts=8,
        max_iter=60,
        alpha=1e-3,
        gate_alpha=1e-2,
        sharpness_range=None,
        competition=1.0,
        competition_warmup=0.0,
        validation_fraction=0.15,
        n_iter_no_change=15,
        tol=1.0,
        newton_steps=3,
        gate_steps=3,
        chunk_size=None,
        device="auto",
        dtype="float64",
        random_state=None,
        verbose=0,
    ):
        self.n_experts = n_experts
        self.max_iter = max_iter
        self.alpha = alpha
        self.gate_alpha = gate_alpha
        self.sharpness_range = sharpness_range
        self.competition = competition
        self.competition_warmup = competition_warmup
        self.validation_fraction = validation_fraction
        self.n_iter_no_change = n_iter_no_change
        self.tol = tol
        self.newton_steps = newton_steps
        self.gate_steps = gate_steps
        self.chunk_size = chunk_size
        self.device = device
        self.dtype = dtype
        self.random_state = random_state
        self.verbose = verbose

    # ------------------------------------------------------------------ utils
    def get_params(self, deep=True):
        code = self.__init__.__code__
        return {k: getattr(self, k) for k in code.co_varnames[1:code.co_argcount]}

    def set_params(self, **params):
        for k, v in params.items():
            if not hasattr(self, k):
                raise ValueError(f"unknown parameter {k!r}")
            setattr(self, k, v)
        return self

    def _loss(self, pred, Y):
        return float(to_numpy(self._sample_losses(pred, Y).mean()))

    def _scored(self, pred, Y):
        """Mean loss and the standard error of that mean.

        The standard error is what makes model selection honest on a small
        validation split: without it, picking the best of sixty iterates on
        forty samples reliably finds noise.
        """
        ell = self._sample_losses(pred, Y)
        n = ell.shape[0]
        mean = float(to_numpy(ell.mean()))
        se = float(to_numpy(ell.std())) / np.sqrt(max(n - 1, 1))
        return mean, se

    def _row_chunks(self, n_samples, n_cols):
        """Rows per pass, so the (rows, K*D) blended design stays within budget."""
        if self.chunk_size is not None:
            step = int(self.chunk_size)
        else:
            step = max(256, 8_000_000 // max(n_cols, 1))     # ~64 MB in float64
        for start in range(0, n_samples, step):
            yield start, min(start + step, n_samples)

    def _design(self, Xs):
        """[x, 1] -- the intercept sits in the last column and is never
        penalised, in the gate or in the experts."""
        xp = self._xp
        ones = xp.ones((Xs.shape[0], 1), dtype=Xs.dtype)
        return xp.concatenate([Xs, ones], axis=1)

    # ------------------------------------------------------------------- gate
    # The gate is a linear softmax over the experts. That choice is load
    # bearing: a density-based gate (a Gaussian mixture, say) can only place
    # regions where the data happens to be dense, and cannot express a boundary
    # like "x3 > 0" that separates two linear regimes sitting inside one blob.
    # Residual steering needs a gate that can actually move where it is told.

    def _gate_logits(self, Xt):
        return Xt @ self.gate_

    def _spread(self, logits):
        """Mean gap between the best and worst expert for a sample.

        The gate is stored normalised to unit spread so that `sharpness` is in
        nats and one schedule means the same thing on any dataset.
        """
        gap = logits.max(axis=1) - logits.min(axis=1)
        return max(float(to_numpy(gap.mean())), _EPS)

    def _normalize_gate(self, G, Xt):
        return G / self._spread(Xt @ G)

    def _fit_gate(self, Xt, Q, G0):
        """Fit the gate to target responsibilities Q by bounded Newton steps.

        Boehning's bound replaces the multinomial Hessian with 0.5 * Xt^T Xt,
        which does not depend on the parameters *or* on the iteration -- so the
        factorisation is computed once per fit and reused here.
        """
        xp = self._xp
        G = G0
        for _ in range(max(1, self.gate_steps)):
            P = _softmax(Xt @ G, xp)
            grad = Xt.T @ (P - Q) + self._gate_pen * G
            G = G - self._gate_solve(grad)
        return G

    # ---------------------------------------------------------------- experts
    def _blended_design(self, Xs, R, lo, hi):
        """Z[i] = concat_k r_ik * [x_i, 1]  for rows lo:hi.

        Folding the responsibilities into the design turns the whole mixture
        into a single linear model, which is what makes the exact M-step below
        possible instead of yet another gradient loop.
        """
        Xt = self._design(Xs[lo:hi])
        return (R[lo:hi, :, None] * Xt[:, None, :]).reshape(Xt.shape[0], -1)

    def _penalty(self, A):
        """Ridge diagonal, relative to the Gram matrix's own scale.

        An absolute alpha would be meaningless here: the responsibilities scale
        the design, so at a flat gate every block of Z^T Z shrinks by ~K^2 and a
        fixed penalty would silently flatten the model. Loading each coefficient
        in proportion to its own diagonal entry is scale-free.
        """
        xp = self._xp
        pen = self.alpha * xp.maximum(xp.diagonal(A), _EPS)
        return xp.where(self._slope_mask_, pen, 0.0)

    def _gram(self, Xs, R):
        xp = self._xp
        p = self.n_experts_ * (Xs.shape[1] + 1)
        A = xp.zeros((p, p), dtype=self._dtype)
        for lo, hi in self._row_chunks(Xs.shape[0], p):
            Z = self._blended_design(Xs, R, lo, hi)
            A += Z.T @ Z
        return A

    def _cross(self, Xs, R, T):
        xp = self._xp
        p = self.n_experts_ * (Xs.shape[1] + 1)
        B = xp.zeros((p, T.shape[1]), dtype=self._dtype)
        for lo, hi in self._row_chunks(Xs.shape[0], p):
            Z = self._blended_design(Xs, R, lo, hi)
            B += Z.T @ T[lo:hi]
        return B

    def _blended_output(self, Xs, R, W):
        xp = self._xp
        out = xp.empty((Xs.shape[0], W.shape[1]), dtype=self._dtype)
        for lo, hi in self._row_chunks(Xs.shape[0], W.shape[0]):
            out[lo:hi] = self._blended_design(Xs, R, lo, hi) @ W
        return out

    def _expert_outputs(self, Xt, W):
        """Every expert's own prediction for every sample -- (n, K, n_out).

        Training only. This is what tells the gate which expert deserves which
        sample; it is never touched at prediction time.
        """
        xp = self._xp
        Wk = W.reshape(self.n_experts_, Xt.shape[1], W.shape[1])
        return xp.einsum("nd,kdo->nko", Xt, Wk)

    def _competition_penalty(self, Xt, Y):
        """Per-(sample, expert) blame, on the same scale as the gate's logits.

        Offsetting by the best expert keeps the tilt about *relative* blame: a
        sample nobody can fit should not drag the partition around. Dividing by
        the mean spread puts blame in units of gate-logit spread, which is what
        makes `competition` a dimensionless number of order one -- tilt by 1.0
        and the worst expert's blame is worth exactly as much as the whole range
        of the gate's current opinion.
        """
        xp = self._xp
        ell = self._per_expert_loss(Xt, Y)
        ell = ell - ell.min(axis=1, keepdims=True)
        spread = xp.maximum((ell.max(axis=1) - ell.min(axis=1)).mean(), _EPS)
        return ell / spread

    # -------------------------------------------------------------------- fit
    def fit(self, X, y):
        if isinstance(self.n_experts, str):
            if self.n_experts != "auto":
                raise ValueError("n_experts must be an int or 'auto'")
            return self._fit_auto(X, y)
        return self._fit_one(X, y)

    def _fit_auto(self, X, y):
        """Pick `n_experts` by the held-out score every fit already computes.

        This is the hyperparameter that matters, and it is not the usual
        capacity dial: K is a claim about how many linear regimes the data
        contains, so more is not safer. Two well-placed experts beat sixteen
        badly placed ones, and the steering term diffuses when there are far
        more regions than regimes. Searching costs a handful of fits and uses
        no test data -- `best_score_` is measured on the internal validation
        split, which is the same split for every K.
        """
        grid = [k for k in (2, 3, 4, 6, 8, 12, 16) if k <= max(2, len(X) // 10)]
        params = self.get_params()
        best = None
        for k in grid:
            cand = type(self)(**{**params, "n_experts": k})._fit_one(X, y)
            if best is None or cand.best_score_ < best.best_score_:
                best = cand
        self.__dict__.update(best.__dict__)
        self.n_experts = "auto"
        self.searched_experts_ = grid
        return self

    def _fit_one(self, X, y):
        xp = resolve_module(self.device)
        self._xp = xp
        self._dtype = np.dtype(self.dtype)

        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 2:
            raise ValueError(f"X must be 2-D, got shape {X.shape}")
        y = np.asarray(y)
        if len(y) != len(X):
            raise ValueError(f"X has {len(X)} rows but y has {len(y)}")
        if not isinstance(self.n_experts, (int, np.integer)) or self.n_experts < 1:
            raise ValueError("n_experts must be an integer >= 1, or 'auto'")

        rng = np.random.default_rng(self.random_state)
        tr_idx, va_idx = self._split(y, rng)

        self._setup_targets(y)                               # sets self._Y
        Y_all = to_module(self._Y, xp, self._dtype)

        # Standardise on the training rows only. A constant column is left as
        # zero rather than blown up by a near-zero standard deviation.
        Xd = to_module(X, xp, self._dtype)
        tr = xp.asarray(tr_idx)
        self._x_mean_ = Xd[tr].mean(axis=0)
        std = Xd[tr].std(axis=0)
        self._x_std_ = xp.where(std > 1e-12, std, 1.0)
        Xs_all = (Xd - self._x_mean_) / self._x_std_

        Xtr, Ytr = Xs_all[tr], Y_all[tr]
        has_val = len(va_idx) > 0
        if has_val:
            va = xp.asarray(va_idx)
            Xva, Yva = Xs_all[va], Y_all[va]

        n_train, n_features = Xtr.shape
        self.n_experts_ = int(min(self.n_experts, max(1, n_train // 2)))
        D = n_features + 1
        K = self.n_experts_

        Xt_tr = self._design(Xtr)
        Xt_va = self._design(Xva) if has_val else None

        mask = xp.ones((K, D), dtype=bool)
        mask[:, -1] = False
        self._slope_mask_ = mask.reshape(-1)
        self.weights_ = xp.zeros((K * D, self._n_out), dtype=self._dtype)

        # Curvature bound for the gate: constant across the whole fit, so it is
        # factored exactly once.
        XtX = Xt_tr.T @ Xt_tr
        gpen = self.gate_alpha * float(to_numpy(xp.diagonal(XtX).mean()))
        self._gate_pen = gpen
        self._gate_solve = spd_solver(0.5 * XtX + gpen * xp.eye(D, dtype=self._dtype), xp)

        # --- seed the partition ---------------------------------------------
        # k-means only breaks the symmetry: without it every expert would carry
        # the same law, every residual would be equal, and the steering term
        # would have nothing to prefer. Where the regions end up is decided by
        # the residuals afterwards, not here.
        if K > 1:
            centers = _init.lloyd(Xtr, _init.kmeans_plus_plus(Xtr, K, xp, rng), xp)
            d2 = _init._sq_dists_to(Xtr, centers, xp)
            labels = xp.argmin(d2, axis=1)
            Q0 = (labels[:, None] == xp.arange(K)).astype(self._dtype)
            Q0 = 0.9 * Q0 + 0.1 / K
            G = self._fit_gate(Xt_tr, Q0, xp.zeros((D, K), dtype=self._dtype))
            self.gate_ = self._normalize_gate(G, Xt_tr)
        else:
            self.gate_ = xp.zeros((D, 1), dtype=self._dtype)

        s_flat, s_sharp = self.sharpness_range or self._default_sharpness
        chain = []                     # every iterate that set a new best score
        stale = 0
        self.history_ = []

        # --- the floor ------------------------------------------------------
        # A zero gate means uniform responsibilities, and the exact M-step under
        # uniform responsibilities is plain ridge (or multinomial logistic)
        # regression. Scoring it first puts the linear model in the running as
        # the simplest candidate of all, so the selection rule below can fall
        # back on it whenever specialising does not clearly pay. This is a
        # cheaper and more honest floor than annealing from a flat gate: doing
        # that leaves every expert carrying the *same* law, which leaves the
        # steering term with no residual differences to work with.
        keep_gate = self.gate_
        self.gate_ = xp.zeros((D, K), dtype=self._dtype)
        R0 = _softmax(self._gate_logits(Xt_tr), xp)
        self.weights_ = self._fit_experts(Xtr, Ytr, R0, self.weights_)
        linear_loss = self._loss(self._blended_output(Xtr, R0, self.weights_), Ytr)
        if has_val:
            Rv0 = _softmax(self._gate_logits(Xt_va), xp)
            best_score, best_se = self._scored(
                self._blended_output(Xva, Rv0, self.weights_), Yva
            )
        else:
            best_score, best_se = linear_loss, 0.0
        self.history_.append({"iter": -1, "sharpness": 1.0, "beta": 0.0,
                              "train_loss": linear_loss, "score": best_score})
        chain.append((best_score, self._snapshot(1.0, -1)))
        best_all_se = best_se
        self.linear_score_ = best_score
        self.gate_ = keep_gate

        for it in range(self.max_iter):
            frac = it / max(self.max_iter - 1, 1)
            sharpness = s_flat * (s_sharp / s_flat) ** frac
            warm = float(self.competition_warmup)
            beta = self.competition * (min(1.0, frac / warm) if warm > 0 else 1.0)

            logits = self._gate_logits(Xt_tr)
            # The experts are fitted against the input-only gate -- exactly what
            # inference will see. Nothing is fitted against information that is
            # unavailable at predict time.
            R = _softmax(sharpness * logits, xp)
            self.weights_ = self._fit_experts(Xtr, Ytr, R, self.weights_)

            train_loss = self._loss(self._blended_output(Xtr, R, self.weights_), Ytr)
            if has_val:
                Rva = _softmax(sharpness * self._gate_logits(Xt_va), xp)
                score, se = self._scored(
                    self._blended_output(Xva, Rva, self.weights_), Yva
                )
            else:
                score, se = train_loss, 0.0
            self.history_.append(
                {"iter": it, "sharpness": sharpness, "beta": beta,
                 "train_loss": train_loss, "score": score}
            )
            if self.verbose:
                print(f"[prism] it={it:3d} sharp={sharpness:8.3f} beta={beta:5.2f} "
                      f"train={train_loss:.6f} score={score:.6f}")

            if score < best_score - 1e-12:
                best_score, best_all_se = score, se
                chain.append((score, self._snapshot(sharpness, it)))
                stale = 0
            else:
                stale += 1
                # The schedule is a path, not a descent. Abandoning it early
                # would leave the sharp, specialised end unexplored and quietly
                # return a linear model, so patience only bites near the end.
                if self.n_iter_no_change and stale >= self.n_iter_no_change and frac > 0.5:
                    break

            # --- the steering step -------------------------------------------
            # Tilt the responsibilities by how badly each expert does on each
            # sample, then refit the gate to *those*. This is the only thing
            # that moves a boundary: at competition=0 the target equals the
            # current gate and the refit is a fixed point.
            if K > 1 and beta > 0.0:
                Q = _softmax(
                    sharpness
                    * (logits - beta * self._competition_penalty(Xt_tr, Ytr)),
                    xp,
                )
                G = self._fit_gate(Xt_tr, Q, sharpness * self.gate_)
                self.gate_ = self._normalize_gate(G, Xt_tr)

        # The one-standard-error rule. Candidates run simplest-first -- the
        # plain linear model, then flat gates, then sharp ones -- so taking the
        # earliest candidate within `tol` standard errors of the best score buys
        # specialisation only where the data can actually prove it is worth it.
        # Only best-so-far iterates need checking: any other iterate inside the
        # threshold is dominated by an earlier one.
        threshold = best_score + self.tol * best_all_se
        self._restore(next(s for sc, s in chain if sc <= threshold))
        self.n_iter_ = len(self.history_)
        self.best_score_ = best_score
        return self

    def _snapshot(self, sharpness, it):
        return {"gate": self.gate_.copy(), "weights": self.weights_.copy(),
                "sharpness": sharpness, "iter": it}

    def _restore(self, snap):
        self.gate_ = snap["gate"]
        self.weights_ = snap["weights"]
        self.sharpness_ = snap["sharpness"]
        self.selected_iter_ = snap["iter"]

    def _split(self, y, rng):
        n = len(y)
        if not self.validation_fraction:
            return np.arange(n), np.arange(0)
        n_val = int(round(self.validation_fraction * n))
        if n_val < 1 or n - n_val < max(4, self.n_experts):
            return np.arange(n), np.arange(0)
        if self._is_classifier:
            tr, va = [], []                       # stratified: no class may vanish
            for c in np.unique(y):
                idx = np.flatnonzero(y == c)
                rng.shuffle(idx)
                k = min(int(round(self.validation_fraction * len(idx))),
                        max(len(idx) - 1, 0))
                va.append(idx[:k])
                tr.append(idx[k:])
            tr, va = np.concatenate(tr), np.concatenate(va)
            if len(va) == 0:
                return np.arange(n), np.arange(0)
            return np.sort(tr), np.sort(va)
        perm = rng.permutation(n)
        return np.sort(perm[n_val:]), np.sort(perm[:n_val])

    # ------------------------------------------------------------------ apply
    def _standardize(self, X):
        xp = self._xp
        Xd = to_module(np.asarray(X, dtype=np.float64), xp, self._dtype)
        if Xd.ndim != 2 or Xd.shape[1] != self._x_mean_.shape[0]:
            raise ValueError(
                f"expected X with {self._x_mean_.shape[0]} features, got {Xd.shape}"
            )
        return (Xd - self._x_mean_) / self._x_std_

    def _decision(self, X):
        xp = self._xp
        Xs = self._standardize(X)
        R = _softmax(self.sharpness_ * self._gate_logits(self._design(Xs)), xp)
        return self._blended_output(Xs, R, self.weights_)

    def expert_weights(self, X):
        """The gate's responsibilities for `X` -- (n_samples, n_experts).

        Rows sum to 1. Useful to see which local law a prediction came from.
        """
        xp = self._xp
        Xs = self._standardize(X)
        return to_numpy(
            _softmax(self.sharpness_ * self._gate_logits(self._design(Xs)), xp)
        )

    def local_coefficients(self, X):
        """The single linear law Prism is effectively applying at each row.

        Returns (n_samples, n_features + 1): the responsibility-weighted blend
        of the experts' coefficients, with the intercept last, in the units of
        the standardised inputs. This is the model's explanation of itself --
        there is one honest linear equation behind every prediction.
        """
        R = self.expert_weights(X)
        W = to_numpy(self.weights_).reshape(self.n_experts_, -1, self._n_out)
        return np.einsum("nk,kdo->ndo", R, W).squeeze(-1) if self._n_out == 1 \
            else np.einsum("nk,kdo->ndo", R, W)


class PrismRegressor(_PrismBase):
    """Prism for regression (single- or multi-output).

    The expert M-step here is *exact*. With the responsibilities frozen inside
    the step, the blended model is linear in the stacked weights, so the optimum
    is one ridge solve of size K*(d+1): every iteration lands on the global
    minimum of the training objective for the current partition. There is no
    descent to tune and no way for the expert fit itself to go wrong.
    """

    _is_classifier = False

    def _setup_targets(self, y):
        Y = np.asarray(y, dtype=np.float64)
        if Y.ndim == 1:
            Y = Y[:, None]
        self._y_mean_ = Y.mean(axis=0)
        std = Y.std(axis=0)
        self._y_std_ = np.where(std > 1e-12, std, 1.0)
        self._Y = (Y - self._y_mean_) / self._y_std_
        self._n_out = self._Y.shape[1]
        self._y_1d = np.asarray(y).ndim == 1

    def _fit_experts(self, Xs, Y, R, W_prev):
        xp = self._xp
        A = self._gram(Xs, R)
        A = A + xp.diag(self._penalty(A))
        return solve_spd(A, self._cross(Xs, R, Y), xp)

    def _sample_losses(self, pred, Y):
        return ((pred - Y) ** 2).mean(axis=1)

    def _per_expert_loss(self, Xt, Y):
        P = self._expert_outputs(Xt, self.weights_)          # (n, K, n_out)
        return ((P - Y[:, None, :]) ** 2).mean(axis=2)

    def predict(self, X):
        out = to_numpy(self._decision(X)) * self._y_std_ + self._y_mean_
        return out[:, 0] if self._y_1d else out

    def score(self, X, y):
        """R^2, uniformly averaged over outputs."""
        y = np.asarray(y, dtype=np.float64)
        pred = np.asarray(self.predict(X), dtype=np.float64)
        if y.ndim == 1:
            y, pred = y[:, None], pred.reshape(-1, 1)
        ss_res = ((y - pred) ** 2).sum(axis=0)
        ss_tot = ((y - y.mean(axis=0)) ** 2).sum(axis=0)
        return float(np.mean(1.0 - ss_res / np.maximum(ss_tot, _EPS)))


class PrismClassifier(_PrismBase):
    """Prism for classification (binary or multiclass).

    Blended logits are not linear in the loss, so the M-step takes bounded
    Newton steps instead: Boehning's quadratic bound replaces the true Hessian
    with 0.5 * Z^T Z, a constant matrix, giving a guaranteed-descent update with
    no step size to choose and one factorisation reused across classes. A
    halving guard catches the rare case where the blocks overshoot each other.
    """

    _is_classifier = True
    # Cross-entropy rewards confident local boundaries more than squared error
    # does, so the classifier is allowed to sharpen further.
    _default_sharpness = (5.0, 50.0)

    def _setup_targets(self, y):
        y = np.asarray(y)
        self.classes_, enc = np.unique(y, return_inverse=True)
        self._n_out = len(self.classes_)
        if self._n_out < 2:
            raise ValueError("classification needs at least 2 classes")
        Y = np.zeros((len(y), self._n_out), dtype=np.float64)
        Y[np.arange(len(y)), enc] = 1.0
        self._Y = Y

    def _fit_experts(self, Xs, Y, R, W_prev):
        xp = self._xp
        A = self._gram(Xs, R)
        pen = self._penalty(A)
        S = 0.5 * A + xp.diag(pen)                           # Boehning majoriser
        W = W_prev
        loss = self._loss(self._blended_output(Xs, R, W), Y)
        for _ in range(max(1, self.newton_steps)):
            P = _softmax(self._blended_output(Xs, R, W), xp)
            step = solve_spd(S, self._cross(Xs, R, P - Y) + pen[:, None] * W, xp)
            scale = 1.0
            for _ in range(6):                               # monotonicity guard
                cand = W - scale * step
                cand_loss = self._loss(self._blended_output(Xs, R, cand), Y)
                if cand_loss <= loss + 1e-12:
                    break
                scale *= 0.5
            else:
                break
            W, loss = cand, cand_loss
        return W

    def _sample_losses(self, logits, Y):
        return -(Y * _log_softmax(logits, self._xp)).sum(axis=1)

    def _per_expert_loss(self, Xt, Y):
        xp = self._xp
        Z = self._expert_outputs(Xt, self.weights_)          # (n, K, n_classes)
        return -(Y[:, None, :] * _log_softmax(Z, xp, axis=2)).sum(axis=2)

    def predict_proba(self, X):
        return to_numpy(_softmax(self._decision(X), self._xp))

    def predict_log_proba(self, X):
        return to_numpy(_log_softmax(self._decision(X), self._xp))

    def predict(self, X):
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]

    def score(self, X, y):
        """Mean accuracy."""
        return float(np.mean(self.predict(X) == np.asarray(y)))

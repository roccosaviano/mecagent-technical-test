"""Seeding of the expert centroids (k-means++ followed by a few Lloyd steps).

Randomness stays on the host: we only ever sample small index sets, and doing
that with a NumPy Generator keeps results reproducible and identical whether the
data itself sits on CPU or GPU.
"""
from __future__ import annotations

import numpy as np

from .backend import to_numpy


def _sq_dists_to(X, centers, xp):
    """Squared euclidean distances, (n, m), via the expanded form (3 matmuls)."""
    x2 = (X * X).sum(axis=1)[:, None]
    c2 = (centers * centers).sum(axis=1)[None, :]
    d2 = x2 + c2 - 2.0 * (X @ centers.T)
    return xp.maximum(d2, 0.0)


def kmeans_plus_plus(X, n_clusters, xp, rng, n_local_trials=None):
    """Standard k-means++ seeding (Arthur & Vassilvitskii, 2007)."""
    n_samples, n_features = X.shape
    if n_local_trials is None:
        n_local_trials = 2 + int(np.log(n_clusters))

    centers = xp.empty((n_clusters, n_features), dtype=X.dtype)
    first = int(rng.integers(n_samples))
    centers[0] = X[first]

    closest = _sq_dists_to(X, centers[0:1], xp)[:, 0]
    current_pot = float(to_numpy(closest.sum()))

    for c in range(1, n_clusters):
        # Sample candidates proportionally to their distance to the current set,
        # then keep the one that shrinks the potential the most.
        probs = to_numpy(closest)
        total = probs.sum()
        if not np.isfinite(total) or total <= 0:
            cand_ids = rng.integers(n_samples, size=n_local_trials)
        else:
            rand_vals = rng.random(n_local_trials) * total
            cand_ids = np.searchsorted(np.cumsum(probs), rand_vals)
            cand_ids = np.clip(cand_ids, 0, n_samples - 1)

        cand_dists = _sq_dists_to(X, X[xp.asarray(cand_ids)], xp)
        cand_dists = xp.minimum(cand_dists, closest[:, None])
        pots = to_numpy(cand_dists.sum(axis=0))
        best = int(np.argmin(pots))

        centers[c] = X[int(cand_ids[best])]
        closest = cand_dists[:, best]
        current_pot = float(pots[best])

    return centers


def lloyd(X, centers, xp, n_iter=10, tol=1e-6):
    """A few Lloyd iterations to tidy up the seeding. Empty clusters are
    re-seeded on the worst-explained point rather than left to collapse."""
    n_clusters = centers.shape[0]
    for _ in range(n_iter):
        d2 = _sq_dists_to(X, centers, xp)
        labels = xp.argmin(d2, axis=1)
        onehot = (labels[:, None] == xp.arange(n_clusters)).astype(X.dtype)
        counts = onehot.sum(axis=0)
        sums = onehot.T @ X
        empty = counts < 0.5
        safe = xp.maximum(counts, 1.0)[:, None]
        new_centers = sums / safe
        if bool(to_numpy(empty.any())):
            worst = xp.argsort(-xp.min(d2, axis=1))[:n_clusters]
            empty_idx = xp.nonzero(empty)[0]
            new_centers[empty_idx] = X[worst[: empty_idx.shape[0]]]
        shift = float(to_numpy(((new_centers - centers) ** 2).sum()))
        centers = new_centers
        if shift < tol:
            break
    return centers

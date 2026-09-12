"""Array-module dispatch so the same code runs on NumPy (CPU) or CuPy (GPU).

The whole estimator is written with ops that NumPy and CuPy spell identically
(matmul, einsum, reductions, linalg.solve/cholesky), so there is no per-backend
code path to maintain -- only the question of which module owns the arrays.
"""
from __future__ import annotations

import numpy as np

_CUPY = None
_CUPY_CHECKED = False


def cupy_module():
    """Return the cupy module, or None if it is not importable/usable."""
    global _CUPY, _CUPY_CHECKED
    if not _CUPY_CHECKED:
        _CUPY_CHECKED = True
        try:
            import cupy as cp  # type: ignore

            # An installed cupy with no visible device is worse than no cupy at
            # all: it imports fine and then throws on the first allocation.
            cp.zeros(1)
            _CUPY = cp
        except Exception:
            _CUPY = None
    return _CUPY


def gpu_available() -> bool:
    return cupy_module() is not None


def array_module(*arrays):
    """Return the module that owns `arrays` (cupy if any of them lives there)."""
    cp = cupy_module()
    if cp is not None:
        for a in arrays:
            if isinstance(a, cp.ndarray):
                return cp
    return np


def resolve_module(device: str):
    """Map a user-facing device string to an array module.

    'auto' -> cupy when a device is actually usable, numpy otherwise.
    """
    if device == "cpu":
        return np
    if device == "gpu":
        cp = cupy_module()
        if cp is None:
            raise RuntimeError(
                "device='gpu' requires CuPy and a visible CUDA device. "
                "Install e.g. `cupy-cuda12x`, or use device='auto'."
            )
        return cp
    if device == "auto":
        cp = cupy_module()
        return cp if cp is not None else np
    raise ValueError(f"device must be 'auto', 'cpu' or 'gpu', got {device!r}")


def to_module(a, xp, dtype=None):
    """Move/convert an array into module `xp`."""
    if dtype is None:
        dtype = getattr(a, "dtype", None)
        if dtype is None or not np.issubdtype(np.dtype(dtype), np.floating):
            dtype = np.float64
    if xp is np:
        return np.asarray(to_numpy(a), dtype=dtype)
    return xp.asarray(to_numpy(a), dtype=dtype)


def to_numpy(a):
    """Bring an array back to host memory as a NumPy array."""
    cp = cupy_module()
    if cp is not None and isinstance(a, cp.ndarray):
        return cp.asnumpy(a)
    return np.asarray(a)


def solve_spd(A, b, xp, jitter=1e-10):
    """Solve A x = b for symmetric positive definite A, with jitter retries.

    Ill-conditioning shows up here as a failed Cholesky rather than silently
    wrong weights, so we escalate the diagonal loading instead of hiding it.
    """
    n = A.shape[-1]
    eye = xp.eye(n, dtype=A.dtype)
    scale = float(to_numpy(xp.abs(xp.diagonal(A)).max())) or 1.0
    for k in range(6):
        try:
            L = xp.linalg.cholesky(A + (jitter * (10.0 ** k) * scale) * eye)
            y = xp.linalg.solve(L, b)
            return xp.linalg.solve(L.T, y)
        except Exception:
            continue
    return xp.linalg.lstsq(A, b, rcond=None)[0]


def spd_solver(A, xp, jitter=1e-8):
    """Factor a symmetric positive definite A once, return a reusable solver.

    The gate is refitted at every iteration against the same design matrix, so
    its curvature bound never changes: factoring once and reusing turns each
    gate update into two triangular solves.
    """
    n = A.shape[-1]
    eye = xp.eye(n, dtype=A.dtype)
    scale = float(to_numpy(xp.abs(xp.diagonal(A)).max())) or 1.0
    L = None
    for k in range(6):
        try:
            L = xp.linalg.cholesky(A + (jitter * (10.0 ** k) * scale) * eye)
            break
        except Exception:
            continue
    if L is None:
        Ainv = xp.linalg.pinv(A)
        return lambda b: Ainv @ b

    def solve(b):
        return xp.linalg.solve(L.T, xp.linalg.solve(L, b))

    return solve

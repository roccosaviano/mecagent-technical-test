"""Prism -- residual-steered mixtures of local linear experts.

A learner whose logic is neither recursive partitioning nor backpropagation:
the input space is covered by soft, overlapping regions, each carrying its own
linear law, and the regions are *moved by the residuals* of the laws they carry.
Runs unchanged on NumPy or CuPy.

    from prism import PrismRegressor, PrismClassifier

    model = PrismClassifier(n_experts=12, device="auto").fit(X_train, y_train)
    model.score(X_test, y_test)

See `prism/README.md` for the derivation and `benchmarks/bench_prism.py` for how
it stacks up against the usual baselines.
"""
from .backend import gpu_available
from .core import PrismClassifier, PrismRegressor

__all__ = ["PrismClassifier", "PrismRegressor", "gpu_available"]
__version__ = "0.1.0"

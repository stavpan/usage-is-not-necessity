"""The multilinear object, done with a multilinear method.

A development x outcome matrix is a *collapse* of a development x outcome x era
tensor, and the collapse is lossy in a specific way: it forces every
development to have the same outcome profile in every era. The correct object
is the tensor and the correct decomposition is Tucker / HOSVD (Tucker 1966;
De Lathauwer et al. 2000), via TensorLy (Kossaifi et al. 2019).

The reported statistic is the share of core energy off the diagonal ``a = b = c``
-- the part that no matrix decomposition can represent -- and it is reported
against an era-shuffled null, because a uniform-chance baseline is not a null.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from tensorly.decomposition import tucker


@dataclass
class TuckerResult:
    core: np.ndarray
    factors: list[np.ndarray]
    ranks: tuple[int, ...]
    reconstruction_error: float
    energy_retained: float


def tucker_decomposition(tensor: np.ndarray, ranks: tuple[int, ...]) -> TuckerResult:
    """Tucker decomposition with HOSVD initialisation and ALS refinement."""
    tensor = np.asarray(tensor, dtype=float)
    total = float((tensor**2).sum())
    core, factors = tucker(tensor, rank=list(ranks), init="svd", tol=1e-8, n_iter_max=200)
    reconstructed = reconstruct(core, factors)
    residual = float(((tensor - reconstructed) ** 2).sum())
    return TuckerResult(
        core=np.asarray(core),
        factors=[np.asarray(f) for f in factors],
        ranks=tuple(int(r) for r in ranks),
        reconstruction_error=residual,
        energy_retained=float(1.0 - residual / total) if total > 0 else 0.0,
    )


def reconstruct(core: np.ndarray, factors: list[np.ndarray]) -> np.ndarray:
    """Rebuild the tensor from a Tucker core and factors.

    Written as one explicit ``einsum`` rather than a chain of ``tensordot`` calls
    or a library helper: the identity ``T = G x1 F1 x2 F2 x3 F3`` is then legible
    in the code, and it cannot silently disagree with TensorLy's conventions
    across versions. (A sequential ``tensordot`` loop was tried first and
    produced a shape mismatch, because each contraction appends the factor axis
    at the end rather than in place.)
    """
    letters = "abcdefghijklmnopqrstuvwxyz"
    core_subscript = letters[: core.ndim]
    output_subscript = letters[core.ndim : core.ndim + len(factors)]
    if len(output_subscript) != len(factors):
        raise ValueError("too many modes for the einsum subscript table")
    subscripts = [core_subscript]
    for mode, factor in enumerate(factors):
        if factor.shape[1] != core.shape[mode]:
            raise ValueError(
                f"factor {mode} has {factor.shape[1]} columns but core mode "
                f"{mode} has length {core.shape[mode]}"
            )
        subscripts.append(output_subscript[mode] + core_subscript[mode])
    expression = ",".join(subscripts) + "->" + output_subscript
    return np.einsum(expression, core, *factors, optimize=True)


def rank_sweep(tensor: np.ndarray, max_rank: int = 3) -> list[tuple[tuple[int, int, int], float]]:
    """Reconstruction error for every rank combination up to ``max_rank``.

    Reported rather than chosen: with 6 era levels the third mode's rank is
    capped at 6, and with a sparse tensor the error curve is usually monotone,
    so the honest output is the curve plus the selected rank and why.
    """
    results: list[tuple[tuple[int, int, int], float]] = []
    for r1 in range(1, max_rank + 1):
        for r2 in range(1, max_rank + 1):
            for r3 in range(1, max_rank + 1):
                outcome = tucker_decomposition(tensor, (r1, r2, r3))
                results.append(((r1, r2, r3), outcome.reconstruction_error))
    return sorted(results, key=lambda item: item[1])


def interaction_share(core: np.ndarray) -> float:
    """Share of core energy that is NOT on the diagonal a = b = c.

    The diagonal is the "no interaction" part: a development hits the same
    outcome modes in every era. Everything else is era-specific coupling, which
    is exactly what collapsing the tensor to a matrix destroys.
    """
    core = np.asarray(core, dtype=float)
    total = float((core**2).sum())
    if total == 0:
        return 0.0
    diagonal = 0.0
    for index in range(min(core.shape)):
        diagonal += float(core[index, index, index] ** 2)
    return float(1.0 - diagonal / total)


def era_shuffle_null(
    tensor: np.ndarray,
    rng: np.random.Generator,
    ranks: tuple[int, ...],
    n_iter: int = 100,
) -> np.ndarray:
    """Null distribution of the interaction share under shuffled era labels.

    Shuffling which era each development belongs to preserves the matrix and the
    era marginals while destroying any real era structure. This is the null that
    the first draft's uniform-chance baseline was standing in for -- and, as it
    turned out, the uniform baseline is far too generous.
    """
    tensor = np.asarray(tensor, dtype=float)
    n_dev, _, n_era = tensor.shape
    shares = np.empty(n_iter)
    for iteration in range(n_iter):
        permuted = np.zeros_like(tensor)
        for i in range(n_dev):
            source = int(np.argmax(tensor[i, :, :].sum(axis=0)))
            target = int(rng.integers(n_era))
            permuted[i, :, target] = tensor[i, :, source]
        result = tucker_decomposition(permuted, ranks)
        shares[iteration] = interaction_share(result.core)
    return shares

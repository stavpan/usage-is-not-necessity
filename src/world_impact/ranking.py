"""Ranking under uncertainty: Pareto dominance first, SMAA second.

Two decisions, forced by the literature rather than by taste:

1. **Arrow (1951), Sen (1970)**: no aggregate ordering satisfies a short list of
   reasonable axioms. So we report the set of *undominated* developments --
   which requires no weights at all -- before reporting any ordering.
2. **Lahdelma, Hokkanen & Salminen (1998)**: when weights are genuinely
   unknown, the honest object is a distribution over orderings. The rank
   acceptability index is the probability that a development occupies each
   rank across the space of legitimate weight vectors; the central weight
   vector says *which* weighting would make it first, which is often the more
   useful output than the rank itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def pareto_frontier(objectives: dict[str, np.ndarray]) -> np.ndarray:
    """Boolean mask of developments not dominated on any listed objective.

    All objectives are "larger is better". This is the only ranking statement
    that needs no normative input, which is why it comes first.
    """
    stack = np.column_stack([np.asarray(v, dtype=float) for v in objectives.values()])
    n = stack.shape[0]
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        dominated = (stack >= stack[i]).all(axis=1) & (stack > stack[i]).any(axis=1)
        if dominated.any():
            keep[i] = False
    return keep


def roc_weights(k: int) -> np.ndarray:
    """Rank-order centroid weights (Barron & Barrett 1996).

    The centroid of the simplex restricted to weight vectors consistent with a
    declared rank order of criteria: the *elicited* alternative to the uniform
    Dirichlet, used to show how much the answer moves between an agnostic and a
    ranked-priorities stance.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    return np.array([(1.0 / k) * sum(1.0 / j for j in range(i + 1, k + 1)) for i in range(k)])


@dataclass
class SmaaResult:
    """Rank acceptability, central weights and confidence, as arrays."""

    rank_acceptability: np.ndarray
    acceptance: np.ndarray
    mean_rank: np.ndarray
    rank_sd: np.ndarray
    central_weights: np.ndarray
    central_weight_draws: np.ndarray
    confidence: np.ndarray
    n_draws: int

    def top_by_acceptance(self, k: int = 10) -> list[int]:
        return [int(i) for i in np.argsort(-self.acceptance)[:k]]

    def best_rank_interval(self, index: int, mass: float = 0.9) -> tuple[int, int]:
        """Narrowest rank interval containing ``mass`` of the probability."""
        distribution = self.rank_acceptability[index]
        best: tuple[int, int] = (1, int(distribution.size))
        span = int(distribution.size)
        for start in range(distribution.size):
            total = 0.0
            for end in range(start, distribution.size):
                total += float(distribution[end])
                if total >= mass and (end - start) < span:
                    best, span = (start + 1, end + 1), end - start
                    break
        return best


MatrixOrDraws = np.ndarray | list[np.ndarray]


def _as_draws(matrices: MatrixOrDraws) -> list[np.ndarray]:
    if isinstance(matrices, list):
        return [np.asarray(m, dtype=float) for m in matrices]
    return [np.asarray(matrices, dtype=float)]


def smaa(
    matrices: MatrixOrDraws,
    rng: np.random.Generator,
    n_draws: int = 20000,
    weight_alpha: float = 1.0,
    confidence_kappa: float = 50.0,
    local_draws: int = 300,
) -> SmaaResult:
    """SMAA over weight uncertainty and optionally value uncertainty.

    Parameters
    ----------
    matrices
        One ``(n_dev, n_out)`` matrix, or a list of them representing draws from
        the measurement model. A list performs SMAA over *both* weight and value
        uncertainty, which is the version worth reporting.
    weight_alpha
        Dirichlet concentration over outcomes. ``1.0`` is uniform over the
        simplex: total agnosticism about which outcome matters.
    confidence_kappa
        Concentration of the local Dirichlet used for the confidence factor. The
        confidence factor is defined here as the probability that a development
        ranks first when weights are drawn from a local Dirichlet centred on its
        own central weight vector -- "if you weight outcomes the way that would
        favour it, how safely does it win?". The literature uses several
        definitions, so this one is stated rather than implied.
    """
    draws = _as_draws(matrices)
    n_dev, n_out = draws[0].shape

    rank_counts = np.zeros((n_dev, n_dev))
    weight_sums = np.zeros((n_dev, n_out))
    weight_counts = np.zeros(n_dev)
    rank_sum = np.zeros(n_dev)
    rank_square_sum = np.zeros(n_dev)

    for _ in range(n_draws):
        weights = rng.dirichlet(np.full(n_out, weight_alpha))
        matrix = draws[int(rng.integers(len(draws)))]
        scores = matrix @ weights
        order = np.argsort(-scores, kind="stable")
        ranks = np.empty(n_dev, dtype=int)
        ranks[order] = np.arange(1, n_dev + 1)
        for rank, index in enumerate(order):
            rank_counts[index, rank] += 1
        rank_sum += ranks
        rank_square_sum += ranks**2
        winner = int(order[0])
        weight_sums[winner] += weights
        weight_counts[winner] += 1

    rank_acceptability = rank_counts / n_draws
    mean_rank = rank_sum / n_draws
    rank_sd = np.sqrt(np.maximum(rank_square_sum / n_draws - mean_rank**2, 0.0))
    central_weights = weight_sums / np.maximum(weight_counts[:, None], 1.0)

    confidence = np.zeros(n_dev)
    for index in range(n_dev):
        if weight_counts[index] == 0:
            continue
        alpha = np.maximum(central_weights[index] * confidence_kappa, 1e-6)
        wins = 0
        for _ in range(local_draws):
            weights = rng.dirichlet(alpha)
            matrix = draws[int(rng.integers(len(draws)))]
            if int(np.argmax(matrix @ weights)) == index:
                wins += 1
        confidence[index] = wins / local_draws

    return SmaaResult(
        rank_acceptability=rank_acceptability,
        acceptance=rank_acceptability[:, 0].copy(),
        mean_rank=mean_rank,
        rank_sd=rank_sd,
        central_weights=central_weights,
        central_weight_draws=weight_counts,
        confidence=confidence,
        n_draws=n_draws,
    )


def pairwise_dominance(
    matrices: MatrixOrDraws,
    rng: np.random.Generator,
    n_draws: int = 5000,
    weight_alpha: float = 1.0,
) -> np.ndarray:
    """P(i outranks j) under uniform weight uncertainty. Antisymmetric."""
    draws = _as_draws(matrices)
    n_dev, n_out = draws[0].shape
    counts = np.zeros((n_dev, n_dev))
    for _ in range(n_draws):
        weights = rng.dirichlet(np.full(n_out, weight_alpha))
        matrix = draws[int(rng.integers(len(draws)))]
        scores = matrix @ weights
        counts += (scores[:, None] > scores[None, :]).astype(float)
    return counts / n_draws

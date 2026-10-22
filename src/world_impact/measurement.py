"""The measurement model: ordinal codes -> a latent scale with uncertainty.

Treating the 0-3 rubric as a ratio scale is the mistake that produced a flat
"impact per development" column in the first draft. The correct treatment is a
graded response model (Samejima 1969), with outcome domains as items and
developments as respondents on a unidimensional "general magnitude of impact"
trait. Two things fall out:

* an EAP estimate of theta per development **with a posterior SD**, so every
  downstream ranking can propagate measurement uncertainty;
* a **test information function**: with four categories per item the
  instrument's information eventually falls, so top-end differences are
  unresolvable. That is a property of the rubric, demonstrable, and it is why
  no acceleration claim is made in this repository.

Estimation is marginal maximum likelihood with Gauss-Hermite quadrature in
numpy/scipy, so the numbers are auditable rather than delegated.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.hermite_e import hermegauss
from scipy.optimize import minimize

from world_impact.grm import (
    category_derivative,
    category_probabilities,
    unpack_parameters,
)


@dataclass
class GradedResponseFit:
    discrimination: np.ndarray
    thresholds: np.ndarray
    log_likelihood: float
    n_parameters: int
    theta: np.ndarray
    theta_sd: np.ndarray
    quadrature: np.ndarray
    quadrature_weights: np.ndarray
    n_categories: int
    converged: bool

    def item_information(self, item: int, theta: np.ndarray) -> np.ndarray:
        """Fisher information of one item at each theta."""
        probabilities = category_probabilities(
            self.discrimination[item], self.thresholds[item], theta, self.n_categories
        )
        derivative = category_derivative(
            self.discrimination[item], self.thresholds[item], theta, self.n_categories
        )
        return np.sum(derivative**2 / probabilities, axis=0)

    def test_information(self, theta: np.ndarray) -> np.ndarray:
        """Sum of item informations: the instrument's resolving power."""
        return np.sum(
            np.stack([self.item_information(j, theta) for j in range(self.discrimination.size)]),
            axis=0,
        )

    def top_theta(self, quantile: float = 0.9) -> float:
        """Theta at which the top ``quantile`` of developments sit."""
        return float(np.quantile(self.theta, quantile))


def fit_graded_response(
    matrix: np.ndarray,
    n_quadrature: int = 41,
    max_iterations: int = 400,
    seed: int = 0,
) -> GradedResponseFit:
    """Fit a graded response model by marginal maximum likelihood.

    ``matrix`` is (n_persons, n_items) of non-negative integer categories
    starting at 0.
    """
    data = np.asarray(matrix, dtype=int)
    n_persons, n_items = data.shape
    n_categories = int(data.max()) + 1

    nodes, weights = hermegauss(n_quadrature)
    quadrature = nodes * np.sqrt(2.0)
    quadrature_weights = weights / np.sqrt(np.pi)

    def person_likelihood(parameters: np.ndarray) -> np.ndarray:
        """(n_persons, n_quadrature) likelihood of each response pattern.

        Vectorised over persons: the naive per-person, per-item loop is 864
        numpy calls per objective evaluation, which makes a 73-parameter
        numerical gradient unusable. Selecting ``P[j][data[:, j], :]`` does the
        same work in 18 calls.
        """
        discrimination, thresholds = unpack_parameters(parameters, n_items, n_categories)
        likelihood = np.ones((n_persons, quadrature.size))
        for j in range(n_items):
            probabilities = category_probabilities(
                discrimination[j], thresholds[j], quadrature, n_categories
            )
            likelihood *= probabilities[data[:, j], :]
        return likelihood

    def negative_log_likelihood(parameters: np.ndarray) -> float:
        likelihood = person_likelihood(parameters)
        marginal = likelihood @ quadrature_weights
        return float(-np.log(np.maximum(marginal, 1e-300)).sum())

    rng = np.random.default_rng(seed)
    block = n_categories
    start = np.zeros(n_items * block)
    start[1::block] = -0.5
    start[2::block] = np.log(0.5)
    start[3::block] = np.log(0.5)
    start = start + rng.normal(scale=0.05, size=start.size)

    result = minimize(
        negative_log_likelihood,
        start,
        method="L-BFGS-B",
        options={"maxiter": max_iterations, "maxfun": 40000},
    )
    discrimination, thresholds = unpack_parameters(result.x, n_items, n_categories)

    posterior = person_likelihood(result.x) * quadrature_weights
    posterior = posterior / np.maximum(posterior.sum(axis=1, keepdims=True), 1e-300)
    theta = posterior @ quadrature
    mean_square = posterior @ (quadrature**2)
    theta_sd = np.sqrt(np.maximum(mean_square - theta**2, 0.0))

    return GradedResponseFit(
        discrimination=discrimination,
        thresholds=thresholds,
        log_likelihood=float(-result.fun),
        n_parameters=int(result.x.size),
        theta=theta,
        theta_sd=theta_sd,
        quadrature=quadrature,
        quadrature_weights=quadrature_weights,
        n_categories=n_categories,
        converged=bool(result.success),
    )

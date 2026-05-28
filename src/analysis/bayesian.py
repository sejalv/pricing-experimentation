from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class BetaBinomialResult:
    control_posterior_mean: float
    treatment_posterior_mean: float
    prob_treatment_better: float
    credible_interval_lower: float  # 95% CI on treatment CR
    credible_interval_upper: float
    expected_loss: float            # Bayesian regret if we ship treatment


def beta_binomial_posterior(
    control_conversions: int,
    control_n: int,
    treatment_conversions: int,
    treatment_n: int,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    n_samples: int = 100_000,
) -> BetaBinomialResult:
    """
    Bayesian A/B test using Beta-Binomial conjugate model.

    Prior: Beta(alpha, beta) — defaults to uniform (no strong prior).
    Posterior: Beta(alpha + conversions, beta + non-conversions).
    """
    rng = np.random.default_rng(42)

    post_alpha_c = prior_alpha + control_conversions
    post_beta_c = prior_beta + (control_n - control_conversions)
    post_alpha_t = prior_alpha + treatment_conversions
    post_beta_t = prior_beta + (treatment_n - treatment_conversions)

    samples_c = rng.beta(post_alpha_c, post_beta_c, size=n_samples)
    samples_t = rng.beta(post_alpha_t, post_beta_t, size=n_samples)

    prob_treatment_better = float((samples_t > samples_c).mean())
    expected_loss = float(np.maximum(samples_c - samples_t, 0).mean())

    post_mean_c = post_alpha_c / (post_alpha_c + post_beta_c)
    post_mean_t = post_alpha_t / (post_alpha_t + post_beta_t)
    ci_lower, ci_upper = float(np.percentile(samples_t, 2.5)), float(np.percentile(samples_t, 97.5))

    return BetaBinomialResult(
        control_posterior_mean=round(post_mean_c, 4),
        treatment_posterior_mean=round(post_mean_t, 4),
        prob_treatment_better=round(prob_treatment_better, 4),
        credible_interval_lower=round(ci_lower, 4),
        credible_interval_upper=round(ci_upper, 4),
        expected_loss=round(expected_loss, 6),
    )


def credible_interval(alpha: float, beta: float, level: float = 0.95) -> tuple[float, float]:
    """HDI (highest density interval) for a Beta posterior."""
    lower = stats.beta.ppf((1 - level) / 2, alpha, beta)
    upper = stats.beta.ppf(1 - (1 - level) / 2, alpha, beta)
    return round(float(lower), 4), round(float(upper), 4)

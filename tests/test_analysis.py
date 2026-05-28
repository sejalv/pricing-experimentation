import pytest
import numpy as np

from src.analysis.frequentist import (
    minimum_detectable_effect,
    required_sample_size,
    t_test_revenue,
    z_test_proportions,
)
from src.analysis.bayesian import beta_binomial_posterior, credible_interval


# --- Frequentist tests ---

def test_z_test_detects_lift():
    result = z_test_proportions(
        control_conversions=400, control_n=5000,
        treatment_conversions=460, treatment_n=5000,
    )
    assert result.p_value < 0.05
    assert result.significant
    assert result.treatment_cr > result.control_cr


def test_z_test_no_effect():
    result = z_test_proportions(
        control_conversions=400, control_n=5000,
        treatment_conversions=405, treatment_n=5000,
    )
    assert not result.significant
    assert result.p_value > 0.05


def test_z_test_ci_contains_zero_when_null():
    result = z_test_proportions(
        control_conversions=500, control_n=5000,
        treatment_conversions=502, treatment_n=5000,
    )
    assert result.ci_lower < 0 < result.ci_upper


def test_t_test_revenue_detects_difference():
    rng = np.random.default_rng(0)
    control = list(rng.normal(120, 20, 400))
    treatment = list(rng.normal(150, 25, 460))
    result = t_test_revenue(control, treatment)
    assert result.significant
    assert result.treatment_mean > result.control_mean


def test_mde_decreases_with_sample_size():
    mde_small = minimum_detectable_effect(0.08, 1000)
    mde_large = minimum_detectable_effect(0.08, 10000)
    assert mde_small > mde_large


def test_required_sample_size_is_positive():
    n = required_sample_size(baseline_cr=0.08, mde=0.01)
    assert n > 0


def test_sample_size_increases_with_smaller_mde():
    n_large_mde = required_sample_size(0.08, 0.02)
    n_small_mde = required_sample_size(0.08, 0.01)
    assert n_small_mde > n_large_mde


# --- Bayesian tests ---

def test_bayesian_detects_treatment_better():
    result = beta_binomial_posterior(
        control_conversions=400, control_n=5000,
        treatment_conversions=460, treatment_n=5000,
    )
    assert result.prob_treatment_better > 0.95
    assert result.treatment_posterior_mean > result.control_posterior_mean


def test_bayesian_null_effect_near_fifty_fifty():
    result = beta_binomial_posterior(
        control_conversions=400, control_n=5000,
        treatment_conversions=400, treatment_n=5000,
    )
    # Should be close to 50/50 when there's no effect
    assert 0.35 < result.prob_treatment_better < 0.65


def test_credible_interval_ordering():
    lower, upper = credible_interval(alpha=10, beta=90)
    assert lower < upper
    assert 0 < lower < upper < 1

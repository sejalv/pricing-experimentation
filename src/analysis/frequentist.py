from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class ProportionTestResult:
    control_cr: float
    treatment_cr: float
    absolute_lift: float
    relative_lift: float
    z_statistic: float
    p_value: float
    ci_lower: float
    ci_upper: float
    significant: bool


@dataclass
class RevenueTestResult:
    control_mean: float
    treatment_mean: float
    absolute_lift: float
    relative_lift: float
    t_statistic: float
    p_value: float
    ci_lower: float
    ci_upper: float
    significant: bool


def z_test_proportions(
    control_conversions: int,
    control_n: int,
    treatment_conversions: int,
    treatment_n: int,
    alpha: float = 0.05,
) -> ProportionTestResult:
    """Two-proportion z-test for conversion rate lift."""
    p_c = control_conversions / control_n
    p_t = treatment_conversions / treatment_n
    p_pool = (control_conversions + treatment_conversions) / (control_n + treatment_n)

    se = np.sqrt(p_pool * (1 - p_pool) * (1 / control_n + 1 / treatment_n))
    z = (p_t - p_c) / se if se > 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    # 95% CI on the difference
    se_diff = np.sqrt(p_c * (1 - p_c) / control_n + p_t * (1 - p_t) / treatment_n)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    diff = p_t - p_c
    ci_lower = diff - z_crit * se_diff
    ci_upper = diff + z_crit * se_diff

    return ProportionTestResult(
        control_cr=round(p_c, 4),
        treatment_cr=round(p_t, 4),
        absolute_lift=round(diff, 4),
        relative_lift=round(diff / p_c if p_c > 0 else 0.0, 4),
        z_statistic=round(z, 4),
        p_value=round(p_value, 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
        significant=p_value < alpha,
    )


def t_test_revenue(
    control_revenues: list[float],
    treatment_revenues: list[float],
    alpha: float = 0.05,
) -> RevenueTestResult:
    """Welch's t-test for average revenue per converted user."""
    c = np.array(control_revenues)
    t = np.array(treatment_revenues)
    t_stat, p_value = stats.ttest_ind(t, c, equal_var=False)

    mean_c = float(c.mean())
    mean_t = float(t.mean())
    diff = mean_t - mean_c

    # 95% CI on difference via bootstrapping (n_bootstrap=1000 is fast enough)
    rng = np.random.default_rng(42)
    boot_diffs = []
    for _ in range(1000):
        bc = rng.choice(c, size=len(c), replace=True)
        bt = rng.choice(t, size=len(t), replace=True)
        boot_diffs.append(bt.mean() - bc.mean())
    ci_lower, ci_upper = float(np.percentile(boot_diffs, 2.5)), float(np.percentile(boot_diffs, 97.5))

    return RevenueTestResult(
        control_mean=round(mean_c, 4),
        treatment_mean=round(mean_t, 4),
        absolute_lift=round(diff, 4),
        relative_lift=round(diff / mean_c if mean_c > 0 else 0.0, 4),
        t_statistic=round(float(t_stat), 4),
        p_value=round(float(p_value), 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
        significant=float(p_value) < alpha,
    )


def minimum_detectable_effect(
    baseline_cr: float,
    n_per_variant: int,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """MDE for a proportion test given the current sample size."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    se = np.sqrt(2 * baseline_cr * (1 - baseline_cr) / n_per_variant)
    return float((z_alpha + z_beta) * se)


def required_sample_size(
    baseline_cr: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Sample size per variant to detect a given absolute MDE."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    p2 = baseline_cr + mde
    n = (z_alpha + z_beta) ** 2 * (baseline_cr * (1 - baseline_cr) + p2 * (1 - p2)) / (mde ** 2)
    return int(np.ceil(n))

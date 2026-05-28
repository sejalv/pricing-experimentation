import pytest
import numpy as np

from src.simulator.generate import simulate_experiment


def test_simulator_returns_correct_row_count():
    df = simulate_experiment(n_users=100, seed=0)
    assert len(df) == 100


def test_simulator_has_both_variants():
    df = simulate_experiment(n_users=500, seed=0)
    variants = df["variant"].unique().tolist()
    assert set(variants) == {"control", "treatment"}


def test_simulator_variant_prices_correct():
    df = simulate_experiment(n_users=200, seed=0)
    assert df.loc[df["variant"] == "control", "price_shown"].unique().tolist() == [9.99]
    assert df.loc[df["variant"] == "treatment", "price_shown"].unique().tolist() == [14.99]


def test_simulator_revenue_only_on_conversion():
    df = simulate_experiment(n_users=500, seed=1)
    assert df.loc[~df["converted"], "revenue"].isna().all()
    assert df.loc[df["converted"], "revenue"].notna().all()


def test_true_lift_reflected_in_cr():
    """With n=10000, the simulated CRs should be within 2pp of configured values."""
    true_lift = 0.20
    baseline_cr = 0.10
    df = simulate_experiment(n_users=10000, baseline_cr=baseline_cr, true_lift=true_lift, seed=42)
    cr_control = df.loc[df["variant"] == "control", "converted"].mean()
    cr_treatment = df.loc[df["variant"] == "treatment", "converted"].mean()
    assert abs(cr_control - baseline_cr) < 0.02
    expected_treatment_cr = baseline_cr * (1 + true_lift)
    assert abs(cr_treatment - expected_treatment_cr) < 0.02


def test_timestamps_within_experiment_window():
    import pandas as pd
    from datetime import datetime, timedelta
    start = datetime(2024, 1, 1)
    days = 14
    df = simulate_experiment(n_users=100, experiment_days=days, start_date=start, seed=0)
    assert df["timestamp"].min() >= pd.Timestamp(start)
    assert df["timestamp"].max() < pd.Timestamp(start + timedelta(days=days + 1))

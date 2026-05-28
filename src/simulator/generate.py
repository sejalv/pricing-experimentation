from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.assignment.service import PRICES, assign_user_offline


def simulate_experiment(
    n_users: int = 5000,
    baseline_cr: float = 0.08,
    true_lift: float = 0.15,
    experiment_days: int = 30,
    start_date: datetime | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic A/B test data for the pricing experiment.

    - Users are assigned via GrowthBook hash (offline, no API needed)
    - Control CR: baseline_cr
    - Treatment CR: baseline_cr * (1 + true_lift)  [negative lift = higher price reduces conversions]
    - Revenue on conversion: Normal(price_shown * 12, price_shown * 2)  [annual subscription]

    Returns a DataFrame with columns:
        user_id, variant, price_shown, timestamp, converted, revenue
    """
    rng = np.random.default_rng(seed)
    start = start_date or datetime(2024, 1, 1)

    cr_map = {
        "control": baseline_cr,
        "treatment": baseline_cr * (1 + true_lift),
    }

    rows = []
    for i in range(n_users):
        user_id = f"user_{i:06d}"
        assignment = assign_user_offline(user_id)
        variant = assignment.variant
        price = assignment.price

        # Spread events across experiment duration
        day_offset = rng.integers(0, experiment_days)
        hour_offset = rng.integers(0, 24)
        ts = start + timedelta(days=int(day_offset), hours=int(hour_offset))

        cr = cr_map[variant]
        converted = bool(rng.random() < cr)
        # Annual subscription revenue (price × 12, with noise)
        revenue = float(rng.normal(price * 12, price * 2)) if converted else None

        rows.append({
            "user_id": user_id,
            "variant": variant,
            "price_shown": price,
            "timestamp": ts,
            "converted": converted,
            "revenue": revenue,
        })

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df


def print_summary(df: pd.DataFrame) -> None:
    print(f"\n{'=' * 50}")
    print(f"Experiment Simulation Summary ({len(df):,} users)")
    print(f"{'=' * 50}")
    for variant, group in df.groupby("variant"):
        cr = group["converted"].mean()
        avg_rev = group.loc[group["converted"], "revenue"].mean()
        n = len(group)
        print(f"\n  {variant.upper()}  (n={n:,})")
        print(f"    Price shown:    ${group['price_shown'].iloc[0]:.2f}")
        print(f"    Conversion rate: {cr:.1%}")
        print(f"    Avg revenue (converted): ${avg_rev:.2f}")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic pricing experiment data")
    parser.add_argument("--n", type=int, default=5000, help="Number of simulated users")
    parser.add_argument("--lift", type=float, default=0.15, help="True treatment lift (e.g. 0.15 = +15%)")
    parser.add_argument("--baseline-cr", type=float, default=0.08, help="Control conversion rate")
    parser.add_argument("--days", type=int, default=30, help="Experiment duration in days")
    parser.add_argument("--output", default=None, help="CSV output path (default: stdout summary only)")
    args = parser.parse_args()

    df = simulate_experiment(
        n_users=args.n,
        baseline_cr=args.baseline_cr,
        true_lift=args.lift,
        experiment_days=args.days,
    )
    print_summary(df)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved to {args.output}")
    else:
        # Write to PostgreSQL if DATABASE_URL is set
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            from sqlalchemy import create_engine
            from src.events.models import create_tables, get_engine
            from src.events.logger import log_exposure, log_conversion
            from src.events.models import get_session_factory

            engine = get_engine()
            create_tables(engine)
            Session = get_session_factory(engine)

            with Session() as session:
                for _, row in df.iterrows():
                    log_exposure(session, row["user_id"], row["variant"], row["price_shown"], row["timestamp"])
                    log_conversion(session, row["user_id"], row["variant"], row["converted"], row["revenue"], row["timestamp"])

            print(f"Wrote {len(df)} rows to PostgreSQL.")

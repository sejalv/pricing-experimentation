from __future__ import annotations

import os
from dataclasses import dataclass

from growthbook import GrowthBook, Experiment


EXPERIMENT_KEY = "pricing-test"
VARIANTS = ["control", "treatment"]
PRICES = {"control": 9.99, "treatment": 14.99}


@dataclass
class Assignment:
    user_id: str
    variant: str
    price: float
    in_experiment: bool


def assign_user(user_id: str, attributes: dict | None = None) -> Assignment:
    """
    Assign a user to a pricing variant using GrowthBook's deterministic hashing.

    Returns the same variant consistently for a given user_id.
    """
    api_host = os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100")
    client_key = os.getenv("GROWTHBOOK_CLIENT_KEY", "sdk-placeholder")

    user_attrs = {"id": user_id}
    if attributes:
        user_attrs.update(attributes)

    gb = GrowthBook(
        attributes=user_attrs,
        api_host=api_host,
        client_key=client_key,
    )

    experiment = Experiment(
        key=EXPERIMENT_KEY,
        variations=VARIANTS,
        coverage=1.0,  # 100% traffic included
    )

    result = gb.run(experiment)
    variant = result.value if result.inExperiment else VARIANTS[0]

    return Assignment(
        user_id=user_id,
        variant=variant,
        price=PRICES[variant],
        in_experiment=result.inExperiment,
    )


def assign_user_offline(user_id: str) -> Assignment:
    """
    Assign without connecting to GrowthBook API — uses hash directly.
    Useful for the simulator when GrowthBook is not running.
    """
    gb = GrowthBook(attributes={"id": user_id})
    experiment = Experiment(key=EXPERIMENT_KEY, variations=VARIANTS, coverage=1.0)
    result = gb.run(experiment)
    variant = result.value if result.inExperiment else VARIANTS[0]
    return Assignment(
        user_id=user_id,
        variant=variant,
        price=PRICES[variant],
        in_experiment=result.inExperiment,
    )

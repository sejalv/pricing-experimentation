"""
GrowthBook initialization script.

Runs after `docker-compose up` to create the pricing experiment
and retrieve an SDK client key. Run once:

    python init_script.py

Then copy the printed SDK key into your .env file as GROWTHBOOK_CLIENT_KEY.
"""
from __future__ import annotations

import json
import os
import sys
import time

import httpx

GROWTHBOOK_API = os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100")
SECRET_KEY = os.getenv("GROWTHBOOK_SECRET_KEY", "")


def wait_for_growthbook(timeout: int = 60) -> None:
    print("Waiting for GrowthBook API...")
    for _ in range(timeout):
        try:
            r = httpx.get(f"{GROWTHBOOK_API}/healthcheck", timeout=2)
            if r.status_code == 200:
                print("GrowthBook is up.")
                return
        except Exception:
            pass
        time.sleep(1)
    print("Timed out waiting for GrowthBook.", file=sys.stderr)
    sys.exit(1)


def get_headers() -> dict:
    if not SECRET_KEY:
        print("Warning: GROWTHBOOK_SECRET_KEY not set. Some API calls may be rejected.")
    return {"Authorization": f"Bearer {SECRET_KEY}", "Content-Type": "application/json"}


def create_sdk_connection(name: str = "pricing-pipeline-sdk") -> str:
    """Create an SDK connection and return the client key."""
    r = httpx.post(
        f"{GROWTHBOOK_API}/api/v1/sdk-connections",
        headers=get_headers(),
        json={
            "name": name,
            "language": "python",
            "environment": "production",
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        data = r.json()
        key = data.get("sdkConnection", {}).get("key", "")
        print(f"SDK connection created. Client key: {key}")
        return key
    print(f"SDK connection response ({r.status_code}): {r.text}")
    return ""


def create_experiment() -> None:
    """Create the pricing A/B experiment in GrowthBook."""
    r = httpx.post(
        f"{GROWTHBOOK_API}/api/v1/experiments",
        headers=get_headers(),
        json={
            "trackingKey": "pricing-test",
            "name": "Pricing Experiment: $9.99 vs $14.99",
            "hypothesis": "Higher pricing will reduce conversion rate but increase revenue per user.",
            "description": "Tests whether the $14.99/mo plan generates more revenue than $9.99/mo.",
            "variations": [
                {"key": "0", "name": "control ($9.99)"},
                {"key": "1", "name": "treatment ($14.99)"},
            ],
            "status": "running",
            "metrics": ["conversion_rate", "revenue_per_user"],
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        print("Experiment created successfully.")
    else:
        print(f"Experiment creation ({r.status_code}): {r.text}")


if __name__ == "__main__":
    wait_for_growthbook()
    sdk_key = create_sdk_connection()
    create_experiment()

    if sdk_key:
        print(f"\nAdd to your .env file:")
        print(f"GROWTHBOOK_CLIENT_KEY={sdk_key}")

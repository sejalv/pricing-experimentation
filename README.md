# Pricing Experimentation

A small, end-to-end example of a pricing A/B test comparing a **$9.99/month control** with a **$14.99/month treatment**. It includes deterministic experiment assignment with GrowthBook, event collection with FastAPI and PostgreSQL, synthetic-data generation, and frequentist and Bayesian analysis.

## What it does

- Assigns users consistently to `control` or `treatment` using GrowthBook hashing.
- Shows the assigned monthly price: $9.99 for control and $14.99 for treatment.
- Records exposure and conversion events through an HTTP API.
- Simulates experiment data without requiring GrowthBook or PostgreSQL.
- Evaluates conversion lift, revenue lift, confidence intervals, sample size, and Bayesian probability of improvement.
- Provides a results notebook with plots for posterior estimates and cumulative conversion rate.

## Project layout

```
src/
  assignment/service.py    GrowthBook-backed and offline variant assignment
  events/                  FastAPI event API and SQLAlchemy models
  simulator/generate.py    Synthetic experiment-data generator
  analysis/frequentist.py  Proportion/revenue tests and power helpers
  analysis/bayesian.py     Beta-Binomial conversion analysis
notebooks/
  experiment_results.ipynb Analysis notebook
tests/                     Unit tests
docker-compose.yml         GrowthBook, MongoDB, PostgreSQL, and API services
init_script.py             Creates the GrowthBook experiment and SDK connection
```

## Quick start: simulate locally

The simulator uses offline deterministic assignment, so this path does not require any services.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Print a summary for 5,000 simulated users
python -m src.simulator.generate

# Save a larger experiment to CSV
python -m src.simulator.generate --n 10000 --baseline-cr 0.08 --lift 0.15 --days 30 --output experiment.csv
```

`--lift` is the relative treatment conversion-rate change. For example, `--lift -0.15` models a 15% conversion-rate reduction at the higher price.

## Run the complete stack

The compose configuration starts:

- GrowthBook UI at <http://localhost:3000>
- GrowthBook API at <http://localhost:3100>
- event API at <http://localhost:8000>
- PostgreSQL at `localhost:5432`

1. Create your local environment file.

   ```bash
   cp .env.example .env
   ```

2. Start the services.

   ```bash
   docker compose up --build
   ```

3. Once GrowthBook is healthy, create the pricing experiment and SDK connection. Run this from another terminal with the virtual environment activated:

   ```bash
   python init_script.py
   ```

   Copy the client key printed by the script into `.env` as `GROWTHBOOK_CLIENT_KEY`, then restart the API service:

   ```bash
   docker compose up -d --force-recreate api
   ```

4. Populate PostgreSQL with synthetic events. The simulator writes to the database when `DATABASE_URL` is set.

   ```bash
   export DATABASE_URL=postgresql://experiment:experiment@localhost:5432/events
   python -m src.simulator.generate --n 5000 --lift 0.15
   ```

## Event API

The API creates its tables automatically at startup. Its interactive schema is available at <http://localhost:8000/docs>.

```bash
# Health check
curl http://localhost:8000/health

# Log a price exposure
curl -X POST http://localhost:8000/event/exposure \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"user_001","variant":"control","price_shown":9.99}'

# Log a conversion
curl -X POST http://localhost:8000/event/conversion \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"user_001","variant":"control","converted":true,"revenue":119.88}'

# Check stored-event counts
curl http://localhost:8000/events/summary
```

`revenue` is stored only for successful conversions; the logger clears it when `converted` is `false`.

## Assign a user in application code (optional)

```python
from src.assignment.service import assign_user

assignment = assign_user("user_001")
print(assignment.variant, assignment.price)
# e.g. treatment 14.99
```

Set `GROWTHBOOK_API_URL` and `GROWTHBOOK_CLIENT_KEY` to use the GrowthBook SDK connection. For scripts and tests that should avoid network access, use `assign_user_offline(user_id)` instead.

## Analyze results

After the simulator has populated PostgreSQL, launch Jupyter from the project root:

```bash
python -m jupyter lab
```

Open the local address printed in the terminal (normally [http://localhost:8888/lab](http://localhost:8888/lab)), then open `notebooks/experiment_results.ipynb` and choose **Run All Cells**. The notebook calculates:

- a two-proportion z-test for conversion rate;
- a Welch t-test with bootstrap confidence interval for converted-user revenue;
- Beta-Binomial posterior means, credible interval, probability treatment is better, and expected loss;
- cumulative conversion-rate and posterior plots; and
- minimum detectable effect and required per-variant sample size.

The core analysis helpers can also be used directly:

```python
from src.analysis.frequentist import z_test_proportions
from src.analysis.bayesian import beta_binomial_posterior

frequentist = z_test_proportions(400, 5000, 460, 5000)
bayesian = beta_binomial_posterior(400, 5000, 460, 5000)

print(frequentist.significant, frequentist.p_value)
print(bayesian.prob_treatment_better)
```

## Configuration

Copy `.env.example` to `.env` to keep local settings together:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection used by the API and simulator | Local `events` database |
| `GROWTHBOOK_API_URL` | GrowthBook API endpoint | `http://localhost:3100` |
| `GROWTHBOOK_CLIENT_KEY` | SDK client key created by `init_script.py` | `sdk-placeholder` |
| `GROWTHBOOK_SECRET_KEY` | Optional authorization value used by `init_script.py` | Empty |

## Tests

```bash
pytest
```

The tests cover simulation output, variant pricing, conversion/revenue behavior, frequentist testing, Bayesian posterior behavior, and sample-size helpers.

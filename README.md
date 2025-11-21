# 20251121

Simple Python implementation of the Cox-Ross-Rubinstein binomial option pricing model.

## Usage

Price European and American options using `binomial_option.py`:

```bash
python binomial_option.py
```

Or import the helper in your own code:

```python
from binomial_option import price_binomial_option

call_price = price_binomial_option(
    spot=100,
    strike=105,
    rate=0.05,
    volatility=0.2,
    maturity=1,
    steps=100,
    option_type="call",
    exercise="european",
)
```

Price options with a custom payoff using Monte Carlo simulation via `monte_carlo_option.py`:

```bash
python monte_carlo_option.py --spot 100 --strike 105 --rate 0.05 --volatility 0.2 \
    --maturity 1 --steps 252 --paths 100000 --payoff "max(s - strike, 0)" --seed 42
```

You can supply any Python expression for `--payoff`. The expression has access to:

- `path`: list of simulated prices
- `s` / `st`: terminal price (`path[-1]`)
- `spot`: starting price (`path[0]`)
- `strike`: the strike value passed via `--strike`
- `step`: the number of steps in the path

## Web Monte Carlo option calculator

A lightweight Flask app provides a browser-based option calculator powered by Monte Carlo simulation.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the server

```bash
python web_option_server.py
```

The app listens on `http://0.0.0.0:8000` by default. Open that URL in your browser to see the form UI. Fill in:

- Underlying inputs (`spot`, `strike`, `rate`, `volatility`, `maturity`, `dividend_yield`)
- Simulation controls (`steps`, `paths`, optional `seed`)
- Any payoff expression using `path`, `s`/`st`, `spot`, `strike`, and `step`

Click **Price option** to send the parameters to the backend and see the JSON response with the estimated price.

### API usage

You can also call the pricing endpoint directly:

```bash
curl -X POST http://localhost:8000/api/price \
  -H "Content-Type: application/json" \
  -d '{
    "spot": 100,
    "strike": 105,
    "rate": 0.05,
    "volatility": 0.2,
    "maturity": 1,
    "steps": 252,
    "paths": 50000,
    "payoff_expression": "max(s - strike, 0)"
  }'
```

The response includes the calculated `price` and echoes the inputs used. A `seed` field can be provided for repeatable simulations.

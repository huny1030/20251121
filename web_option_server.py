"""Simple Flask web server for Monte Carlo option pricing.

The server exposes:
- ``GET /``: Interactive form for entering simulation parameters.
- ``POST /api/price``: JSON endpoint to compute a price via Monte Carlo simulation.

It reuses :func:`price_monte_carlo_option` and :func:`build_expression_payoff`
from :mod:`monte_carlo_option` so the pricing logic stays in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from flask import Flask, jsonify, render_template_string, request

from monte_carlo_option import build_expression_payoff, price_monte_carlo_option


@dataclass
class PricingRequest:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    steps: int
    paths: int
    dividend_yield: float
    payoff_expression: str
    seed: int | None


def _parse_float(payload: Mapping[str, Any], key: str, *, default: float) -> float:
    value = payload.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number") from exc


def _parse_int(payload: Mapping[str, Any], key: str, *, default: int, minimum: int = 1) -> int:
    value = payload.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc

    if parsed < minimum:
        raise ValueError(f"{key} must be at least {minimum}")
    return parsed


def _parse_optional_int(payload: Mapping[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value in (None, "", "none", "null"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer or omitted") from exc


def parse_pricing_request(payload: Mapping[str, Any]) -> PricingRequest:
    return PricingRequest(
        spot=_parse_float(payload, "spot", default=100.0),
        strike=_parse_float(payload, "strike", default=100.0),
        rate=_parse_float(payload, "rate", default=0.05),
        volatility=_parse_float(payload, "volatility", default=0.2),
        maturity=_parse_float(payload, "maturity", default=1.0),
        steps=_parse_int(payload, "steps", default=252, minimum=1),
        paths=_parse_int(payload, "paths", default=50_000, minimum=1),
        dividend_yield=_parse_float(payload, "dividend_yield", default=0.0),
        payoff_expression=str(payload.get("payoff_expression", "max(s - strike, 0)")),
        seed=_parse_optional_int(payload, "seed"),
    )


def price_option(request_data: PricingRequest) -> float:
    payoff = build_expression_payoff(request_data.payoff_expression, extra_context={"strike": request_data.strike})

    return price_monte_carlo_option(
        spot=request_data.spot,
        rate=request_data.rate,
        volatility=request_data.volatility,
        maturity=request_data.maturity,
        steps=request_data.steps,
        paths=request_data.paths,
        dividend_yield=request_data.dividend_yield,
        payoff=payoff,
        seed=request_data.seed,
    )


app = Flask(__name__)


@app.get("/")
def index() -> str:
    """Serve a minimal HTML interface for interactive pricing."""
    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Monte Carlo Option Pricer</title>
            <style>
                body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 900px; line-height: 1.5; padding: 0 1rem; }
                form { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
                label { display: flex; flex-direction: column; gap: 0.25rem; font-weight: 600; }
                input, textarea { padding: 0.5rem; font-size: 1rem; }
                button { padding: 0.75rem 1.25rem; font-size: 1rem; cursor: pointer; }
                pre { background: #f7f7f9; padding: 1rem; border-radius: 8px; overflow-x: auto; }
                .full-width { grid-column: 1 / -1; }
                .error { color: #b00020; }
                .success { color: #006400; }
            </style>
        </head>
        <body>
            <h1>Monte Carlo Option Pricer</h1>
            <p>Enter parameters and click "Price option" to run a Monte Carlo simulation in the backend.</p>
            <form id="pricing-form">
                <label>Spot (S₀)<input name="spot" type="number" step="any" value="100" required /></label>
                <label>Strike (K)<input name="strike" type="number" step="any" value="100" required /></label>
                <label>Rate (r)<input name="rate" type="number" step="any" value="0.05" required /></label>
                <label>Volatility (σ)<input name="volatility" type="number" step="any" value="0.2" required /></label>
                <label>Maturity (T, years)<input name="maturity" type="number" step="any" value="1" required /></label>
                <label>Steps<input name="steps" type="number" min="1" step="1" value="252" required /></label>
                <label>Paths<input name="paths" type="number" min="1" step="1" value="50000" required /></label>
                <label>Dividend yield (q)<input name="dividend_yield" type="number" step="any" value="0" required /></label>
                <label>Seed (optional)<input name="seed" type="number" step="1" /></label>
                <label class="full-width">Payoff expression<textarea name="payoff_expression" rows="3">max(s - strike, 0)</textarea></label>
                <div class="full-width"><button type="submit">Price option</button></div>
            </form>
            <div id="result"></div>
            <script>
                async function handleSubmit(event) {
                    event.preventDefault();
                    const form = event.target;
                    const data = Object.fromEntries(new FormData(form));
                    const resultBox = document.getElementById('result');
                    resultBox.textContent = 'Running simulation...';
                    try {
                        const response = await fetch('/api/price', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data),
                        });
                        const payload = await response.json();
                        if (!response.ok) {
                            resultBox.innerHTML = `<p class="error">${payload.error || 'Failed to price option'}</p>`;
                            return;
                        }
                        const formatted = JSON.stringify(payload, null, 2);
                        resultBox.innerHTML = `<pre class="success">${formatted}</pre>`;
                    } catch (error) {
                        resultBox.innerHTML = `<p class="error">${error}</p>`;
                    }
                }
                document.getElementById('pricing-form').addEventListener('submit', handleSubmit);
            </script>
        </body>
        </html>
        """
    )


@app.post("/api/price")
def api_price() -> tuple[Any, int]:
    payload = request.get_json(silent=True) or {}

    try:
        pricing_request = parse_pricing_request(payload)
        price = price_option(pricing_request)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive catch for unexpected errors
        return jsonify({"error": str(exc)}), 500

    return (
        jsonify(
            {
                "price": price,
                "inputs": {
                    "spot": pricing_request.spot,
                    "strike": pricing_request.strike,
                    "rate": pricing_request.rate,
                    "volatility": pricing_request.volatility,
                    "maturity": pricing_request.maturity,
                    "steps": pricing_request.steps,
                    "paths": pricing_request.paths,
                    "dividend_yield": pricing_request.dividend_yield,
                    "payoff_expression": pricing_request.payoff_expression,
                    "seed": pricing_request.seed,
                },
            }
        ),
        200,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    app.run(host=host, port=port)


if __name__ == "__main__":
    run()

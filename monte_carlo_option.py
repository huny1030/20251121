"""Monte Carlo option pricing with flexible payoffs.

This module exposes :func:`price_monte_carlo_option`, which simulates
geometric Brownian motion price paths and discounts the expected payoff.
Payoffs can be provided as callables or as string expressions evaluated
for each simulated path. The expression helper makes it easy to prototype
non-standard payoffs without editing code.
"""
from __future__ import annotations

import argparse
import math
import random
from typing import Callable, Iterable

PayoffFunc = Callable[[list[float]], float]


def _validate_inputs(
    *,
    spot: float,
    volatility: float,
    maturity: float,
    steps: int,
    paths: int,
) -> None:
    if spot <= 0:
        raise ValueError("spot price must be positive")
    if volatility < 0:
        raise ValueError("volatility must be non-negative")
    if maturity <= 0:
        raise ValueError("maturity must be positive")
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if paths < 1:
        raise ValueError("paths must be at least 1")


def _simulate_path(
    *,
    spot: float,
    rate: float,
    volatility: float,
    dividend_yield: float,
    maturity: float,
    steps: int,
    rng: random.Random,
) -> list[float]:
    dt = maturity / steps
    drift = (rate - dividend_yield - 0.5 * volatility * volatility) * dt
    diffusion = volatility * math.sqrt(dt)

    prices = [spot]
    current = spot
    for _ in range(steps):
        z = rng.normalvariate(0.0, 1.0)
        current *= math.exp(drift + diffusion * z)
        prices.append(current)

    return prices


def build_expression_payoff(expression: str, *, extra_context: dict[str, float] | None = None) -> PayoffFunc:
    """Create a payoff function from a Python expression string.

    The expression is evaluated with access to:
    - ``path``: list of prices along the simulated path
    - ``s`` or ``st``: terminal price ``path[-1]``
    - ``spot``: initial price ``path[0]``
    - ``step``: number of steps in the path (len(path) - 1)
    - Any additional name/value pairs supplied via ``extra_context``

    Only mathematical functions from :mod:`math` along with ``max`` and
    ``min`` are allowed. Builtins are otherwise blocked to avoid surprises.
    """

    code = compile(expression, "<payoff>", "eval")
    math_namespace = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
    safe_globals = {**math_namespace, "max": max, "min": min, "__builtins__": {}}
    extra_context = extra_context or {}

    def payoff(path: list[float]) -> float:
        local_vars = {
            "path": path,
            "s": path[-1],
            "st": path[-1],
            "spot": path[0],
            "step": len(path) - 1,
            **extra_context,
        }
        return float(eval(code, safe_globals, local_vars))

    return payoff


def price_monte_carlo_option(
    *,
    spot: float,
    rate: float,
    volatility: float,
    maturity: float,
    steps: int,
    paths: int,
    payoff: PayoffFunc,
    dividend_yield: float = 0.0,
    seed: int | None = None,
) -> float:
    """Price an option using Monte Carlo simulation.

    Parameters
    ----------
    spot: float
        Current underlying price ``S_0``.
    rate: float
        Continuously compounded risk-free rate ``r``.
    volatility: float
        Annualized volatility ``sigma``.
    maturity: float
        Time to maturity in years ``T``.
    steps: int
        Number of simulation time steps.
    paths: int
        Number of Monte Carlo paths to simulate.
    payoff: Callable[[list[float]], float]
        Function that receives the entire simulated path and returns the
        path's payoff.
    dividend_yield: float, optional
        Continuous dividend yield ``q``. Default is 0.
    seed: int, optional
        Seed for the random number generator to produce repeatable runs.

    Returns
    -------
    float
        Present value estimate of the option.
    """
    _validate_inputs(
        spot=spot,
        volatility=volatility,
        maturity=maturity,
        steps=steps,
        paths=paths,
    )

    rng = random.Random(seed)
    discount = math.exp(-rate * maturity)

    payoffs: list[float] = []
    for _ in range(paths):
        path = _simulate_path(
            spot=spot,
            rate=rate,
            volatility=volatility,
            dividend_yield=dividend_yield,
            maturity=maturity,
            steps=steps,
            rng=rng,
        )
        payoffs.append(payoff(path))

    return discount * (sum(payoffs) / len(payoffs))


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monte Carlo option pricer with custom payoff expressions.")
    parser.add_argument("--spot", type=float, default=100.0, help="current underlying price (S0)")
    parser.add_argument("--strike", type=float, default=100.0, help="strike price (K), available in the payoff expression")
    parser.add_argument("--rate", type=float, default=0.05, help="risk-free rate (r) as a continuously compounded value")
    parser.add_argument("--volatility", type=float, default=0.2, help="annualized volatility (sigma)")
    parser.add_argument("--maturity", type=float, default=1.0, help="time to maturity in years (T)")
    parser.add_argument("--steps", type=int, default=50, help="number of time steps in each path")
    parser.add_argument("--paths", type=int, default=50_000, help="number of Monte Carlo paths to simulate")
    parser.add_argument("--dividend-yield", type=float, default=0.0, help="continuous dividend yield (q)")
    parser.add_argument(
        "--payoff",
        dest="payoff_expression",
        default="max(s - strike, 0)",
        help="Python expression for the payoff; available names: path, s, st, spot, strike, step",
    )
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducible runs")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = _parse_args(argv)

    payoff = build_expression_payoff(args.payoff_expression, extra_context={"strike": args.strike})

    price = price_monte_carlo_option(
        spot=args.spot,
        rate=args.rate,
        volatility=args.volatility,
        maturity=args.maturity,
        steps=args.steps,
        paths=args.paths,
        dividend_yield=args.dividend_yield,
        payoff=payoff,
        seed=args.seed,
    )

    print(f"Estimated price: {price:.4f}")


if __name__ == "__main__":
    main()

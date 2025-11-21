"""Binomial option pricing (Cox-Ross-Rubinstein) implementation.

The module exposes :func:`price_binomial_option` to price European or American
calls and puts. Example:

>>> price_binomial_option(
...     spot=100,
...     strike=105,
...     rate=0.05,
...     volatility=0.2,
...     maturity=1,
...     steps=100,
...     option_type="call",
...     exercise="european",
... )
8.026...
"""
from __future__ import annotations

import math
from typing import Literal


OptionType = Literal["call", "put"]
ExerciseStyle = Literal["european", "american"]


def _validate_inputs(spot: float, strike: float, maturity: float, steps: int) -> None:
    if spot <= 0:
        raise ValueError("spot price must be positive")
    if strike <= 0:
        raise ValueError("strike price must be positive")
    if maturity <= 0:
        raise ValueError("maturity must be positive")
    if steps < 1:
        raise ValueError("steps must be at least 1")


def price_binomial_option(
    *,
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    steps: int,
    option_type: OptionType = "call",
    exercise: ExerciseStyle = "european",
    dividend_yield: float = 0.0,
) -> float:
    """Price an option with the Cox-Ross-Rubinstein binomial model.

    Parameters
    ----------
    spot: float
        Current underlying price ``S_0``.
    strike: float
        Strike price ``K``.
    rate: float
        Continuously compounded risk-free rate ``r``.
    volatility: float
        Annualized volatility ``sigma``.
    maturity: float
        Time to maturity in years ``T``.
    steps: int
        Number of binomial steps ``N``.
    option_type: {"call", "put"}
        Option payoff type.
    exercise: {"european", "american"}
        Exercise style. Early exercise is only applied for American options.
    dividend_yield: float, optional
        Continuous dividend yield ``q``. Default is 0.

    Returns
    -------
    float
        Present value of the option.
    """
    _validate_inputs(spot, strike, maturity, steps)

    dt = maturity / steps
    if dt == 0:
        raise ValueError("time step size became zero")

    up = math.exp(volatility * math.sqrt(dt))
    down = 1 / up

    growth = math.exp((rate - dividend_yield) * dt)
    prob_up = (growth - down) / (up - down)

    if not 0 <= prob_up <= 1:
        raise ValueError("risk-neutral probability is outside [0, 1]; adjust inputs")

    discount = math.exp(-rate * dt)

    # Terminal payoffs
    payoffs = []
    for i in range(steps + 1):
        asset_price = spot * (up ** i) * (down ** (steps - i))
        intrinsic = max(asset_price - strike, 0.0) if option_type == "call" else max(strike - asset_price, 0.0)
        payoffs.append(intrinsic)

    # Backward induction through the tree
    american = exercise == "american"
    for step in range(steps - 1, -1, -1):
        for i in range(step + 1):
            continuation = discount * (prob_up * payoffs[i + 1] + (1 - prob_up) * payoffs[i])

            if american:
                asset_price = spot * (up ** i) * (down ** (step - i))
                intrinsic = max(asset_price - strike, 0.0) if option_type == "call" else max(strike - asset_price, 0.0)
                payoffs[i] = max(continuation, intrinsic)
            else:
                payoffs[i] = continuation

    return payoffs[0]


if __name__ == "__main__":
    european_call = price_binomial_option(
        spot=100,
        strike=105,
        rate=0.05,
        volatility=0.2,
        maturity=1,
        steps=100,
        option_type="call",
        exercise="european",
    )
    american_put = price_binomial_option(
        spot=100,
        strike=105,
        rate=0.05,
        volatility=0.2,
        maturity=1,
        steps=100,
        option_type="put",
        exercise="american",
    )
    print(f"European call: {european_call:.4f}")
    print(f"American put : {american_put:.4f}")

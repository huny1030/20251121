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

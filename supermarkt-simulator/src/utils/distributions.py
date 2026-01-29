"""Distribution sampling utilities for simulation logic."""

import random
import math
from typing import Optional


def sample_uniform(a: float, b: float, rng: Optional[random.Random] = None) -> float:
    """Sample from Uniform(a, b)."""
    r = rng or random
    low, high = (a, b) if a <= b else (b, a)
    return r.uniform(low, high)


def sample_normal(mu: float, sigma: float, rng: Optional[random.Random] = None) -> float:
    """Sample from Normal(mu, sigma)."""
    r = rng or random
    if sigma == 0:
        return mu
    return r.normalvariate(mu, sigma)


def sample_exponential(mean: float, rng: Optional[random.Random] = None) -> float:
    """Sample from Exponential(mean)."""
    r = rng or random
    if mean <= 0:
        return 0.0
    return r.expovariate(1.0 / mean)

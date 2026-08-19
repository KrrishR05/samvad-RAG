"""
SAMVAD Analytics — Percentile Calculations

Reusable statistical functions for latency analysis.
These are fully implemented and testable now —
they do not depend on the RAG pipeline.
"""

from __future__ import annotations

import math
from typing import Sequence

from app.schemas.analytics import PercentileStats


def compute_percentile(values: Sequence[float], percentile: float) -> float:
    """
    Compute the given percentile from a list of values
    using the nearest-rank method.

    Args:
        values: Non-empty sequence of numeric values.
        percentile: Percentile to compute (0–100).

    Returns:
        The percentile value.

    Raises:
        ValueError: If values is empty or percentile is out of range.
    """
    if not values:
        raise ValueError("Cannot compute percentile of an empty sequence.")
    if not (0 <= percentile <= 100):
        raise ValueError(f"Percentile must be between 0 and 100, got {percentile}.")

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    if n == 1:
        return sorted_vals[0]

    # Linear interpolation method
    rank = (percentile / 100.0) * (n - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    fraction = rank - lower

    if lower == upper:
        return sorted_vals[lower]

    return sorted_vals[lower] + fraction * (sorted_vals[upper] - sorted_vals[lower])


def compute_stats(values: Sequence[float]) -> PercentileStats:
    """
    Compute full percentile statistics for a list of values.

    Returns a PercentileStats with p50, p70, p100, mean, min, max, count.
    If values is empty, returns a zeroed-out stats object.
    """
    if not values:
        return PercentileStats(count=0)

    return PercentileStats(
        p50=round(compute_percentile(values, 50), 2),
        p70=round(compute_percentile(values, 70), 2),
        p100=round(compute_percentile(values, 100), 2),
        mean=round(sum(values) / len(values), 2),
        min=round(min(values), 2),
        max=round(max(values), 2),
        count=len(values),
    )

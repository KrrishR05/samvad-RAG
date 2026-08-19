"""
Tests — Percentile Calculations
"""

import pytest

from app.analytics.percentiles import compute_percentile, compute_stats


class TestComputePercentile:
    def test_single_value(self):
        assert compute_percentile([42.0], 50) == 42.0

    def test_median_odd(self):
        result = compute_percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50)
        assert result == 3.0

    def test_median_even(self):
        result = compute_percentile([1.0, 2.0, 3.0, 4.0], 50)
        assert result == 2.5

    def test_p100(self):
        result = compute_percentile([10.0, 20.0, 30.0], 100)
        assert result == 30.0

    def test_p0(self):
        result = compute_percentile([10.0, 20.0, 30.0], 0)
        assert result == 10.0

    def test_p70(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        result = compute_percentile(values, 70)
        assert result == pytest.approx(73.0)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            compute_percentile([], 50)

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            compute_percentile([1.0], 101)


class TestComputeStats:
    def test_empty(self):
        stats = compute_stats([])
        assert stats.count == 0
        assert stats.p50 is None

    def test_basic(self):
        stats = compute_stats([10.0, 20.0, 30.0, 40.0, 50.0])
        assert stats.count == 5
        assert stats.p50 == 30.0
        assert stats.min == 10.0
        assert stats.max == 50.0
        assert stats.mean == 30.0

    def test_single(self):
        stats = compute_stats([99.0])
        assert stats.count == 1
        assert stats.p50 == 99.0
        assert stats.p100 == 99.0

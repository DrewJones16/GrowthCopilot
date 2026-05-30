"""Rolling baseline helpers. MAD is preferred over std because it survives
the kinds of one-day spikes common in app analytics."""
import statistics


def median_mad(values: list[float]) -> tuple[float, float]:
    m = statistics.median(values)
    mad = statistics.median([abs(v - m) for v in values])
    return m, mad


def weighted_mean(values: list[float], weights: list[float]) -> float:
    total_w = sum(weights)
    if total_w == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / total_w

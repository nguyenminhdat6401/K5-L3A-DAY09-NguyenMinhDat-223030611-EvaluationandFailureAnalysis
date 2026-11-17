"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    if len(human) != len(judge):
        raise ValueError("human and judge must have equal length")

    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}

    for truth, predicted in zip(human, judge):
        if truth not in {"PASS", "FAIL"}:
            raise ValueError(f"invalid human label: {truth}")
        if predicted not in {"PASS", "FAIL"}:
            raise ValueError(f"invalid judge label: {predicted}")

        if truth == POS:
            key = "tp" if predicted == POS else "fn"
        else:
            key = "fp" if predicted == POS else "tn"

        counts[key] += 1

    return counts


def precision_recall(
    human: Sequence[str], judge: Sequence[str]
) -> tuple[float, float]:
    counts = confusion(human, judge)
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    counts = confusion(human, judge)
    n = sum(counts.values())

    if n == 0:
        raise ValueError("kappa is undefined for empty data")

    tp, fp = counts["tp"], counts["fp"]
    fn, tn = counts["fn"], counts["tn"]

    observed = (tp + tn) / n
    human_positive = (tp + fn) / n
    judge_positive = (tp + fp) / n
    expected = (
        human_positive * judge_positive
        + (1 - human_positive) * (1 - judge_positive)
    )

    if expected == 1.0:
        raise ValueError("kappa is undefined")

    return (observed - expected) / (1 - expected)


def rogan_gladen(
    observed_rate: float,
    sensitivity: float,
    specificity: float,
) -> float:
    if any(
        not 0.0 <= value <= 1.0
        for value in (observed_rate, sensitivity, specificity)
    ):
        raise ValueError("rates must be between 0 and 1")

    denominator = sensitivity + specificity - 1
    if denominator <= 0:
        raise ValueError("sensitivity + specificity must exceed 1")

    corrected = (observed_rate + specificity - 1) / denominator
    return max(0.0, min(1.0, corrected))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    if len(a) != len(b) or len(a) == 0:
        raise ValueError("paired samples must have equal, nonzero length")
    if n_resamples <= 0:
        raise ValueError("n_resamples must be positive")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    left = np.asarray(a, dtype=float)
    right = np.asarray(b, dtype=float)

    if left.ndim != 1 or right.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("samples must contain only finite values")

    delta = float(np.mean(left - right))

    if np.array_equal(left, right):
        return 0.0, 0.0, 0.0

    if len(left) < 2:
        raise ValueError("bootstrap requires at least two paired items")

    def mean_difference(x, y, axis=-1):
        return np.mean(x - y, axis=axis)

    result = bootstrap(
        (left, right),
        mean_difference,
        paired=True,
        vectorized=True,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="percentile",
        rng=np.random.default_rng(rng),
    )

    return (
        delta,
        float(result.confidence_interval.low),
        float(result.confidence_interval.high),
    )


def _validate_pass_k(n: int, c: int, k: int) -> None:
    if any(type(value) is not int for value in (n, c, k)):
        raise ValueError("n, c and k must be integers")
    if n < 1:
        raise ValueError("n must be positive")
    if not 0 <= c <= n:
        raise ValueError("c must be between 0 and n")
    if not 1 <= k <= n:
        raise ValueError("k must be between 1 and n")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that at least one of k sampled trials passes."""
    from math import comb

    _validate_pass_k(n, c, k)
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """Probability that all k sampled trials pass."""
    from math import comb

    _validate_pass_k(n, c, k)
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)

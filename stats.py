"""Statistical analysis helpers for Research Integrity Auditor.

Implements `analyze_p_values()` which follows Developer 2's spec:
- Filter p-values to [0.00, 0.05].
- Compute counts for Risky (0.04-0.05) and Highly Significant (<=0.01).
- Compute a risk ratio and derive an Integrity Score (0-100) and status string.

The score mapping uses: score = int(100 * (1 / (1 + risk_ratio))).
This yields 100 when there are no Risky values, ~50 when risky==high_sig,
and approaches 0 for very large ratios.
"""
from typing import Iterable, Tuple, Dict


def analyze_p_values(p_values: Iterable[float]) -> Tuple[int, str]:
    """Analyze a sequence of p-values and return (integrity_score, status).

    Args:
        p_values: Iterable of raw p-values (floats).

    Returns:
        (score, status): score is an int 0-100 (higher = more reliable).
            status is one of: 'No p-values in 0-0.05', 'High Risk',
            'Moderate Risk', 'Likely Reliable'.
    """
    filtered = [float(p) for p in p_values if p is not None]
    # Keep only values within the conventional p-curve window
    window = [p for p in filtered if 0.0 <= p <= 0.05]

    if len(window) == 0:
        return 100, "No p-values in 0-0.05"

    risky_count = sum(1 for p in window if 0.04 <= p <= 0.05)
    high_sig_count = sum(1 for p in window if p <= 0.01)

    # Avoid division by zero; if there are no highly significant values,
    # treat denominator as 1 so ratio grows proportionally to risky_count.
    denom = high_sig_count if high_sig_count > 0 else 1
    risk_ratio = risky_count / denom

    # Map ratio -> score in a smooth way: score = 100 / (1 + ratio)
    score = int(round(100 * (1.0 / (1.0 + risk_ratio))))

    if score < 40:
        status = "High Risk"
    elif score < 70:
        status = "Moderate Risk"
    else:
        status = "Likely Reliable"

    return score, status


def summarize_p_values(p_values: Iterable[float]) -> Dict[str, float]:
    """Return detailed counts and the computed risk ratio for debugging.

    This helper is useful for UI or logging.
    """
    filtered = [float(p) for p in p_values if p is not None]
    window = [p for p in filtered if 0.0 <= p <= 0.05]
    risky_count = sum(1 for p in window if 0.04 <= p <= 0.05)
    high_sig_count = sum(1 for p in window if p <= 0.01)
    denom = high_sig_count if high_sig_count > 0 else 1
    risk_ratio = risky_count / denom
    return {
        "filtered_count": len(window),
        "risky_count": risky_count,
        "high_sig_count": high_sig_count,
        "risk_ratio": risk_ratio,
    }


if __name__ == "__main__":
    # Quick manual smoke test
    sample = [0.005, 0.009, 0.03, 0.045, 0.049]
    score, status = analyze_p_values(sample)
    print(f"Score={score}, status={status}")

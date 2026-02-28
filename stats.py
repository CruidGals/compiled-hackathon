"""Statistical analysis helpers for Research Integrity Auditor (Developer 2).

MATHEMATICAL FOUNDATION (P-Curve Detection):
============================================

The p-curve is a forensic statistical tool for detecting p-hacking—the practice
of manipulating data analysis (HARKing, p-hacking, publication bias) to make
results appear statistically significant.

KEY PRINCIPLE:
In legitimate research with a true effect, p-values follow a right-skewed
distribution. Most discoveries are highly significant (p ≤ 0.01), fewer are
marginally significant (0.04-0.05), and this frequency naturally decreases
toward the 0.05 threshold.

In p-hacked data, researchers iteratively analyze, delete failures, or adjust
hypotheses until results barely cross p < 0.05. This creates an UNNATURAL "bump"
clustering at 0.044-0.049, inverting the natural ratio.

DETECTION LOGIC:
- Calculate: risky_count = p-values in [0.04, 0.05]
- Calculate: high_sig_count = p-values in (0.00, 0.01]
- Risk Ratio = risky_count / max(high_sig_count, 1)
  * Legitimate (right-skew): ratio << 1
  * P-hacked (inverted bump): ratio >> 1
- Map ratio → Integrity Score (0-100):
  score = 100 / (1 + risk_ratio)
  * score = 100 when ratio = 0 (no risky values, clean data)
  * score ≈ 50 when ratio ≈ 1 (borderline suspicious)
  * score → 0 when ratio >> 1 (highly suspicious)

MATHEMATICAL PROPERTIES VALIDATED IN TESTS:
- Bounded output: score ∈ [0, 100]
- Monotonic: higher risky/high_sig ratio → lower score
- Edge cases: empty data, no values in window, outliers
- Distribution validation: Beta(0.5, 5) models genuine right-skew

REFERENCES:
- Simonsohn, U., Nelson, L. D., & Simmons, J. P. (2014).
  "P-curve: A key to the file-drawer." Journal of Experimental Psychology.

MVP NOTE: Analysis uses raw p-values only. Context (e.g. which hypothesis, test type,
or outcome) could be added later for finer-grained credibility assessment.
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

    Uses every detected p-value: total_count and count_above_005 include values > 0.05.
    The integrity score (risk_ratio, etc.) is based only on [0, 0.05] per p-curve methodology.
    """
    filtered = [float(p) for p in p_values if p is not None]
    window = [p for p in filtered if 0.0 <= p <= 0.05]
    above_005 = [p for p in filtered if p > 0.05]
    risky_count = sum(1 for p in window if 0.04 <= p <= 0.05)
    high_sig_count = sum(1 for p in window if p <= 0.01)
    denom = high_sig_count if high_sig_count > 0 else 1
    risk_ratio = risky_count / denom
    return {
        "total_count": len(filtered),
        "filtered_count": len(window),
        "count_above_005": len(above_005),
        "risky_count": risky_count,
        "high_sig_count": high_sig_count,
        "risk_ratio": risk_ratio,
    }


if __name__ == "__main__":
    # Quick manual smoke test
    sample = [0.005, 0.009, 0.03, 0.045, 0.049]
    score, status = analyze_p_values(sample)
    print(f"Score={score}, status={status}")

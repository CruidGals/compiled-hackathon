"""Comprehensive p-curve analysis tests.

These tests validate the detection of p-hacking through p-curve analysis.
The mathematical principle: In legitimate research, p-values follow a right-skewed
distribution (more highly significant results at p<=0.01 than at 0.04-0.05).
In p-hacked data, there's an unnatural clustering near p=0.05 threshold.

Tests cover:
  - Standard scientific scenario (right-skewed, legitimate distribution)
  - P-hacking scenario (clustering at 0.04-0.05, suspicious bump)
  - Edge cases and robustness
  - Mathematical validation of the risk ratio
  - Miner integration: PDF bytes -> get_p_values -> analyze_p_values/summarize_p_values
"""
import sys
import os
from pathlib import Path
import pytest
import matplotlib.pyplot as plt
import numpy as np
import fitz  # PyMuPDF - used for miner integration tests

# Fix import: add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stats import analyze_p_values, summarize_p_values
from miner import get_p_values


# ============================================================================
# SCENARIO 1: Legitimate Research (Right-Skewed Distribution)
# ============================================================================

def test_legitimate_right_skewed_distribution():
    """Test detection of a legitimate right-skewed p-curve.

    In real scientific findings, the vast majority of significant p-values
    cluster at highly significant levels (p <= 0.01). As p increases toward 0.05,
    the frequency drops naturally. This produces a right-skewed histogram.

    Expected: High integrity score + "Likely Reliable" status
    """
    # Example: 60 legitimate discoveries from a real effect
    legitimate_data = (
        [0.0001, 0.0005, 0.001, 0.003, 0.005] * 8 +  # 40 highly significant
        [0.01, 0.012, 0.015, 0.018] * 3 +             # 12 moderately sig
        [0.025, 0.03, 0.035, 0.04] * 2                # 8 near threshold
    )
    score, status = analyze_p_values(legitimate_data)
    # High sig count >> risky count, so risk_ratio is small, score is high
    assert score > 70, f"Expected score > 70 for legitimate data, got {score}"
    assert status == "Likely Reliable"
    
    summary = summarize_p_values(legitimate_data)
    assert summary["high_sig_count"] > summary["risky_count"], (
        "Legitimate data should have more highly significant than risky counts"
    )


def test_right_skew_mathematical_property():
    """Verify the right-skew property: P(p <= 0.01) >> P(0.04 <= p <= 0.05).

    Mathematical foundation: When testing a true effect, p-values follow
    a beta distribution skewed toward zero. The ratio of marginal (0.04-0.05)
    to highly significant (<=0.01) should be << 1.
    """
    # Synthetic right-skewed distribution
    p_values = (
        np.random.beta(0.5, 5, 500) * 0.05  # Beta(0.5, 5) skewed right, scaled to [0, 0.05]
    )
    p_values = [max(0.0001, p) for p in p_values]  # Avoid zeros

    summary = summarize_p_values(p_values)
    ratio = summary["risk_ratio"]

    # For genuine right-skew: ratio should be much less than 1
    assert ratio < 1.0, (
        f"Right-skewed distribution should have risk_ratio < 1, got {ratio}. "
        f"Risky: {summary['risky_count']}, HighSig: {summary['high_sig_count']}"
    )


# ============================================================================
# SCENARIO 2: P-Hacked Data (Suspicious Bump at 0.05 Threshold)
# ============================================================================

def test_phacked_clustering_at_threshold():
    """Test detection of p-hacking via clustering at the 0.05 boundary.

    P-hackers repeatedly analyze data, delete failures, try different
    statistical tests, or adjust parameters until results barely cross
    p < 0.05. This creates an unnatural "bump" at 0.044-0.049.

    Expected: Low integrity score + "High Risk" or "Moderate Risk" status
    """
    # Simulate a p-hacked paper: most values artificially clustered near 0.05
    phacked_data = (
        [0.001] * 2 +              # Few legitimate highly significant
        [0.045, 0.046, 0.047, 0.048, 0.049] * 8 +  # 40 suspicious bump at 0.05
        [0.02, 0.025, 0.03] * 3    # Some filler in middle
    )
    score, status = analyze_p_values(phacked_data)
    # Risk ratio will be large (40 risky vs 2 highly sig), score drops
    assert score < 40, f"Expected score < 40 for p-hacked data, got {score}"
    assert status in ["High Risk", "Moderate Risk"]

    summary = summarize_p_values(phacked_data)
    assert summary["risky_count"] > summary["high_sig_count"], (
        "P-hacked data should have more risky than highly significant"
    )


def test_phacking_risk_ratio_amplified():
    """Verify that p-hacking produces an inverted (risky > high_sig) ratio.

    Mathematical signature of p-hacking: the ratio of marginal results
    (0.04-0.05) to highly significant (<=0.01) is >> 1, indicating the
    distribution has been artificially skewed toward the threshold.
    """
    # Pure p-hacking scenario: concentrate at 0.044-0.050
    phacked = [
        0.044, 0.0448, 0.0456, 0.0464, 0.0472, 0.048, 0.0488, 0.0496,
        0.0445, 0.0453, 0.0461, 0.0469, 0.0477, 0.0485, 0.0493, 0.05,
    ] * 5  # Repeat for statistical significance

    summary = summarize_p_values(phacked)
    ratio = summary["risk_ratio"]

    # For p-hacking: ratio should be >> 1 (almost all are risky)
    assert ratio > 1.0, (
        f"P-hacked data should have risk_ratio > 1, got {ratio}. "
        f"Risky: {summary['risky_count']}, HighSig: {summary['high_sig_count']}"
    )
    score, status = analyze_p_values(phacked)
    assert score < 50, f"P-hacked data should have low score, got {score}"


# ============================================================================
# EDGE CASES AND ROBUSTNESS
# ============================================================================

def test_empty_input():
    """Test handling of empty p-value list."""
    score, status = analyze_p_values([])
    assert score == 100
    assert status == "No p-values in 0-0.05"


def test_no_values_in_window():
    """Test handling when no p-values fall in [0.00, 0.05]."""
    score, status = analyze_p_values([0.1, 0.5, 0.99])
    assert score == 100
    assert status == "No p-values in 0-0.05"


def test_all_highly_significant():
    """Test when all p-values are highly significant (p <= 0.01)."""
    data = [0.0001, 0.001, 0.005, 0.01, 0.008]
    score, status = analyze_p_values(data)
    # No risky values, so ratio = 0, score = 100
    assert score == 100
    assert status == "Likely Reliable"


def test_all_risky():
    """Test when all p-values are risky (0.04 <= p <= 0.05)."""
    data = [0.040, 0.042, 0.044, 0.046, 0.048, 0.050] * 5
    score, status = analyze_p_values(data)
    # All risky, no highly significant, denominator = 1
    # ratio = 30 / 1 = 30, score = int(100 / (1 + 30)) = 3
    assert score < 10
    assert status == "High Risk"


def test_none_and_invalid_handling():
    """Test robustness with None values and non-numeric types."""
    # The function should filter None values gracefully
    data = [0.005, None, 0.015, 0.045, None]
    score, status = analyze_p_values(data)
    # Should process [0.005, 0.015, 0.045]
    assert isinstance(score, int)
    assert isinstance(status, str)


def test_scores_are_bounded_0_100():
    """Test that all scores remain in [0, 100]."""
    test_cases = [
        [],
        [0.001],
        [0.049] * 100,
        [0.001, 0.002, 0.025, 0.04, 0.045],
    ]
    for data in test_cases:
        score, _ = analyze_p_values(data)
        assert 0 <= score <= 100, f"Score {score} out of bounds for data {data}"


def test_status_strings_valid():
    """Test that status strings are one of the expected values."""
    valid_statuses = {
        "No p-values in 0-0.05",
        "High Risk",
        "Moderate Risk",
        "Likely Reliable"
    }
    test_cases = [
        [],
        [0.001],
        [0.045] * 10,
        [0.001] * 10,
        [0.025],
    ]
    for data in test_cases:
        _, status = analyze_p_values(data)
        assert status in valid_statuses, (
            f"Unexpected status '{status}' for data {data}"
        )


# ============================================================================
# MINER INTEGRATION (PDF -> get_p_values -> stats)
# ============================================================================

def _pdf_bytes_with_text(text):
    """Build a minimal PDF containing the given text; return its bytes."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_miner_extract_then_analyze_legitimate():
    """miner.get_p_values(PDF bytes) -> stats.analyze_p_values: legitimate pattern."""
    text = "Results: p=0.001, p=0.005, p<0.01, p=0.008."
    pdf_bytes = _pdf_bytes_with_text(text)
    p_values = get_p_values(pdf_bytes)
    assert len(p_values) >= 3, f"Expected at least 3 p-values from miner, got {p_values}"
    score, status = analyze_p_values(p_values)
    assert score >= 70, f"Legitimate p-values should score >= 70, got {score}"
    assert status == "Likely Reliable"


def test_miner_extract_then_analyze_phacked():
    """miner.get_p_values(PDF bytes) -> stats.analyze_p_values: p-hacked pattern."""
    text = "p=0.045, p=0.046, p=0.047, p=0.048, p=0.049, p=0.044."
    pdf_bytes = _pdf_bytes_with_text(text)
    p_values = get_p_values(pdf_bytes)
    assert len(p_values) >= 3, f"Expected at least 3 p-values from miner, got {p_values}"
    score, status = analyze_p_values(p_values)
    assert score < 70, f"P-hacked pattern should score < 70, got {score}"
    assert status in ("High Risk", "Moderate Risk")


def test_miner_extract_then_summarize():
    """miner.get_p_values -> stats.summarize_p_values returns expected keys."""
    text = "p=0.02, p=0.04, p<0.01."
    pdf_bytes = _pdf_bytes_with_text(text)
    p_values = get_p_values(pdf_bytes)
    summary = summarize_p_values(p_values)
    assert "filtered_count" in summary
    assert "risky_count" in summary
    assert "high_sig_count" in summary
    assert "risk_ratio" in summary


# ============================================================================
# VISUALIZATION & DEMONSTRATION HELPERS
# ============================================================================

def visualize_comparison(save_path=None):
    """Generate comprehensive p-curve visualizations.

    Creates 3 figures:
    1. Side-by-side legitimate vs. p-hacked distributions
    2. Distribution shapes with region annotations
    3. Risk ratio to score mapping charts

    Args:
        save_path: If provided, saves figures to this directory. Otherwise displays inline.
    """
    print("\n" + "=" * 80)
    print("P-CURVE VISUALIZATION: Detecting P-Hacking")
    print("=" * 80)

    # Generate samples
    print("\n[1] Generating Legitimate (Right-Skewed) Distribution...")
    legitimate = np.random.beta(0.5, 5, 200) * 0.05
    legitimate = np.clip(legitimate, 0.0001, 0.05)
    score_legit, status_legit = analyze_p_values(legitimate)
    summary_legit = summarize_p_values(legitimate)
    print(f"    ✓ Score: {score_legit}/100, Status: {status_legit}")
    print(f"    ✓ Risk Ratio: {summary_legit['risk_ratio']:.3f}")

    print("\n[2] Generating P-Hacked (Bump at 0.05) Distribution...")
    phacked = np.concatenate([
        np.random.uniform(0.044, 0.050, 150),
        np.random.uniform(0.001, 0.02, 50),
    ])
    score_phack, status_phack = analyze_p_values(phacked)
    summary_phack = summarize_p_values(phacked)
    print(f"    ✗ Score: {score_phack}/100, Status: {status_phack}")
    print(f"    ✗ Risk Ratio: {summary_phack['risk_ratio']:.3f}")

    # Figure 1: Comparison
    print("\n[3] Creating Figure 1: Side-by-Side Comparison...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(legitimate, bins=10, color="green", alpha=0.7, edgecolor="black", linewidth=1.5)
    ax1.axvline(0.01, color="red", linestyle="--", linewidth=2, label="p=0.01")
    ax1.axvline(0.05, color="orange", linestyle="--", linewidth=2, label="p=0.05")
    ax1.set_title(
        f"Legitimate: RIGHT-SKEWED\nScore: {score_legit}/100 ({status_legit})",
        fontsize=12, fontweight="bold", color="green"
    )
    ax1.set_xlabel("p-value")
    ax1.set_ylabel("Frequency")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax1.text(
        0.025, max(ax1.get_ylim()) * 0.9,
        f"Risk Ratio: {summary_legit['risk_ratio']:.3f}",
        fontsize=10, bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.8)
    )

    ax2.hist(phacked, bins=10, color="red", alpha=0.7, edgecolor="black", linewidth=1.5)
    ax2.axvline(0.01, color="green", linestyle="--", linewidth=2, label="p=0.01")
    ax2.axvline(0.05, color="orange", linestyle="--", linewidth=2, label="p=0.05")
    ax2.set_title(
        f"P-Hacked: SUSPICIOUS BUMP\nScore: {score_phack}/100 ({status_phack})",
        fontsize=12, fontweight="bold", color="red"
    )
    ax2.set_xlabel("p-value")
    ax2.set_ylabel("Frequency")
    ax2.legend()
    ax2.grid(alpha=0.3)
    ax2.text(
        0.025, max(ax2.get_ylim()) * 0.9,
        f"Risk Ratio: {summary_phack['risk_ratio']:.3f}",
        fontsize=10, bbox=dict(boxstyle="round", facecolor="lightcoral", alpha=0.8)
    )

    plt.suptitle("P-Curve Detection: Legitimate vs. P-Hacked", fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        fig.savefig(Path(save_path) / "figure1_comparison.png", dpi=150, bbox_inches="tight")
        print(f"    ✓ Saved: figure1_comparison.png")
    plt.show()
    plt.close()

    # Figure 2: Distribution shapes
    print("\n[4] Creating Figure 2: Distribution Shapes...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(legitimate, bins=10, color="green", alpha=0.7, edgecolor="black", linewidth=1.5)
    ax1.axvspan(0.0, 0.01, alpha=0.2, color="blue", label="Highly Sig (p≤0.01)")
    ax1.axvspan(0.04, 0.05, alpha=0.2, color="red", label="Risky (0.04-0.05)")
    ax1.set_title("Legitimate: RIGHT-SKEWED\n(Natural decline)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("p-value")
    ax1.set_ylabel("Count")
    ax1.legend()
    ax1.grid(alpha=0.3, axis="y")

    ax2.hist(phacked, bins=10, color="red", alpha=0.7, edgecolor="black", linewidth=1.5)
    ax2.axvspan(0.0, 0.01, alpha=0.2, color="blue", label="Highly Sig (p≤0.01)")
    ax2.axvspan(0.04, 0.05, alpha=0.2, color="red", label="Risky (0.04-0.05)")
    ax2.set_title("P-Hacked: INVERTED BUMP\n(Artificial clustering)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("p-value")
    ax2.set_ylabel("Count")
    ax2.legend()
    ax2.grid(alpha=0.3, axis="y")

    plt.suptitle("Mathematical Signature of Data Integrity", fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        fig.savefig(Path(save_path) / "figure2_shapes.png", dpi=150, bbox_inches="tight")
        print(f"    ✓ Saved: figure2_shapes.png")
    plt.show()
    plt.close()

    # Figure 3: Score mapping
    print("\n[5] Creating Figure 3: Risk Ratio → Score Mapping...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    scenarios = ["Legitimate\n(Right-Skew)", "Borderline", "P-Hacked\n(Bump)"]
    risk_ratios = [0.1, 1.0, 5.0]
    scores = [int(100 / (1 + r)) for r in risk_ratios]
    colors = ["green", "yellow", "red"]

    ax1.bar(scenarios, risk_ratios, color=colors, alpha=0.7, edgecolor="black", linewidth=2)
    ax1.set_ylabel("Risk Ratio", fontsize=11, fontweight="bold")
    ax1.set_title("Risk Ratio: Diagnostic for P-Hacking", fontsize=12, fontweight="bold")
    ax1.axhline(y=1.0, color="orange", linestyle="--", linewidth=2, label="Threshold")
    ax1.legend()
    ax1.grid(alpha=0.3, axis="y")

    ax2.bar(scenarios, scores, color=colors, alpha=0.7, edgecolor="black", linewidth=2)
    ax2.set_ylabel("Integrity Score (0–100)", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, 110)
    ax2.set_title("Integrity Score: 100 / (1 + Risk Ratio)", fontsize=12, fontweight="bold")
    ax2.axhline(y=70, color="green", linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.axhline(y=40, color="red", linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.grid(alpha=0.3, axis="y")

    plt.suptitle("Scoring Formula Visualization", fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        fig.savefig(Path(save_path) / "figure3_scoring.png", dpi=150, bbox_inches="tight")
        print(f"    ✓ Saved: figure3_scoring.png")
    plt.show()
    plt.close()

    print("\n" + "=" * 80)
    if save_path:
        print(f"Visualizations saved to: {save_path}")
    print("=" * 80)

    # Verify mathematical property
    assert score_legit > score_phack, (
        f"Legitimate ({score_legit}) should score higher than p-hacked ({score_phack})"
    )


def test_visualization_comprehensive():
    """Generate and validate comprehensive p-curve visualizations.

    This test creates 3 publication-quality figures demonstrating:
    1. Side-by-side legitimate vs. p-hacked histograms
    2. Distribution shapes highlighting risk regions
    3. Risk ratio to integrity score mapping
    
    No files are saved unless explicitly passed a save_path.
    """
    visualize_comparison()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

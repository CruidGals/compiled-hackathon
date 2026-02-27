import pytest

from stats import analyze_p_values, summarize_p_values


def test_analyze_with_balanced_risky_and_highsig():
    sample = [0.005, 0.009, 0.03, 0.045, 0.049]
    score, status = analyze_p_values(sample)
    assert score == 50
    assert status == "Moderate Risk"


def test_analyze_with_no_risky_or_highsig():
    sample = [0.02, 0.03]
    score, status = analyze_p_values(sample)
    assert score == 100
    assert status == "Likely Reliable"


def test_analyze_empty():
    score, status = analyze_p_values([])
    assert score == 100
    assert status == "No p-values in 0-0.05"


def test_summarize_returns_counts():
    sample = [0.005, 0.049, 0.03]
    s = summarize_p_values(sample)
    assert s["filtered_count"] == 3
    assert s["risky_count"] == 1
    assert s["high_sig_count"] == 1

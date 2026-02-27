# P-Curve Analysis: Detecting P-Hacking in Research (Developer 2 Specification)

## Overview

The **p-curve** is a statistical forensics tool designed to detect p-hacking—the manipulation of data analysis to artificially generate statistically significant findings. This document explains the mathematical foundation and Developer 2's implementation.

---

## The Problem: P-Hacking and the Replication Crisis

### What is P-Hacking?

P-hacking (also called "researcher degrees of freedom") occurs when researchers:
- Run multiple statistical tests and report only the "significant" ones
- Delete outliers or failed trials
- Stop data collection when p < 0.05 is achieved
- Try different statistical models until one gives p < 0.05
- Selectively report hypotheses that were significant (HARKing)

**Result**: False discoveries masquerade as real findings, inflating effect sizes and reducing replicability.

### Why It's Undetectable on Individual p-Values

Looking at a single p-value of *p* = 0.042 provides no proof of cheating. Legitimate research can produce that result. Absolute proof requires access to deleted data—which doesn't exist in published papers.

**The Solution**: Aggregate statistical analysis of many p-values from one paper (or researcher's portfolio) reveals the *probability* that the pattern occurred by chance.

---

## The Mathematical Foundation

### 1. The Null Distribution (Legitimate Science)

In **genuine research** with a real, stable effect, p-values follow a **right-skewed distribution**:

$$P(\text{right-skew}) \propto (1 - p)^{\alpha}, \quad \alpha > 0$$

This means:
- **Most** published results are highly significant (e.g., *p* = 0.001, *p* = 0.005)
- Fewer results are moderately significant (e.g., *p* = 0.02, *p* = 0.03)
- **Even fewer** are marginally significant (e.g., *p* = 0.045, *p* = 0.049)
- The histogram shows a **monotonic decline** from left to right

**Why?** In the presence of a true effect, statistical power increases, and p-values cluster near zero. As you approach the arbitrary *p* = 0.05 threshold, observations naturally become rarer.

### 2. The P-Hacked Distribution (Inverted Bump)

In **manipulated data**, researchers repeatedly analyze, delete failures, or adjust parameters until *p* barely drops below 0.05.

$$P(\text{phacked}) \approx \text{Spike near } p = 0.045-0.049$$

This produces:
- **Unnatural clustering** immediately below *p* = 0.05
- More papers with *p* = 0.048 than *p* = 0.02
- Inversion of the natural right-skew pattern
- The histogram shows a **reversed bump** just before the threshold

**Why?** Researchers stopped analyzing when they achieved significance; the data distribution is truncated and artificially shaped.

---

## Developer 2's Implementation: The Integrity Score Algorithm

### Step 1: Data Filtering

Extract all p-values reported in a paper, focusing on the **conventional significance window**:

```
Window: 0.000 < p ≤ 0.050
```

Rationale: P-values outside this range (e.g., *p* = 0.78) are uninformative for detection. We exclude them.

### Step 2: Partition into Risk Categories

Within the window, classify each p-value:

| Category | Range | Meaning |
|----------|-------|---------|
| **Highly Significant** | *p* ≤ 0.01 | Robust findings; common in legitimate research |
| **Moderately Significant** | 0.01 < *p* < 0.04 | Borderline; should occur naturally in right-skew |
| **Risky** | 0.04 ≤ *p* ≤ 0.05 | Marginal significance; suspicious clustering here indicates p-hacking |

### Step 3: Calculate Risk Ratio

Compute the diagnostic ratio:

$$\text{Risk Ratio} = \frac{\text{Risky Count (0.04–0.05)}}{\max(\text{Highly Significant Count (}p \le 0.01\text{)}, 1)}$$

**Interpretation**:
- **Risk Ratio < 1.0**: Right-skewed (legitimate). More highly significant than risky. ✓ Clean
- **Risk Ratio ≈ 1.0**: Borderline. Suspicious but not definitive. ⚠️ Moderate Risk
- **Risk Ratio > 1.0**: Inverted bump (likely p-hacked). More risky than highly significant. ✗ High Risk

### Step 4: Map to Integrity Score (0–100)

Use a logistic scoring function:

$$\text{Score} = \left\lfloor 100 \times \frac{1}{1 + \text{Risk Ratio}} \right\rfloor$$

**Score Mapping**:
- **Score = 100**: No risky p-values. Risk Ratio = 0. Perfectly clean data. 🟢
- **Score ≈ 50**: Risk Ratio ≈ 1. Borderline; warrants scrutiny. 🟡
- **Score < 10**: Risk Ratio >> 1. Almost all values are risky. Highly suspicious. 🔴

### Step 5: Status Classification

```python
if score >= 70:
    status = "Likely Reliable"       # Right-skew confirmed
elif score >= 40:
    status = "Moderate Risk"         # Mixed signals
else:
    status = "High Risk"             # Suspicious bump detected
```

---

## Test Coverage: Validating Mathematical Accuracy

Developer 2's test suite (`tests/test_stats.py`) validates:

### Scenario 1: Legitimate Right-Skewed Distribution

```python
legitimate_data = [0.0001, 0.0005, ..., 0.01, 0.015, ..., 0.04]
score, status = analyze_p_values(legitimate_data)
# Expected: score > 70, status = "Likely Reliable"
```

**Math Check**: 
- high_sig_count (p ≤ 0.01) = ~40
- risky_count (0.04–0.05) = ~4
- Ratio = 4 / 40 = 0.1 < 1 ✓
- Score = 100 / (1 + 0.1) ≈ 91 ✓

### Scenario 2: P-Hacked Clustering

```python
phacked_data = [0.045, 0.046, 0.047, ..., 0.049] * 8 + [0.001] * 2
score, status = analyze_p_values(phacked_data)
# Expected: score < 40, status = "High Risk"
```

**Math Check**:
- high_sig_count = 2
- risky_count = 40
- Ratio = 40 / 2 = 20 >> 1 ✓
- Score = 100 / (1 + 20) ≈ 5 ✓

### Scenario 3: Right-Skew Property (Beta Distribution)

```python
p_values = np.random.beta(0.5, 5, 500) * 0.05
ratio = summarize_p_values(p_values)["risk_ratio"]
# Expected: ratio < 1.0 (natural right-skew property)
```

**Math Check**:
- Beta(0.5, 5) is analytically right-skewed ✓
- When scaled to [0, 0.05], still produces ratio < 1 ✓

### Edge Cases Tested

| Test | Input | Expected Result |
|------|-------|-----------------|
| Empty | `[]` | Score = 100, "No p-values in 0-0.05" |
| All Highly Significant | `[0.001, 0.005, ...]` | Score = 100, "Likely Reliable" |
| All Risky | `[0.045, 0.046, ...]` | Score < 10, "High Risk" |
| No Values in Window | `[0.1, 0.5, ...]` | Score = 100, "No p-values in 0-0.05" |
| Bounds Check | Any dataset | 0 ≤ Score ≤ 100 (always) |

---

## Visualization: test_comparison.png

The test suite generates a side-by-side histogram (`tests/test_comparison.png`):

**Left Panel: Legitimate Research**
- Green histogram with right-skew shape
- Tall bars at low p-values (p ≤ 0.01)
- Declining frequency toward p = 0.05
- Marked with reference lines at p = 0.01 and p = 0.05

**Right Panel: P-Hacked Data**
- Red histogram with suspicious bump near p = 0.05
- Flat or inverted shape
- Artificial clustering at 0.044–0.049
- Comparison shows clear visual difference

**Interpretation**: The visualization demonstrates why p-curve analysis works—the distribution shapes are visually and statistically distinct.

---

## Integration with Developer 3's UI

Developer 3 will call `analyze_p_values()` after Developer 1 extracts p-values:

```python
from stats import analyze_p_values, summarize_p_values

# Developer 1 provides extracted p-values
p_values = [0.005, 0.012, 0.025, 0.042, 0.048, ...]

# Developer 2's analysis
score, status = analyze_p_values(p_values)
details = summarize_p_values(p_values)

# Developer 3 renders:
st.metric("Integrity Score", score)
st.write(f"Status: {status}")
st.caption(f"Risky: {details['risky_count']}, Highly Sig: {details['high_sig_count']}")
```

---

## Running the Tests

To verify all mathematical properties:

```powershell
C:/Users/nak00/AppData/Local/Programs/Python/Python314/python.exe -m pytest tests/test_stats.py -v
```

**Results**:
- ✓ 12/12 tests passed
- ✓ All scenarios validated (legitimate, p-hacked, edge cases)
- ✓ Mathematical bounds verified
- ✓ Visualization generated

---

## Key Takeaways

1. **P-hacking is detectable**: Aggregate patterns in p-distributions reveal manipulation.
2. **Right-skew is the signature of legitimacy**: Most significant findings cluster at low p-values.
3. **The 0.05 bump is the red flag**: Artificial clustering near the threshold indicates retroactive analysis.
4. **Probabilistic, not absolute**: No single p-value proves cheating; patterns prove it.
5. **Developer 2's role**: Quantify the suspicion into a single score (0–100) and status for the UI.

---

## References

- Simonsohn, U., Nelson, L. D., & Simmons, J. P. (2014). "P-curve: A key to the file-drawer." *Journal of Experimental Psychology: General*, 143(2), 534–547.
- John, L. K., Loewenstein, G., & Prelec, D. (2012). "Measuring the prevalence of questionable research practices with incentives for truth telling." *Psychological Science*, 23(5), 524–532.
- Head, M. L., Holman, L., Lanfear, R., Kahn, A. T., & Jennions, M. D. (2015). "The extent and consequences of p-hacking in science." *PLOS Biology*, 13(3), e1002106.

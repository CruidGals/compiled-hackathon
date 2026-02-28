"""
Research Integrity Auditor — UI & Visualization (Module 3).
Placeholder implementations for get_p_values and analyze_integrity until other modules are ready.
"""

import hashlib
import random
import streamlit as st
import matplotlib.pyplot as plt


# ----- Placeholders (replace with miner.get_p_values and stats.analyze_integrity) -----

def get_p_values(file_bytes: bytes) -> list[float]:
    """Placeholder: returns deterministic fake p-values based on file content."""
    seed = int(hashlib.sha256(file_bytes).hexdigest()[:8], 16)
    rng = random.Random(seed)
    n = rng.randint(15, 45)
    # Mix of values in [0, 0.05] with a slight bump near 0.05 (p-hacking look) or more uniform
    values = []
    for _ in range(n):
        if rng.random() < 0.6:
            values.append(round(rng.uniform(0.001, 0.05), 4))
        else:
            values.append(round(rng.uniform(0.01, 0.049), 4))
    return sorted(values)


def analyze_integrity(p_values: list[float]) -> tuple[float, str]:
    """Placeholder: returns deterministic fake score and status from p-value list."""
    sig = [p for p in p_values if 0 <= p <= 0.05]
    if not sig:
        return 0.0, "No significant p-values"
    risky = sum(1 for p in sig if 0.04 <= p <= 0.05)
    highly_sig = sum(1 for p in sig if p <= 0.01)
    ratio = (risky / highly_sig) if highly_sig else 5.0
    score = max(0, min(100, round(100 - ratio * 18, 1)))
    if score >= 70:
        status = "Reliable"
    elif score >= 40:
        status = "Moderate Risk"
    else:
        status = "High Risk"
    return score, status


@st.dialog("About this p-value")
def show_pvalue_context():
    p = st.session_state.get("explain_pvalue")
    if p is None:
        st.write("No p-value selected.")
        if st.button("Close"):
            st.rerun()
        return
    st.markdown(f"**p = {p}**")
    st.write(
        "This is one of the reported p-values from the paper that falls below the conventional 0.05 significance threshold. "
        "It was extracted from the PDF (e.g. from a results section or table)."
    )
    st.markdown("**What does this value mean?**")
    if p <= 0.01:
        st.write(
            "This is a **highly significant** result (p ≤ 0.01). Strong evidence like this is what we expect in solid, "
            "replicable research. On its own, this value is not concerning."
        )
    elif p <= 0.04:
        st.write(
            "This is in the **moderate** range (0.01 < p ≤ 0.04). It is still conventionally significant and not suspicious "
            "by itself. Context matters: many values in this band can be normal."
        )
    else:
        st.write(
            "This value sits in the **risky band** (0.04 ≤ p ≤ 0.05)—right at the edge of significance. A lot of values "
            "clustered here can suggest p-hacking (e.g. analysts trying until they just cross 0.05). One such value is "
            "not proof, but it contributes to a suspicious pattern when the overall P-curve shows a bump near 0.05."
        )
    if st.button("Close", type="primary"):
        st.rerun()


# ----- UI -----

st.set_page_config(page_title="Research Integrity Auditor", layout="wide")

# Only show uploader when no file is in session (or we're not in "dashboard" mode)
if "audit_result" not in st.session_state:
    # Wider margins: constrain content to a centered column with gutters
    _margin_l, _center, _margin_r = st.columns([2, 8, 2])
    with _center:
        st.title("Research Integrity Auditor", text_alignment="center")
        st.caption("P-Curve analysis for detecting p-hacking in academic PDFs")
        st.markdown("---")

        uploaded = st.file_uploader(
            "Upload a PDF to run the audit",
            type=["pdf"],
            help="Drop an academic paper PDF here",
        )

        if uploaded is None:
            st.info("Upload a PDF to see the integrity dashboard.")
            st.stop()

        file_bytes = uploaded.read()
        file_name = uploaded.name

        p_values = get_p_values(file_bytes)
        sig_only = [p for p in p_values if 0 <= p <= 0.05]
        if not sig_only:
            sig_only = [round(random.Random(42).uniform(0.01, 0.05), 4) for _ in range(20)]
        score, status = analyze_integrity(p_values)

        st.session_state["audit_result"] = {
            "file_name": file_name,
            "p_values": p_values,
            "sig_only": sig_only,
            "score": score,
            "status": status,
        }
    st.rerun()

# ----- Metric dashboard (shown after upload) -----

_margin_l, _center, _margin_r = st.columns([1, 10, 1])

with _center:
    result = st.session_state["audit_result"]
    file_name = result["file_name"]
    sig_only = result["sig_only"]
    score = result["score"]
    status = result["status"]
    p_values = result["p_values"]

    # Top bar: paper name + option to upload another
    col_title, col_reset = st.columns([3, 1])
    with col_title:
        st.subheader(f"📄 {file_name}")
    with col_reset:
        if st.button("Upload another paper"):
            del st.session_state["audit_result"]
            st.rerun()

    st.markdown("---")
    st.markdown("#### Primary Metrics")

    # Primary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Integrity Score",
            f"{score:.1f}",
            delta="0–100 scale",
            help="Higher = more reliable; lower = higher p-hacking risk",
        )
    with col2:
        st.metric("Verdict", status, help="Overall integrity assessment")
    with col3:
        st.metric("P-values (significant)", len(sig_only), help="Count in range 0–0.05")
    with col4:
        st.metric("Total P-values", len(p_values), help="All extracted from document")

    st.markdown("---")
    st.markdown("#### P-Curve")

    # Histogram: 5 bins from 0.00 to 0.05
    fig, ax = plt.subplots(figsize=(8, 3.5))
    bins = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
    ax.hist(sig_only, bins=bins, edgecolor="black", alpha=0.75)
    ax.set_xlabel("p-value")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of reported p-values (0.00 – 0.05)")
    ax.set_xlim(0, 0.05)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    with st.expander("View extracted p-values"):
        st.write(f"Total extracted: {len(p_values)} · In significant range (0–0.05): {len(sig_only)}. Click any value to explain it.")
        st.markdown(
            """
            <style>
            /* Same-size buttons, tighter grid */
            [data-testid="stExpander"] [data-testid="stVerticalBlock"] > div button {
                width: 5.5em !important; min-width: 5.5em !important; max-width: 5.5em !important;
                height: 2.25em !important; min-height: 2.25em !important;
                padding: 4px 8px !important; border-radius: 10px; font-family: monospace; font-size: 13px;
            }
            [data-testid="stExpander"] [data-testid="stVerticalBlock"] > div button:hover { border-color: #888 !important; }
            /* Tighter spacing between grid columns and rows */
            [data-testid="stExpander"] [data-testid="stHorizontalBlock"] { gap: 6px !important; }
            [data-testid="stExpander"] [data-testid="stVerticalBlock"] > div { padding-top: 2px !important; padding-bottom: 2px !important; }
            @media (prefers-color-scheme: dark) {
                [data-testid="stExpander"] [data-testid="stVerticalBlock"] > div button { background-color: #262730 !important; color: #fafafa !important; border-color: #4b5563 !important; }
                [data-testid="stExpander"] [data-testid="stVerticalBlock"] > div button:hover { background-color: #374151 !important; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        n_cols = 10
        for start in range(0, len(sig_only), n_cols):
            row_vals = sig_only[start : start + n_cols]
            cols = st.columns(n_cols)
            for c, (col, p) in enumerate(zip(cols, row_vals)):
                i = start + c
                with col:
                    if st.button(f"{p}", key=f"pval_{i}", help="Click to explain this p-value"):
                        st.session_state["explain_pvalue"] = p
                        show_pvalue_context()

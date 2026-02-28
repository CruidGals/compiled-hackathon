"""
Analyze a PDF paper: extract p-values (miner) and compute integrity score (stats).
Usage: python analyze_paper.py <path_to_pdf>
"""
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from miner import get_p_values
from stats import analyze_p_values, summarize_p_values


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_paper.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)
    if pdf_path.suffix.lower() != ".pdf":
        print("Error: expected a .pdf file")
        sys.exit(1)

    p_values = get_p_values(pdf_path)

    if not p_values:
        print(f"No p-values extracted from {pdf_path.name}")
        score, status = 100, "No p-values in 0-0.05"
    else:
        score, status = analyze_p_values(p_values)
        summary = summarize_p_values(p_values)
        print(f"Extracted {len(p_values)} p-value(s); in [0, 0.05] window: {summary['filtered_count']}")
        print(f"  Risky (0.04-0.05): {summary['risky_count']}, Highly sig (<=0.01): {summary['high_sig_count']}")
        print(f"  Risk ratio: {summary['risk_ratio']:.3f}")

    print(f"\nIntegrity score: {score}/100 - {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

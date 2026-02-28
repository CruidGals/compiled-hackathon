"""
Main entry point: run miner text extraction (PDF -> p-values) then the stats
pipeline (same logic validated in test_stats.py).
Usage: python main.py [path_to_pdf]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from miner import get_p_values
from stats import analyze_p_values, summarize_p_values


def run_pipeline(pdf_path: Path) -> int:
    """Extract p-values from PDF (miner) and run stats (analyze + summarize)."""
    if not pdf_path.exists():
        print(f"Error: file not found: {pdf_path}")
        return 1
    if pdf_path.suffix.lower() != ".pdf":
        print("Error: expected a .pdf file")
        return 1

    # 1. Miner: text extraction -> p-values (PDF opened inside miner)
    p_values = get_p_values(pdf_path)

    if not p_values:
        print(f"No p-values extracted from {pdf_path.name}")
        score, status = 100, "No p-values in 0-0.05"
    else:
        # 2. Stats: uses every detected p-value; score is based on [0, 0.05] (p-curve standard).
        score, status = analyze_p_values(p_values)
        summary = summarize_p_values(p_values)
        total = summary["total_count"]
        in_window = summary["filtered_count"]
        above = summary["count_above_005"]
        print(f"Using all {total} detected p-value(s): {in_window} in [0, 0.05] (for score), {above} above 0.05")
        print(f"  Risky (0.04-0.05): {summary['risky_count']}, Highly sig (<=0.01): {summary['high_sig_count']}")
        print(f"  Risk ratio: {summary['risk_ratio']:.3f}")

    print(f"\nIntegrity score: {score}/100 - {status}")
    return 0


def main():
    if len(sys.argv) >= 2:
        pdf_path = Path(sys.argv[1])
    else:
        # Default: use first available sample PDF in project
        for name in ("sample_paper.pdf", "sample_paper_2.pdf"):
            candidate = ROOT / name
            if candidate.exists():
                pdf_path = candidate
                print(f"Using default: {pdf_path.name}\n")
                break
        else:
            print("Usage: python main.py [path_to_pdf]")
            print("  No PDF path given and no sample_paper.pdf / sample_paper_2.pdf found.")
            return 1

    return run_pipeline(pdf_path)


if __name__ == "__main__":
    sys.exit(main())

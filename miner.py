import fitz  # PyMuPDF
import re
from pathlib import Path


def get_p_values(pdf_path):
    """
    Extracts numerical p-values from a PDF file using regex.
    pdf_path: path to the PDF file (str or pathlib.Path).
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    file_bytes = path.read_bytes()
    # Extract raw text from PDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    # Step 3: Apply Regex
    # Matches 'p', 'P', followed by optional space, then =, <, or >, then the number.
    # Captures: .05, 0.05, 0.001, etc.
    pattern = r'[pP]\s*[=<>]\s*(\d*\.?\d+)'
    matches = re.findall(pattern, full_text)
    
    # Step 4: Normalize results
    normalized_p_values = []
    for val in matches:
        try:
            # Ensure leading zero (e.g., convert ".05" to "0.05")
            p_float = float(val) if val.startswith('0') or '.' in val else float(f"0{val}")
            
            # Basic sanity check: p-values are rarely > 1.0
            if 0 <= p_float <= 1.0:
                normalized_p_values.append(p_float)
        except ValueError:
            continue
            
    return normalized_p_values

# --- LOCAL TESTING BLOCK ---
# --- TEST BLOCK ---
if __name__ == "__main__":
    pdf_path = "sample_paper.pdf"  # Make sure the file name matches exactly!

    try:
        results = get_p_values(pdf_path)
        print(f"--- Audit Results for {pdf_path} ---")
        print(f"Found {len(results)} total p-values.")
        print(f"Values: {results}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
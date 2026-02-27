import fitz  # PyMuPDF
import re

def get_p_values(file_bytes):
    """
    Extracts numerical p-values from a PDF byte stream using regex.
    """
    # Step 2: Extract raw text from PDF
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
    # 1. Create a "fake" paper string with various p-value formats
    fake_paper_text = """
    We found a significant effect (p=0.04). 
    The secondary analysis showed p < .001 and P = 0.05.
    However, the control group was not significant (p > 0.1).
    Some random text with a number like 123.45 should be ignored.
    """
    
    # 2. Manually run your regex (Step 3)
    import re
    pattern = r'[pP]\s*[=<>]\s*(\d*\.?\d+)'
    matches = re.findall(pattern, fake_paper_text)
    print(f"Regex Matches found: {matches}") 
    # EXPECTED: ['.04', '.001', '0.05', '0.1']

    # 3. Manually run your normalization (Step 4)
    normalized = [float(v) for v in matches if 0 <= float(v) <= 1]
    print(f"Normalized Floats: {normalized}")
    # EXPECTED: [0.04, 0.001, 0.05, 0.1]
Usage

Quick example showing `analyze_p_values()` from `stats.py`:

```python
from stats import analyze_p_values

sample = [0.005, 0.009, 0.03, 0.045, 0.049]
score, status = analyze_p_values(sample)
print(f"Integrity Score: {score}, Status: {status}")
```

Run the unit tests with:

```powershell
C:/Users/nak00/AppData/Local/Programs/Python/Python314/python.exe -m pytest -q
```

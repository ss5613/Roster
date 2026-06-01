"""Diagnostic: print out the actual structure of the Excel file."""
import pandas as pd
import os

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Shift draft (1).xlsx")
sheets = pd.read_excel(filepath, sheet_name=None, engine="openpyxl")

for name, df in sheets.items():
    print(f"\n{'='*60}")
    print(f"SHEET: '{name}'")
    print(f"Shape: {df.shape} (rows={df.shape[0]}, cols={df.shape[1]})")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"Column dtypes:\n{df.dtypes}")
    print(f"\nFirst 5 rows:")
    print(df.head(5).to_string())
    print(f"{'='*60}")

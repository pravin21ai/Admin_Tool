import pandas as pd

def parse_excel(file_path, sheet_name=0, dtype=None):
    try:
        # Read the excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=dtype)
        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")

def validate_mandatory_columns(df, mandatory_columns):
    missing = [col for col in mandatory_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing mandatory columns: {', '.join(missing)}")

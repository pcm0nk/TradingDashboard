import pandas as pd
import numpy as np


def clean_and_prepare_data(uploaded_file) -> pd.DataFrame:
    """
    Ingests raw file (CSV, Excel, or DataFrame) and standardizes formatting,
    types, and headers for the validation pipeline.
    """
    if uploaded_file is None:
        return pd.DataFrame()

    # 1. Ingest Raw Input (Handles DataFrame, UploadedFile, or string path)
    if isinstance(uploaded_file, pd.DataFrame):
        df = uploaded_file.copy()
    else:
        filename = getattr(uploaded_file, "name", str(uploaded_file))
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

    if df.empty:
        return pd.DataFrame()

    # 2. Column Mapping
    col_map = {
        'Futures': 'pair',
        'Symbol': 'pair',
        'Instrument': 'pair',
        'Direction': 'direction',
        'Side': 'direction',
        'Filled Price': 'price',
        'Price': 'price',
        'Filled Quantity': 'quantity',
        'Amount': 'quantity',
        'Qty': 'quantity',
        'Realized PNL': 'pnl',
        'PNL': 'pnl',
        'fees': 'fees',
        'Fee': 'fees',
        'Filled time(UTC)': 'fill_time',
        'Time': 'fill_time',
        'Date': 'fill_time'
    }
    
    rename_dict = {orig: col_map[orig] for orig in col_map if orig in df.columns}
    df = df.rename(columns=rename_dict).copy()

    # 3. Clean Numeric Formatting
    for col in ['quantity', 'price', 'pnl', 'fees']:
        if col in df.columns:
            cleaned = (
                df[col]
                .astype(str)
                .str.replace(',', '', regex=False)
                .str.replace('$', '', regex=False)
                .str.strip()
            )
            cleaned = cleaned.str.extract(r'(-?\d+\.?\d*(?:[eE]-?\d+)?)')[0]
            df[col] = pd.to_numeric(cleaned, errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0

    # 4. Standardize Direction String Formatting
    if 'direction' in df.columns:
        df['direction'] = df['direction'].astype(str).str.strip()

    # 5. Timestamp Conversion & Chronological Sorting
    if 'fill_time' in df.columns:
        df['fill_time'] = pd.to_datetime(
            df['fill_time'], utc=True, errors='coerce', format='mixed'
        )
        df = df.dropna(subset=['fill_time']).sort_values('fill_time').reset_index(drop=True)

    return df
import pandas as pd

def run_sanity_checks(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Executes raw execution log structural sanity and timestamp checks.
    
    Returns:
        dict: Test results containing status icons and descriptions.
        pd.DataFrame: Dataframe verified and chronologically sorted.
    """
    results = {}
    df_sorted = df.copy()

    # 1. Fill Timestamp Parsing & Chronological Ordering Check
    if 'fill_time' in df_sorted.columns:
        is_sorted = df_sorted['fill_time'].is_monotonic_increasing
        if not is_sorted:
            df_sorted = df_sorted.sort_values('fill_time').reset_index(drop=True)
        results['Timestamp Order'] = {
            'Passed': True,
            'Status': '✅ PASS' if is_sorted else 'ℹ️ AUTO-FIX',
            'Detail': 'Timestamps are in strict chronological order.' if is_sorted else 'Fills were re-sorted chronologically.'
        }

    # 2. Trade Direction String Validation
    valid_directions = {
        "Open Long", "Close Long", "Open Short", "Close Short",
        "OPEN_LONG", "CLOSE_LONG", "OPEN_SHORT", "CLOSE_SHORT",
        "BURST_LIQUIDATE_LONG", "BURST_LIQUIDATE_SHORT",
        "OFFSET_LIQUIDATE_SHORT", "FORCE_LIQUIDATE_SHORT",
        "FORCE_LIQUIDATE_LONG", "OFFSET_LIQUIDATE_LONG"
    }
    actual_dirs = set(df_sorted['direction'].dropna().unique())
    invalid_dirs = actual_dirs - valid_directions

    results['Trade Direction Check'] = {
        'Passed': len(invalid_dirs) == 0,
        'Status': '✅ PASS' if len(invalid_dirs) == 0 else '⚠️ WARN',
        'Detail': f"Unrecognized directions: {invalid_dirs}" if invalid_dirs else f"All fill directions verified ({len(actual_dirs)} types)."
    }

    # 3. Quantity Sanity Checks
    bad_qty = (df_sorted['quantity'] <= 0).sum()
    results['Quantity Sanity Check'] = {
        'Passed': bad_qty == 0,
        'Status': '✅ PASS' if bad_qty == 0 else '🚨 FAIL',
        'Detail': 'All execution quantities strictly positive.' if bad_qty == 0 else f"Found {bad_qty:,} zero or negative quantity rows."
    }

    # 4. Price Sanity Checks
    bad_price = (df_sorted['price'] <= 0).sum()
    results['Price Sanity Check'] = {
        'Passed': bad_price == 0,
        'Status': '✅ PASS' if bad_price == 0 else '🚨 FAIL',
        'Detail': 'All execution prices strictly positive.' if bad_price == 0 else f"Found {bad_price:,} zero or negative price rows."
    }

    # 5. Open/Close Fill Count Pairing Audit
    open_mask = df_sorted['direction'].str.contains('Open|OPEN', case=False, na=False)
    close_mask = df_sorted['direction'].str.contains('Close|CLOSE|LIQUIDATE', case=False, na=False)

    open_counts = df_sorted[open_mask].groupby('pair').size()
    close_counts = df_sorted[close_mask].groupby('pair').size()

    imbalances = {}
    all_pairs = set(open_counts.index) | set(close_counts.index)
    for p in all_pairs:
        o_cnt = open_counts.get(p, 0)
        c_cnt = close_counts.get(p, 0)
        if o_cnt != c_cnt:
            imbalances[p] = f"Open fills: {o_cnt}, Close fills: {c_cnt}"

    results['Fill Balance Pre-Audit'] = {
        'Passed': len(imbalances) == 0,
        'Status': '✅ PASS' if len(imbalances) == 0 else 'ℹ️ INFO',
        'Detail': 'Open and Close fill counts match per pair.' if not imbalances else f"Unbalanced pairs: {imbalances}"
    }

    return results, df_sorted
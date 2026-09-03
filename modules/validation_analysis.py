import streamlit as st
import pandas as pd

from validation.data_prep import clean_and_prepare_data
from validation.sanity_checks import run_sanity_checks
from validation.fifo_engine import process_fifo_trades

def run_validation_phase(uploaded_file):
    """
    Executes Phase 1: Data Preparation, Structural Sanity Checks, 
    and FIFO Order Matching.
    """
    # 1. Load Raw File and Standardize Schema
    raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df = clean_and_prepare_data(raw_df)

    start_dt = df['fill_time'].min().strftime('%Y-%m-%d %H:%M UTC')
    end_dt = df['fill_time'].max().strftime('%Y-%m-%d %H:%M UTC')

    st.subheader("Phase 1: Validation & FIFO Reconstruction")
    st.caption(f"**Execution Window:** {start_dt} to {end_dt} | **Total Raw Fills:** {len(df):,}")

    # 2. Run Sanity Checks BEFORE FIFO Processing
    st.markdown("### 1. Pre-FIFO Raw Execution Sanity Checks")
    sanity_results, df_sorted = run_sanity_checks(df)

    sanity_table = []
    for test_name, res in sanity_results.items():
        sanity_table.append({
            "Validation Check": test_name,
            "Status": res['Status'],
            "Audit Detail": res['Detail']
        })

    st.dataframe(pd.DataFrame(sanity_table), use_container_width=True)

    # 3. Pass Clean Fills to FIFO Engine
    st.markdown("### 2. FIFO Order Reconstruction & Position Audit")
    clean_trades_df, anomalies_df = process_fifo_trades(df_sorted)

    # Separate FIFO Orphans
    orphan_opens = anomalies_df[anomalies_df['anomaly_type'].str.contains('Open', case=False, na=False)] if not anomalies_df.empty else pd.DataFrame()
    orphan_closes = anomalies_df[anomalies_df['anomaly_type'].str.contains('Close', case=False, na=False)] if not anomalies_df.empty else pd.DataFrame()

    # Metrics Summary Bar
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("Raw Fills Ingested", f"{len(df_sorted):,}")
    mcol2.metric("Matched FIFO Trades", f"{len(clean_trades_df):,}")
    mcol3.metric("Open Position Inventory", f"{len(orphan_opens):,}")
    mcol4.metric("Unmatched Close Errors", f"{len(orphan_closes):,}", delta_color="inverse")

    # Display Anomalies Table if present
    if not anomalies_df.empty:
        st.markdown("#### FIFO Audit Inventory & Execution Anomalies")
        st.dataframe(anomalies_df, use_container_width=True)

    # Metadata pipeline handoff to Phase 2 (Trade Analysis)
    all_sanity_passed = all(res['Passed'] for res in sanity_results.values())
    has_no_close_errors = len(orphan_closes) == 0

    meta = {
        'passed': all_sanity_passed and has_no_close_errors,
        'total_fills': len(df_sorted),
        'matched_trades': len(clean_trades_df),
        'open_positions': len(orphan_opens),
        'unmatched_errors': len(orphan_closes)
    }

    return meta, clean_trades_df
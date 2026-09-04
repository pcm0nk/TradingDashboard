import streamlit as st
import pandas as pd

from validation.data_prep import clean_and_prepare_data
from validation.sanity_checks import run_sanity_checks
from validation.fifo_engine import process_fifo_trades

def run_validation_phase(uploaded_file):
    """
    Executes Phase 1: Data Preparation, Structural Sanity Checks, 
    and FIFO Order Matching & Position Consolidation.
    """
    # 1. Load Raw File and Standardize Schema
    if isinstance(uploaded_file, str):
        file_name = uploaded_file
    else:
        file_name = uploaded_file.name

    # Load CSV or Excel based on file extension
    if file_name.lower().endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)
        
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

    # 3. Pass Clean Fills to FIFO Engine (Receives raw fragments, consolidated positions, anomalies)
    st.markdown("### 2. FIFO Order Reconstruction & Position Audit")
    clean_trades_df, consolidated_trades_df, anomalies_df = process_fifo_trades(df_sorted)

    # Separate FIFO Orphans
    orphan_opens = anomalies_df[anomalies_df['anomaly_type'].str.contains('Open', case=False, na=False)] if not anomalies_df.empty else pd.DataFrame()
    orphan_closes = anomalies_df[anomalies_df['anomaly_type'].str.contains('Close', case=False, na=False)] if not anomalies_df.empty else pd.DataFrame()

    # Metrics Summary Bar
    mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
    mcol1.metric("Raw Fills Ingested", f"{len(df_sorted):,}")
    mcol2.metric("Matched Execution Fragments", f"{len(clean_trades_df):,}")
    mcol3.metric("Consolidated Positions", f"{len(consolidated_trades_df):,}")
    mcol4.metric("Open Position Inventory", f"{len(orphan_opens):,}")
    mcol5.metric("Unmatched Close Errors", f"{len(orphan_closes):,}", delta_color="inverse")

    # Download Button for Consolidated Positions CSV
    if not consolidated_trades_df.empty:
        csv_data = consolidated_trades_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Consolidated Positions (CSV)",
            data=csv_data,
            file_name="consolidated_fifo_positions.csv",
            mime="text/csv",
            help="Download the consolidated position dataset where partial entries and scaled exits are merged into single unified trade lifecycles."
        )

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
        'consolidated_positions': len(consolidated_trades_df),
        'open_positions': len(orphan_opens),
        'unmatched_errors': len(orphan_closes)
    }

    # Pass consolidated positions to Phase 2 so Session Transitions/Trade Analysis use full trades
    return meta, consolidated_trades_df
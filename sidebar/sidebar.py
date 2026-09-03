import streamlit as st
import pandas as pd

def render_sidebar():
    """
    Renders the Streamlit sidebar containing file uploads and capital/segment controls.
    Keeps table empty until trades pass validation analysis, then populates Row 1.
    """
    st.sidebar.title("⚡ Control Panel")
    uploaded_file = st.sidebar.file_uploader("Upload Exchange CSV / Excel", type=['csv', 'xlsx'])

    # 1. Reset state when a new file is uploaded
    if uploaded_file is not None:
        if st.session_state.get("last_uploaded_filename") != uploaded_file.name:
            st.session_state.validation_meta = None
            st.session_state.diag_results = None
            st.session_state.clean_trades_df = None
            st.session_state.anomalies_df = None
            st.session_state.full_trades_df = None
            st.session_state.analysis_ran = False
            if "deposit_ledger" in st.session_state:
                del st.session_state["deposit_ledger"]
            st.session_state.last_uploaded_filename = uploaded_file.name

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Capital and Segment Control")

    clean_df = st.session_state.get("clean_trades_df")

    # 2. Keep ledger empty until clean trades are generated from Validation Analysis
    if clean_df is None or clean_df.empty:
        st.session_state.deposit_ledger = pd.DataFrame(columns=["Type", "Date", "Amount ($)"])
        st.sidebar.info("⏳ Complete Validation Analysis to enable segment controls.")
    else:
        # Extract earliest trade date from clean trades
        date_col = next((c for c in ['Open Time', 'open_time', 'exit_time', 'time'] if c in clean_df.columns), None)
        if date_col:
            earliest_dt = pd.to_datetime(clean_df[date_col]).min()
            earliest_dt_str = earliest_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            earliest_dt_str = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

        # Auto-initialize Row 1 once clean trades exist
        if st.session_state.deposit_ledger.empty:
            st.session_state.deposit_ledger = pd.DataFrame([
                {"Type": "Deposit", "Date": earliest_dt_str, "Amount ($)": 10.0}
            ])

    st.sidebar.caption("Row 1 sets baseline starting capital & date. Row 2+ triggers top-up segments:")

    # 3. Render interactive data editor
    edited_ledger = st.sidebar.data_editor(
        st.session_state.deposit_ledger,
        num_rows="dynamic",
        column_config={
            "Type": st.column_config.SelectboxColumn(
                "Type",
                options=["Deposit"],
                default="Deposit",
                required=True
            ),
            "Date": st.column_config.TextColumn(
                "Date",
                help="Row 1 = Baseline Start Date. Row 2+ = Top-up Dates (YYYY-MM-DD HH:MM:SS)",
                required=True
            ),
            "Amount ($)": st.column_config.NumberColumn(
                "Amount ($)",
                min_value=0.0,
                format="$%.2f",
                required=True
            )
        },
        use_container_width=True,
        key="capital_ledger_editor"
    )

    return uploaded_file, edited_ledger
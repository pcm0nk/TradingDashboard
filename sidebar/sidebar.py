import os
import streamlit as st
import pandas as pd
from sidebar.how_it_works import render_how_it_works_button

# Paths to dummy data files sitting at project root alongside app.py
STANDARD_DUMMY_PATH = "dummydata.csv"
BLOWN_DUMMY_PATH = "blownaccount_dummydata.csv"

def render_sidebar():
    """
    Renders the Streamlit sidebar containing file uploads, walkthrough modal trigger,
    and capital/segment controls.
    """
    st.sidebar.title("⚡ Control Panel")
    
    # ── 0. WALKTHROUGH & DOCUMENTATION TRIGGER ──────────────────────────────────
    render_how_it_works_button()
    st.sidebar.markdown("---")

    # ── 1. SAMPLE DATA SELECTION ────────────────────────────────────────────────
    sample_option = st.sidebar.selectbox(
        "Sample Data Option",
        options=["None (Select Sample File)", "Standard Dummy Data", "Blown Account Dummy Data"],
        index=0
    )

    uploaded_file = None

    if sample_option == "Standard Dummy Data":
        if os.path.exists(STANDARD_DUMMY_PATH):
            uploaded_file = STANDARD_DUMMY_PATH
            st.sidebar.success("Loaded `dummydata.csv`.")
        else:
            st.sidebar.error(f"File not found: `{STANDARD_DUMMY_PATH}`")

    elif sample_option == "Blown Account Dummy Data":
        if os.path.exists(BLOWN_DUMMY_PATH):
            uploaded_file = BLOWN_DUMMY_PATH
            st.sidebar.warning("Loaded `blownaccount_dummydata.csv`.")
        else:
            st.sidebar.error(f"File not found: `{BLOWN_DUMMY_PATH}`")

    else:
        uploaded_file = st.sidebar.file_uploader("Upload Exchange CSV / Excel", type=['csv', 'xlsx'])

    # 2. Reset state when a new file or sample dataset is selected
    if isinstance(uploaded_file, str):
        current_filename = uploaded_file
    elif uploaded_file is not None:
        current_filename = uploaded_file.name
    else:
        current_filename = None
    
    if current_filename is not None:
        if st.session_state.get("last_uploaded_filename") != current_filename:
            st.session_state.validation_meta = None
            st.session_state.diag_results = None
            st.session_state.clean_trades_df = None
            st.session_state.anomalies_df = None
            st.session_state.full_trades_df = None
            st.session_state.analysis_ran = False
            if "deposit_ledger" in st.session_state:
                del st.session_state["deposit_ledger"]
            st.session_state.last_uploaded_filename = current_filename

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Capital and Segment Control")

    clean_df = st.session_state.get("clean_trades_df")

    # 3. Keep ledger empty until clean trades are generated from Validation Analysis
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

        # Auto-initialize ledger once clean trades exist
        if st.session_state.get("deposit_ledger") is None or st.session_state.deposit_ledger.empty:
            initial_deposit_row = {"Type": "Deposit", "Date": earliest_dt_str, "Amount ($)": 10.0}
            
            # If Blown Account sample data is selected, append the second $10 top-up at 2026-04-17
            if sample_option == "Blown Account Dummy Data":
                second_deposit_row = {"Type": "Deposit", "Date": "2026-04-17 13:13:13", "Amount ($)": 10.0}
                st.session_state.deposit_ledger = pd.DataFrame([initial_deposit_row, second_deposit_row])
            else:
                st.session_state.deposit_ledger = pd.DataFrame([initial_deposit_row])

    st.sidebar.caption("Row 1 sets baseline starting capital & date. Row 2+ triggers top-up segments:")

    # 4. Render interactive data editor
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

    # ── 5. DATE RANGE VALIDATION ────────────────────────────────────────────────
    trades_df = st.session_state.get("clean_trades_df", st.session_state.get("full_trades_df"))

    if trades_df is not None and not trades_df.empty and edited_ledger is not None and not edited_ledger.empty:
        time_cols = [c for c in ['Open Time', 'open_time', 'exit_time', 'close_time', 'time'] if c in trades_df.columns]
        
        if time_cols:
            # Extract dataset boundaries
            all_times = pd.concat([pd.to_datetime(trades_df[col]) for col in time_cols]).dropna()
            if not all_times.empty:
                min_trade_dt = all_times.min()
                max_trade_dt = all_times.max()

                out_of_bounds_entries = []

                for idx, row in edited_ledger.iterrows():
                    raw_date = row.get("Date")
                    if pd.isna(raw_date) or not str(raw_date).strip():
                        continue

                    try:
                        dep_dt = pd.to_datetime(raw_date)
                        
                        # Handle timezone alignment if necessary
                        if dep_dt.tzinfo is not None and min_trade_dt.tzinfo is None:
                            dep_dt = dep_dt.tz_localize(None)
                        elif dep_dt.tzinfo is None and min_trade_dt.tzinfo is not None:
                            dep_dt = dep_dt.tz_localize(min_trade_dt.tzinfo)

                        if dep_dt < min_trade_dt or dep_dt > max_trade_dt:
                            out_of_bounds_entries.append(f"Row {idx + 1}: `{raw_date}`")
                    except Exception:
                        continue

                # Display warning directly beneath the ledger table if any date is out of range
                if out_of_bounds_entries:
                    min_str = min_trade_dt.strftime("%Y-%m-%d %H:%M:%S")
                    max_str = max_trade_dt.strftime("%Y-%m-%d %H:%M:%S")

                    st.sidebar.error(
                        f"⚠️ **Deposit Date Out of Range!**\n\n"
                        f"The trade dataset ranges from **{min_str}** to **{max_str}**.\n\n"
                        f"The following deposit dates fall outside this range:\n"
                        + "\n".join([f"- {item}" for item in out_of_bounds_entries])
                    )

    return uploaded_file, edited_ledger
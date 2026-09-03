import os
import pandas as pd
import streamlit as st

# Path to standard dummy dataset at root
STANDARD_DUMMY_PATH = "dummydata.csv"

def show_how_it_works_dialog():
    """
    Renders the modal dialog explaining dashboard features, dataset choices,
    accepted direction variants, sample downloads, capital control, validation, and analytics tabs.
    """
    @st.dialog("📖 Dashboard Walkthrough & Documentation", width="large")
    def _render_dialog():
        st.markdown("Welcome to the **Quantitative Trading & Diagnostic Suite**! This guide explains data formatting, accepted directions, sample downloads, and system usage.")

        st.markdown("---")

        # Tabbed view inside the modal
        doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
            "📂 1. Data Requirements",
            "💰 2. Capital Control",
            "🛡️ 3. Section 1: Validation",
            "📈 4. Section 2: Trading Analysis"
        ])

        with doc_tab1:
            st.markdown("### 📂 Data Ingestion & Accepted Schema")
            st.markdown("Custom CSV/Excel logs (`.csv`, `.xlsx`) must align with the core schema below:")

            # Restored Schema Table with dedicated Open/Close Direction rows
            schema_data = {
                "Column Name": [
                    "Open Time", 
                    "Close Time", 
                    "Symbol / Pair", 
                    "Open Direction", 
                    "Close Direction", 
                    "Price", 
                    "Qty / Size", 
                    "Fee"
                ],
                "Accepted Variants": [
                    "Open Time, open_time, Time, datetime",
                    "Close Time, close_time, exit_time",
                    "Symbol, Pair, symbol, pair, Instrument",
                    "OPEN_LONG, OPEN_SHORT, BUY, LONG, Open Long, Open Short",
                    "CLOSE_LONG, CLOSE_SHORT, CLOSE LONG, CLOSE SHORT, SELL, SHORT, Close Long, Close Short, BURST_LIQUIDATE_LONG, BURST_LIQUIDATE_SHORT, OFFSET_LIQUIDATE_SHORT, FORCE_LIQUIDATE_SHORT, FORCE_LIQUIDATE_LONG, OFFSET_LIQUIDATE_LONG",
                    "Price, price, Executed Price",
                    "Qty, Size, Quantity, Amount, Volume",
                    "Fee, Fees, Commission, fee_amount"
                ],
                "Example": [
                    "2026-04-10 14:30:00",
                    "2026-04-10 15:45:00",
                    "BTCUSDT",
                    "OPEN_LONG",
                    "CLOSE_LONG",
                    "65400.50",
                    "0.15",
                    "0.0025"
                ]
            }
            st.table(pd.DataFrame(schema_data))

            st.markdown("---")
            
            # Inline Download Section
            dl_col1, dl_col2 = st.columns([2, 1], vertical_alignment="center")

            with dl_col1:
                st.markdown("**Download sample template for formatting reference:**")

            with dl_col2:
                if os.path.exists(STANDARD_DUMMY_PATH):
                    with open(STANDARD_DUMMY_PATH, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Sample Template CSV",
                            data=file,
                            file_name="sample_trading_log_template.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.caption("⚠️ `dummydata.csv` missing at root.")

        with doc_tab2:
            st.markdown("### 💰 Capital & Segment Control Ledger")
            st.markdown("""
            The interactive ledger in the sidebar manages portfolio equity and capital injections:
            
            * **Row 1 (Baseline Starting Capital):** Auto-set to the earliest trade date with a $10 baseline.
            * **Row 2+ (Top-Ups):** Add rows to simulate capital injections (e.g., $10 on `2026-04-17`), creating new analysis **Segments**.
            * **Active Segment Selector:** Defaults to **"All Segments Combined View"** for overall lifecycle analysis.
            """)

        with doc_tab3:
            st.markdown("### 🛡️ Section 1: Validation Analysis Phase")
            st.markdown("""
            Multi-stage data integrity validation before performance analytics:
            
            * **Schema Verification:** Standardizes columns (`Open Time`, `Close Time`, `Pair`, `Directions`, `Price`, `Qty`, `Fees`).
            * **FIFO Engine:** Matches entries and exits chronologically.
            * **Orphan Detection:** Isolates **Orphan Closes** (missing entries) and **Orphan Opens** (unclosed inventory).
            """)

        with doc_tab4:
            st.markdown("### 📈 Section 2: Trading Analysis Engine")
            st.markdown("""
            * **📊 Executive Summary:** High-level metrics—Net Realized PnL, Win Rate, Profit Factor, Open/Close Fees, Equity Curves, and Drawdown.
            * **🎯 Pair Performance:** Per-pair vs. total performance breakdowns with PnL, fee analysis, and visual charts.
            * **⏰ Session Dynamics:** Trade count and win-rate distribution mapped across market sessions with visual charting.
            * **🔄 Session Transitions & Holds:** Tracks position entry/exit sessions, hold durations, and exit triggers (`TP`, `SL`, `Liquidation`).
            * **🔍 Audit & Trade Logs:** Detailed execution table featuring trade session tags and blown-account audit logging.
            * **⚙️ Session Settings & Risk:** Account parameters—Segment Start Capital, Ending Equity, Max Peak, Risk/Drawdown thresholds, and Max $/% Drawdown.
            """)

        st.markdown("---")
        if st.button("Close Walkthrough", use_container_width=True):
            st.rerun()

    _render_dialog()


def render_how_it_works_button():
    """
    Renders the sidebar button to trigger the walkthrough modal.
    """
    if st.sidebar.button("📖 How It Works", use_container_width=True):
        st.session_state.show_walkthrough_modal = True

    if st.session_state.get("show_walkthrough_modal", False):
        st.session_state.show_walkthrough_modal = False
        show_how_it_works_dialog()
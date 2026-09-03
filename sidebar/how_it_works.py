import streamlit as st

def show_how_it_works_dialog():
    """
    Renders the modal dialog explaining dashboard features, dataset choices,
    capital control ledger, validation phase, and trading analysis tabs.
    """
    @st.dialog("📖 Dashboard Walkthrough & Documentation", width="large")
    def _render_dialog():
        st.markdown("Welcome to the **Quantitative Trading & Diagnostic Suite**! This guide explains how data flows through the application and how to interpret each component.")

        st.markdown("---")

        # Tabbed view inside the modal for structured navigation
        doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
            "📂 1. Data Ingestion & Samples",
            "💰 2. Capital & Segment Control",
            "🛡️ 3. Section 1: Validation",
            "📈 4. Section 2: Trading Analysis"
        ])

        with doc_tab1:
            st.markdown("### 📂 Data Ingestion & Sample Datasets")
            st.markdown("""
            You can analyze custom exchange logs or test the platform using built-in datasets:
            
            1. **Upload Exchange File:**
               - Upload your own trade history in **CSV** or **Excel** format (`.csv`, `.xlsx`).
            2. **Standard Dummy Data (`dummydata.csv`):**
               - A clean, standard trading history covering multiple crypto assets with normal entry/exit dynamics.
            3. **Blown Account Dummy Data (`blownaccount_dummydata.csv`):**
               - Simulates a high-drawdown strategy that experiences account liquidation/blowout. Selecting this automatically loads a **2-segment top-up setup** in the Capital Control panel.
            """)

        with doc_tab2:
            st.markdown("### 💰 Capital & Segment Control Ledger")
            st.markdown("""
            The interactive ledger in the sidebar manages portfolio equity, initial baseline start dates, and capital injections across time:
            
            * **Row 1 (Baseline Starting Capital):**
              - Automatically populated with the earliest trade date found in your log and a default $10 baseline.
            * **Row 2+ (Top-Ups & Injections):**
              - Add rows to simulate capital injections (e.g., adding $10 on `2026-04-17`).
              - Each new deposit row establishes a new **Segment**, dividing trading metrics into isolated time windows.
            * **Active Segment Selector:**
              - Defaults to **"All Segments Combined View"** to analyze overall performance across the entire account lifecycle.
            """)

        with doc_tab3:
            st.markdown("### 🛡️ Section 1: Validation Analysis Phase")
            st.markdown("""
            Before trading metrics are calculated, raw execution logs undergo multi-stage data integrity validation:
            
            * **Schema Verification:** Standardizes columns (`Open Time`, `Close Time`, `Symbol/Pair`, `Side`, `Price`, `Qty`, `Fees`).
            * **FIFO Matching Engine:** Pairs entry executions with exit executions on a First-In-First-Out basis.
            * **Orphan Detection:** Isolates **Orphan Closes** (exits without recorded entries) and **Orphan Opens** (unclosed inventory) to protect PnL accuracy.
            """)

        with doc_tab4:
            st.markdown("### 📈 Section 2: Trading Analysis Engine")
            st.markdown("""
            Once trade logs pass validation, explore execution diagnostics across tabs:
            
            * **📊 Executive Summary:** High-level metrics including Net Realized PnL, Win Rate, Profit Factor, Open/Close Fees, Equity Curves, and Drawdown depth.
            * **🔍 Trade Analysis & Strategies:** Itemized matched trade details with hold durations, pair metrics, and exit triggers (`TP`, `SL`, `Liquidation`, `Breakeven`).
            * **⚠️ Anomalies & Diagnostics:** Logs and tracks missing data rows or unmapped fee logs for complete quantitative auditing.
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
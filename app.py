import pandas as pd
import streamlit as st

# Import custom analysis modules
from modules.ml_analysis import run_ml_analysis_phase
from modules.trade_analysis import run_trade_analysis_phase
from modules.validation_analysis import run_validation_phase

# Import sidebar & components
from sidebar.sidebar import render_sidebar
from components.contact_modal import show_contact_modal

# ── 1. PAGE CONFIGURATION & DARK QUANT THEME ──────────────────────────────────
st.set_page_config(
    page_title="Quant Diagnostic & Trading Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #F1C40F; }
    .stTable { background-color: #1E222D; }
    .stButton>button {
        background-color: #1F2937;
        color: #F1C40F;
        border: 1px solid #F1C40F;
        border-radius: 4px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #F1C40F;
        color: #0E1117;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── 2. SESSION STATE INITIALIZATION ───────────────────────────────────────────
if "analysis_ran" not in st.session_state:
    st.session_state.analysis_ran = False
if "full_trades_df" not in st.session_state:
    st.session_state.full_trades_df = None
if "validation_meta" not in st.session_state:
    st.session_state.validation_meta = None
if "diag_results" not in st.session_state:
    st.session_state.diag_results = None
if "last_uploaded_filename" not in st.session_state:
    st.session_state.last_uploaded_filename = None
if "show_walkthrough_modal" not in st.session_state:
    st.session_state.show_walkthrough_modal = False

# ── 3. RENDER SIDEBAR CONTROLS ────────────────────────────────────────────────
uploaded_file, ledger_df = render_sidebar()

# ── 4. HEADER WITH CONTACT DEVELOPER BUTTON ──────────────────────────────────
col_header, col_contact = st.columns([0.78, 0.22])

with col_header:
    st.markdown(
        "<h2 style='margin-bottom: 0px;'>🛡️ Quantitative Trading & Diagnostic"
        " Suite</h2>",
        unsafe_allow_html=True,
    )

with col_contact:
    st.write("")  # Spacing alignment
    if st.button("📩 Contact Developer", use_container_width=True):
        show_contact_modal()

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ── 5. MAIN APPLICATION FLOW ──────────────────────────────────────────────────
if uploaded_file is None:
    st.info(
        "👈 Upload your trade log file in the sidebar to initiate the pipeline."
    )
    st.session_state.analysis_ran = False
else:
    # Top-Level Navigation Tabs (Main Menu)
    menu_tab1, menu_tab2, menu_tab3 = st.tabs([
        "🛡️ Section 1: Validation Analysis",
        "📈 Section 2: Trading Analysis Engine",
        "🤖 Section 3: Machine Learning Engine",
    ])

    # Variable to capture the sliced active segment trades across tabs
    active_trades_df = None

    # ── MENU TAB 1: VALIDATION ANALYSIS ───────────────────────────────────────
    with menu_tab1:
        meta, clean_trades_df = run_validation_phase(uploaded_file)

        # Save clean trades and trigger a rerun if this is the first time clean_trades is created
        if clean_trades_df is not None:
            if st.session_state.get("clean_trades_df") is None:
                st.session_state.clean_trades_df = clean_trades_df
                st.rerun()  # Triggers sidebar to populate Row 1 date instantly!
            else:
                st.session_state.clean_trades_df = clean_trades_df

    # ── MENU TAB 2: TRADING ANALYSIS ──────────────────────────────────────────
    with menu_tab2:
        clean_trades = st.session_state.get("clean_trades_df")
        if clean_trades is not None and not clean_trades.empty:
            # Executes Section 2 and returns the active segment sliced trades dataframe
            res = run_trade_analysis_phase(clean_trades, meta, ledger_df)
            if res is not None and isinstance(res, tuple) and len(res) >= 1:
                active_trades_df = res[0]
            else:
                active_trades_df = clean_trades
        else:
            st.warning(
                "⚠️ No valid matched FIFO trades available for trading"
                " analysis."
            )

    # ── MENU TAB 3: MACHINE LEARNING ENGINE ───────────────────────────────────
    with menu_tab3:
        # Check if trade_analysis has stored an active segment slice; if not, fall back to clean_trades
        ml_trades = st.session_state.get(
            "active_segment_trades", st.session_state.get("clean_trades_df")
        )

        if ml_trades is not None and not ml_trades.empty:
            run_ml_analysis_phase(trades_df=ml_trades, ledger_df=ledger_df)
        else:
            st.warning(
                "⚠️ No valid trade records available in the active segment to"
                " execute Machine Learning analysis."
            )
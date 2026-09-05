import pandas as pd
import streamlit as st

from machinelearning.behavioral_diagnostics import render_behavioral_diagnostics_tab
from machinelearning.execution_clustering import render_execution_clustering_tab
from machinelearning.feature_drivers import render_feature_drivers_tab
from machinelearning.outcome_prediction import render_outcome_prediction_tab


def run_ml_analysis_phase(trades_df: pd.DataFrame, ledger_df: pd.DataFrame):
    """Executes Section 3: Machine Learning Diagnostic Engine."""
    st.markdown("## 🤖 Machine Learning Diagnostic Engine")

    ml_tab1, ml_tab2, ml_tab3 = st.tabs([
        "🎯 Outcome Prediction & Drivers",
        "🧬 Execution Style Clustering",
        "🧠 Behavioral Edge & Risk Diagnostics",
    ])

    with ml_tab1:
        # Load both components inside Tab 1
        render_outcome_prediction_tab(trades_df)
        st.markdown("---")
        render_feature_drivers_tab(trades_df)

    with ml_tab2:
        render_execution_clustering_tab(trades_df)

    with ml_tab3:
        render_behavioral_diagnostics_tab(trades_df)
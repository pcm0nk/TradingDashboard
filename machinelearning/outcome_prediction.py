import pandas as pd
import streamlit as st
from machinelearning.feature_engineering import extract_trade_features
from machinelearning.trade_classifier import train_trade_classifier


def get_model_results(trades_df: pd.DataFrame):
    """Helper function to extract features and train the classifier once."""
    if trades_df is None or trades_df.empty:
        return None, "empty"

    X, y = extract_trade_features(trades_df)

    if X.empty or len(X) < 10:
        return len(X), "insufficient_samples"

    results = train_trade_classifier(X, y)
    if results.get("status") != "success":
        return None, "cv_failed"

    return (X, y, results), "success"


def render_outcome_prediction_tab(trades_df: pd.DataFrame):
    """Renders Tab 1: Outcome Prediction Model Performance."""
    st.markdown(
        "Evaluates supervised model accuracy and target class distribution on"
        " the active segment."
    )

    data, status = get_model_results(trades_df)

    if status == "empty":
        st.warning(
            "⚠️ No trade records available in this active segment to train"
            " machine learning models."
        )
        return
    elif status == "insufficient_samples":
        st.info(
            f"ℹ️ The selected active segment has **{data}** trade sample(s)."
            " At least 10 completed position records are required to train the"
            " machine learning classifier."
        )
        return
    elif status == "cv_failed":
        st.warning(
            "Insufficient sample variance in this active segment to complete"
            " cross-validation."
        )
        return

    X, y, results = data

    # ── High-Level Metric Cards ───────────────────────────────────────────────
    st.subheader(
        "📈 Predictive Performance Metrics",
        help=(
            "Summary of cross-validated model precision, total feature parameters,"
            " evaluated trade sample count, and overall target class distribution."
        ),
    )
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    win_count = int(y.sum())
    loss_count = len(y) - win_count
    cv_acc = results["mean_cv_accuracy"] * 100

    m_col1.metric(
        "Time-Series CV Accuracy",
        f"{cv_acc:.1f}%",
        help=(
            "Cross-validated accuracy calculated using TimeSeriesSplit on this"
            " active segment."
        ),
    )
    m_col2.metric(
        "Total Features Evaluated",
        f"{X.shape[1]}",
        help="Number of extracted trade attributes for the active segment.",
    )
    m_col3.metric(
        "Segment Trade Samples",
        f"{len(X)}",
        help="Total closed trades evaluated within this active segment.",
    )
    m_col4.metric(
        "Target Balance (Win / Loss)",
        f"{win_count}W / {loss_count}L",
        help="Winning trades vs losing trades in the selected active segment.",
    )

    st.markdown("---")

    # ── Performance Verdict Banner ──────────────────────────────────────────
    st.subheader(
        "⚖️ Model Performance Verdict",
        help=(
            "Interprets overall cross-validation accuracy to categorize model"
            " predictive edge into Strong Pattern Signal, Moderate Edge, or High"
            " Noise / Random Walk."
        ),
    )
    if cv_acc >= 60.0:
        st.success(
            f"✅ **Strong Pattern Signal:** Achieving **{cv_acc:.1f}%** CV"
            " accuracy on this segment. The model has identified reliable"
            " predictive patterns."
        )
    elif cv_acc >= 50.0:
        st.info(
            f"ℹ️ **Moderate Edge:** Achieving **{cv_acc:.1f}%** CV accuracy on"
            " this segment. Moderate signal strength detected above random"
            " chance."
        )
    else:
        st.warning(
            f"⚠️ **High Noise / Random Walk:** Achieving **{cv_acc:.1f}%** CV"
            " accuracy on this segment. Market conditions or execution style in"
            " this segment show high randomness."
        )
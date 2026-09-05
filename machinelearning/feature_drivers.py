import pandas as pd
import streamlit as st
from machinelearning.outcome_prediction import get_model_results


def render_feature_drivers_tab(trades_df: pd.DataFrame):
    """Renders Tab 2: Predictive Feature Drivers & Factor Weight Distribution."""
    st.markdown("### 🔑 Predictive Feature Drivers")
    st.caption(
        "Isolates specific trade attributes (holding time, volume, session,"
        " direction) driving profitability."
    )

    data, status = get_model_results(trades_df)

    if status != "success":
        st.info("⚠️ Complete model requirements on Tab 1 to view feature drivers.")
        return

    X, y, results = data
    top_features = results["feature_importances"].head(10)

    # ── Feature Weight Chart ──────────────────────────────────────────────────
    st.markdown("#### 📊 Predictive Feature Weight Distribution")
    st.bar_chart(top_features, use_container_width=True)

    st.markdown("---")

    # ── Detailed Driver Ranking ───────────────────────────────────────────────
    st.markdown("#### 💡 Top Dominant Drivers Breakdown")
    top_3 = top_features.head(5)

    cols = st.columns(min(len(top_3), 3))
    for rank, (feat, weight) in enumerate(top_3.items(), start=1):
        formatted_feat = (
            feat.replace("_", " ").title().replace("Pair ", "Pair: ")
        )
        col_idx = (rank - 1) % len(cols)
        cols[col_idx].metric(
            label=f"Rank #{rank}: {formatted_feat}",
            value=f"{weight * 100:.2f}%",
            help="Relative predictive weight assigned by the Random Forest model.",
        )
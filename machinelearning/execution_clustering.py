import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def render_execution_clustering_tab(trades_df: pd.DataFrame):
    """Executes Unsupervised K-Means Clustering to group trades by execution style

    (Duration, Size, PnL).
    """
    st.markdown("### 🧬 Execution Style Clustering (Unsupervised ML)")
    st.caption(
        "Discovers structural trading archetypes by grouping trades with"
        " similar duration, position size, and profit profile."
    )

    # 1. Minimum Sample Check
    if trades_df is None or len(trades_df) < 10:
        st.warning(
            "⚠️ **Execution Style Clustering requires at least 10 completed"
            " positions.** "
            f"(Current sample size: {len(trades_df) if trades_df is not None else 0})"
        )
        return

    df = trades_df.copy()

    # 2. Derive Duration dynamically using available FIFO / Trade Analysis timestamp columns
    if "duration_min" not in df.columns:
        open_col = next(
            (
                c
                for c in [
                    "entry_time",
                    "open_time",
                    "Open Time",
                    "open_date",
                    "time",
                ]
                if c in df.columns
            ),
            None,
        )
        exit_col = next(
            (
                c
                for c in [
                    "exit_time",
                    "close_time",
                    "Close Time",
                    "close_date",
                ]
                if c in df.columns
            ),
            None,
        )

        if open_col and exit_col:
            df["duration_min"] = (
                pd.to_datetime(df[exit_col]) - pd.to_datetime(df[open_col])
            ).dt.total_seconds() / 60.0
        else:
            st.error(
                "⚠️ **Cannot perform clustering:** Missing timestamp columns to"
                " calculate hold duration."
            )
            return

    # 3. Resolve Volume/Size Column from FIFO matching / cleaning pipeline
    vol_col = next(
        (
            c
            for c in [
                "volume",
                "vol",
                "size",
                "lots",
                "Volume",
                "Size",
                "position_size",
                "qty",
                "quantity",
            ]
            if c in df.columns
        ),
        None,
    )

    # 4. Resolve PnL Column matching trade_analysis.py priority ('net_pnl' then 'pnl')
    pnl_col = next(
        (
            c
            for c in [
                "net_pnl",
                "pnl",
                "net_change",
                "PnL",
                "Profit",
                "net_profit",
            ]
            if c in df.columns
        ),
        None,
    )

    if not vol_col or not pnl_col:
        found_cols = list(df.columns)
        st.error(
            f"⚠️ **Cannot perform clustering:** Missing Volume or PnL columns.\n\n"
            f"**Detected DataFrame Columns:** `{found_cols}`"
        )
        return

    # Create numeric normalized features
    df["volume_feat"] = pd.to_numeric(df[vol_col], errors="coerce")
    df["pnl_feat"] = pd.to_numeric(df[pnl_col], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")

    # Select clean features for clustering
    clustering_df = df[["duration_min", "volume_feat", "pnl_feat"]].dropna()

    if len(clustering_df) < 10:
        st.warning(
            "⚠️ Not enough clean data rows with complete Duration, Volume, and"
            " PnL features."
        )
        return

    # 5. Normalize Features with StandardScaler
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(clustering_df)

    # Determine optimal number of clusters (K) based on dataset size
    n_samples = len(clustering_df)
    n_clusters = 3 if n_samples >= 20 else 2

    # 6. Train K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)
    clustering_df["Cluster"] = cluster_labels

    # Compute Silhouette Score (Quality Metric)
    sil_score = silhouette_score(scaled_features, cluster_labels)

    # 7. Map Clusters to Human-Readable Style Personas
    cluster_summary = (
        clustering_df.groupby("Cluster")
        .agg(
            Avg_Duration=("duration_min", "mean"),
            Avg_Volume=("volume_feat", "mean"),
            Avg_PnL=("pnl_feat", "mean"),
            Trade_Count=("pnl_feat", "count"),
        )
        .reset_index()
    )

    # Sort clusters by average duration to assign logical personas
    cluster_summary = cluster_summary.sort_values(
        "Avg_Duration"
    ).reset_index(drop=True)

    persona_names = {}
    if n_clusters == 2:
        persona_names[cluster_summary.loc[0, "Cluster"]] = (
            "⚡ Quick Scalps / Fast Execution"
        )
        persona_names[cluster_summary.loc[1, "Cluster"]] = (
            "⏳ Extended / Swing Holds"
        )
    else:
        persona_names[cluster_summary.loc[0, "Cluster"]] = "⚡ Fast Scalps"
        persona_names[cluster_summary.loc[1, "Cluster"]] = "⏱️ Day Trades"
        persona_names[cluster_summary.loc[2, "Cluster"]] = (
            "⏳ Extended / Swing Holds"
        )

    clustering_df["Style_Persona"] = clustering_df["Cluster"].map(
        persona_names
    )

    # ── RENDER RESULTS UI ──────────────────────────────────────────────────────
    col_metric1, col_metric2, col_metric3 = st.columns(3)

    col_metric1.metric(
        label="Identified Execution Styles", value=f"{n_clusters} Clusters"
    )
    col_metric2.metric(
        label="Clustering Quality (Silhouette)", value=f"{sil_score:.2f}"
    )

    quality_text = (
        "Strong Separation"
        if sil_score > 0.4
        else "Moderate Separation"
        if sil_score > 0.2
        else "Overlapping Styles"
    )
    col_metric3.metric(label="Cluster Separation", value=quality_text)

    # Scatter Plot Visualization
    st.markdown("#### 📊 Execution Style Mapping")
    fig = px.scatter(
        clustering_df,
        x="duration_min",
        y="pnl_feat",
        size="volume_feat",
        color="Style_Persona",
        hover_data=["duration_min", "volume_feat", "pnl_feat"],
        labels={
            "duration_min": "Hold Duration (Minutes)",
            "pnl_feat": "Net P&L ($)",
            "volume_feat": "Volume (Lots)",
            "Style_Persona": "Execution Style",
        },
        title="Trade Execution Profiles (Duration vs. P&L scaled by Lot Size)",
        template="plotly_dark",
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

    # Summary Breakdown Table
    st.markdown("#### 📋 Style Persona Breakdown")
    summary_display = (
        clustering_df.groupby("Style_Persona")
        .agg(
            Trades=("pnl_feat", "count"),
            Avg_Duration_Min=("duration_min", "mean"),
            Avg_Volume_Lots=("volume_feat", "mean"),
            Win_Rate=(
                "pnl_feat",
                lambda x: f"{(x > 0).sum() / len(x) * 100:.1f}%",
            ),
            Total_PnL=("pnl_feat", "sum"),
            Avg_PnL=("pnl_feat", "mean"),
        )
        .reset_index()
    )

    st.dataframe(
        summary_display.style.format(
            {
                "Avg_Duration_Min": "{:.1f} m",
                "Avg_Volume_Lots": "{:.2f} Lots",
                "Total_PnL": "${:,.2f}",
                "Avg_PnL": "${:,.2f}",
            }
        ),
        use_container_width=True,
    )
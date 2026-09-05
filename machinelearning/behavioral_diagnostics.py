import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from machinelearning.trade_classifier import resolve_trade_columns

# Global configuration to enable scroll zoom across all charts
PLOTLY_CONFIG = {
    'scrollZoom': True,
    'displayModeBar': True,
    'modeBarButtonsToAdd': ['drawrect', 'eraseshape'],
}


def render_behavioral_diagnostics_tab(trades_df: pd.DataFrame):
    """Renders Tab 3: Behavioral Edge & Risk Diagnostics.

    Analyzes win probabilities across detailed sessions/pairs, position sizing risk
    spikes (oversizing/overleveraging), and holding time edge decay.
    """
    st.markdown("### 🧠 Behavioral Edge & Risk Diagnostics")
    st.caption(
        "Uncovers behavioral leaks, cross-market win probabilities, and risk"
        " scaling anomalies."
    )

    if trades_df is None or trades_df.empty:
        st.warning(
            "⚠️ No trade records available in this active segment to execute"
            " behavioral analysis."
        )
        return

    df = trades_df.copy()

    # Resolve required columns using utility function
    pnl_col, vol_col, open_col, exit_col, dir_col = resolve_trade_columns(df)

    if not pnl_col or not vol_col:
        st.error(
            "⚠️ Unable to resolve required PnL or Volume columns for behavioral"
            " analysis."
        )
        return

    # Clean data types and round raw floats
    df["clean_pnl"] = pd.to_numeric(df[pnl_col], errors="coerce").round(3)
    df["clean_vol"] = pd.to_numeric(df[vol_col], errors="coerce").round(3)
    df["is_win"] = (df["clean_pnl"] > 0).astype(int)

    # Resolve Symbol / Pair Column
    symbol_col = next(
        (
            c
            for c in [
                "symbol",
                "pair",
                "instrument",
                "Symbol",
                "Pair",
                "Instrument",
            ]
            if c in df.columns
        ),
        None,
    )

    # Derive Duration and Detailed Trading Session
    if open_col and exit_col:
        df["open_dt"] = pd.to_datetime(df[open_col], errors="coerce")
        df["exit_dt"] = pd.to_datetime(df[exit_col], errors="coerce")
        df["duration_min"] = (
            (df["exit_dt"] - df["open_dt"]).dt.total_seconds() / 60.0
        ).round(3)

        # Granular UTC-based Trading Session Mapping
        df["open_hour"] = df["open_dt"].dt.hour
        conditions = [
            (df["open_hour"] >= 21) | (df["open_hour"] < 0),   # Sydney (21:00 - 06:00 UTC)
            (df["open_hour"] >= 0) & (df["open_hour"] < 6),    # Tokyo (00:00 - 09:00 UTC)
            (df["open_hour"] >= 1) & (df["open_hour"] < 7),    # Hong Kong (01:00 - 08:00 UTC)
            (df["open_hour"] >= 7) & (df["open_hour"] < 8),    # Frankfurt (07:00 - 15:00 UTC)
            (df["open_hour"] >= 8) & (df["open_hour"] < 13),   # London (08:00 - 16:00 UTC)
            (df["open_hour"] >= 13) & (df["open_hour"] < 21),  # New York (13:00 - 21:00 UTC)
        ]
        choices = [
            "Sydney",
            "Tokyo",
            "Hong Kong",
            "Frankfurt",
            "London",
            "New York",
        ]
        df["session"] = np.select(conditions, choices, default="Off-Hours")
    else:
        df["duration_min"] = np.nan
        df["session"] = "Unknown Session"

    # ── ROW 1: Cross-Market & Session Win Probabilities (Full Width Matrix) ──
    st.markdown("#### 🌐 Win Probability Matrix by Market & Detailed Session")

    if symbol_col and "session" in df.columns:
        pivot_df = (
            df.groupby([symbol_col, "session"])
            .agg(
                win_rate=("is_win", "mean"),
                total_pnl=("clean_pnl", "sum"),
                trade_count=("is_win", "count"),
            )
            .reset_index()
        )

        pivot_df = pivot_df[pivot_df["trade_count"] >= 1]

        if not pivot_df.empty:
            pivot_df["win_rate_pct"] = (pivot_df["win_rate"] * 100).round(1)
            matrix_df = pivot_df.pivot(
                index=symbol_col, columns="session", values="win_rate_pct"
            )

            # Enforce exact chronological session order on columns
            session_order = [
                "Sydney",
                "Tokyo",
                "Hong Kong",
                "Frankfurt",
                "London",
                "New York",
            ]
            existing_sessions = [
                s for s in session_order if s in matrix_df.columns
            ]
            matrix_df = matrix_df[existing_sessions]

            fig_matrix = px.imshow(
                matrix_df,
                text_auto=".1f",
                labels=dict(
                    x="Trading Session",
                    y="Symbol / Pair",
                    color="Win Rate (%)",
                ),
                color_continuous_scale="RdYlGn",
                title="Win Rate % Matrix (Pair vs. Detailed Session)",
                template="plotly_dark",
                aspect="auto",  # Allows heatmap cells to stretch horizontally to fill container width
            )
            
            # Maximize horizontal width by stripping side padding while keeping height compact
            fig_matrix.update_layout(
                height=350,  # Compact vertical height
                autosize=True,
                margin=dict(l=0, r=0, t=40, b=10),  # Zero left/right margin to maximize stretch
            )
            
            # Ensure text labels inside matrix cells scale clearly when stretched
            fig_matrix.update_traces(
                textfont=dict(size=13),
            )

            st.plotly_chart(
                fig_matrix,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        else:
            st.info(
                "ℹ️ Insufficient trade frequency per pair/session combination to"
                " generate probability matrix."
            )
    else:
        st.info("ℹ️ Symbol or timestamp data missing for Session/Pair matrix.")

    st.markdown("---")

    # ── ROW 2: Position Sizing vs Realized PnL ──────────────────────────────
    st.markdown("#### ⚖️ Position Sizing vs. Realized PnL")
    fig_size = px.scatter(
        df,
        x="clean_vol",
        y="clean_pnl",
        color="is_win",
        color_continuous_scale=["#EF553B", "#00CC96"],
        size=np.abs(df["clean_pnl"]).clip(lower=1).round(3),
        labels={
            "clean_vol": "Position Size (Lots/Volume)",
            "clean_pnl": "Realized PnL ($)",
            "is_win": "Win (1) / Loss (0)",
        },
        template="plotly_dark",
        title="PnL Outliers & Dispersion by Position Sizing Tier",
    )
    fig_size.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_size.update_layout(height=420)
    st.plotly_chart(fig_size, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("---")

    # ── ROW 3: Sizing Tier Efficiency Analysis ─────────────────────────────
    st.markdown("#### 📊 Sizing Tier Expectancy")
    if len(df["clean_vol"].unique()) >= 2:
        df["vol_bin"] = pd.qcut(
            df["clean_vol"],
            q=min(4, len(df["clean_vol"].unique())),
            duplicates="drop",
        )
        vol_summary = (
            df.groupby("vol_bin", observed=False)
            .agg(
                avg_pnl=("clean_pnl", "mean"),
                win_rate=("is_win", "mean"),
            )
            .reset_index()
        )
        vol_summary["avg_pnl"] = vol_summary["avg_pnl"].round(3)
        vol_summary["win_rate_pct"] = (vol_summary["win_rate"] * 100).round(1)
        vol_summary["vol_bin"] = vol_summary["vol_bin"].astype(str)

        fig_bar = px.bar(
            vol_summary,
            x="vol_bin",
            y="avg_pnl",
            color="win_rate_pct",
            color_continuous_scale="Tealgrn",
            labels={
                "vol_bin": "Volume Bucket (Lots)",
                "avg_pnl": "Average Expectancy ($)",
                "win_rate_pct": "Win Rate (%)",
            },
            template="plotly_dark",
            title="Average Expectancy ($) per Volume Bucket",
            text_auto=".3f",
        )
        fig_bar.update_layout(height=420)
        st.plotly_chart(
            fig_bar, use_container_width=True, config=PLOTLY_CONFIG
        )

    st.markdown("---")

    # ── ROW 4 & 5: Duration & Holding Edge Decay ────────────────────────────
    if "duration_min" in df.columns and df["duration_min"].notna().sum() >= 5:
        st.markdown("#### ⏳ Hold Time Win Rate Decay")

        valid_dur = df.dropna(subset=["duration_min"]).copy()
        if len(valid_dur["duration_min"].unique()) >= 2:
            valid_dur["dur_bin"] = pd.qcut(
                valid_dur["duration_min"],
                q=min(4, len(valid_dur["duration_min"].unique())),
                duplicates="drop",
            )

            dur_summary = (
                valid_dur.groupby("dur_bin", observed=False)
                .agg(
                    win_rate=("is_win", "mean"),
                    avg_pnl=("clean_pnl", "mean"),
                )
                .reset_index()
            )
            dur_summary["avg_pnl"] = dur_summary["avg_pnl"].round(3)
            dur_summary["win_rate_pct"] = (
                dur_summary["win_rate"] * 100
            ).round(1)
            dur_summary["dur_bin"] = dur_summary["dur_bin"].astype(str)

            # ROW 4 Chart: Win Rate Decay Line Chart
            fig_dur_wr = px.line(
                dur_summary,
                x="dur_bin",
                y="win_rate_pct",
                markers=True,
                title="Win Rate (%) Decay Across Holding Duration Tiers",
                labels={
                    "dur_bin": "Duration Tier (Minutes)",
                    "win_rate_pct": "Win Rate (%)",
                },
                template="plotly_dark",
            )
            fig_dur_wr.update_traces(
                line_color="#FFA15A", line_width=3, marker_size=8
            )
            fig_dur_wr.update_layout(height=420)
            st.plotly_chart(
                fig_dur_wr, use_container_width=True, config=PLOTLY_CONFIG
            )

            st.markdown("---")

            # ROW 5 Chart: Duration Expectancy Bar Chart
            st.markdown("#### ⏳ Duration Expectancy Breakdown")
            fig_dur_pnl = px.bar(
                dur_summary,
                x="dur_bin",
                y="avg_pnl",
                color="avg_pnl",
                color_continuous_scale="RdYlGn",
                title="Average Expectancy ($) per Duration Tier",
                labels={
                    "dur_bin": "Duration Tier (Minutes)",
                    "avg_pnl": "Average PnL ($)",
                },
                template="plotly_dark",
                text_auto=".3f",
            )
            fig_dur_pnl.update_layout(height=420)
            st.plotly_chart(
                fig_dur_pnl, use_container_width=True, config=PLOTLY_CONFIG
            )
import numpy as np
import pandas as pd
import streamlit as st


def compute_sharpe(pnl_series, rf=0.0, annualize=365):
    """Calculates annualized Sharpe Ratio based on trade-by-trade PnL series."""
    if len(pnl_series) < 2 or pnl_series.std() == 0:
        return 0.0
    return float((pnl_series.mean() - rf) / pnl_series.std() * np.sqrt(annualize))


def compute_sortino(pnl_series, rf=0.0, annualize=365):
    """Calculates annualized Sortino Ratio based on downside deviation of negative PnLs."""
    if len(pnl_series) < 2:
        return 0.0
    negative_pnls = pnl_series[pnl_series < 0]
    if len(negative_pnls) == 0 or negative_pnls.std() == 0:
        return 0.0
    downside_std = negative_pnls.std()
    return float((pnl_series.mean() - rf) / downside_std * np.sqrt(annualize))


def render_settings_risk_tab(
    trades_df: pd.DataFrame,
    timeline_df: pd.DataFrame,
    seg_start_cap: float,
    selected_seg_name: str,
):
    st.markdown(
        f"### ⚙️ Risk Parameters & Performance Metrics — `{selected_seg_name}`"
    )

    pnl_series = (
        trades_df['net_pnl']
        if 'net_pnl' in trades_df.columns
        else trades_df['pnl']
    )
    wins = pnl_series[pnl_series > 0]
    losses = pnl_series[pnl_series < 0]

    # --- Core Metric Calculations ---
    tot_pnl = pnl_series.sum()
    total_trades = len(pnl_series)
    avg_pnl = pnl_series.mean() if total_trades > 0 else 0.0

    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0

    win_count = len(wins)
    loss_count = len(losses)
    win_loss_ratio = (
        win_count / loss_count if loss_count > 0 else (float(win_count) if win_count > 0 else 0.0)
    )

    win_rate = win_count / total_trades if total_trades > 0 else 0.0
    loss_rate = loss_count / total_trades if total_trades > 0 else 0.0

    # Expectancy ($ per trade) = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    # Profit Factor = Gross Profits / Gross Losses
    profit_factor = (
        wins.sum() / abs(losses.sum()) if abs(losses.sum()) > 0 else 0.0
    )

    # Drawdowns
    max_dd_val = timeline_df['drawdown'].min() if not timeline_df.empty else 0.0
    max_dd_pct = (
        timeline_df['drawdown_pct'].min() if not timeline_df.empty else 0.0
    )
    abs_max_dd_val = abs(max_dd_val)

    # Recovery Factor = Net Realized PnL / Max Dollar Drawdown
    recovery_factor = (
        tot_pnl / abs_max_dd_val if abs_max_dd_val > 0 else 0.0
    )

    # Risk-Adjusted Return (%) = Total Net Return (%) / Max Drawdown (%)
    net_return_pct = (
        (tot_pnl / seg_start_cap) * 100.0 if seg_start_cap > 0 else 0.0
    )
    risk_adj_return = (
        net_return_pct / abs(max_dd_pct) if abs(max_dd_pct) > 0 else 0.0
    )

    # Sharpe & Sortino
    sharpe = compute_sharpe(pnl_series)
    sortino = compute_sortino(pnl_series)

    # --- Section 1: Account & Drawdown Thresholds ---
    st.markdown("#### Account & Drawdown Thresholds")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Segment Start Capital",
            value=f"${seg_start_cap:,.2f}",
            help="Initial capital deposited or carried forward into this segment.",
        )
        st.metric(
            label="Max Dollar Drawdown",
            value=f"${max_dd_val:,.2f}",
            help="Largest peak-to-trough monetary loss experienced in this segment.",
        )

    with col2:
        st.metric(
            label="Current Ending Equity",
            value=(
                f"${timeline_df['equity'].iloc[-1]:,.2f}"
                if not timeline_df.empty
                else f"${seg_start_cap:,.2f}"
            ),
            help="Final account balance at the end of the selected segment.",
        )
        st.metric(
            label="Max Percentage Drawdown",
            value=f"{max_dd_pct:.2f}%",
            help="Largest peak-to-trough percentage loss relative to equity high-water mark.",
        )

    with col3:
        st.metric(
            label="Max Peak Equity",
            value=(
                f"${timeline_df['peak'].max():,.2f}"
                if not timeline_df.empty
                else f"${seg_start_cap:,.2f}"
            ),
            help="Highest account equity high-water mark reached during this segment.",
        )

    st.markdown("---")

    # --- Section 2: Performance & Risk Ratios ---
    st.markdown("#### Risk-Adjusted Ratios & Trade Statistics")
    r_col1, r_col2, r_col3 = st.columns(3)

    with r_col1:
        st.metric(
            label="Average P/L",
            value=f"${avg_pnl:,.2f}",
            help="Average monetary outcome across all executed trades (winning and losing combined).",
        )
        st.metric(
            label="Sharpe Ratio",
            value=f"{sharpe:.2f}",
            help="Measures excess return per unit of total risk (standard deviation of trade PnLs, annualized).",
        )
        st.metric(
            label="Recovery Factor",
            value=f"{recovery_factor:.2f}",
            help="Net Realized PnL divided by Max Dollar Drawdown. Evaluates how effectively the strategy recovers from drawdowns.",
        )
        st.metric(
            label="Profit Factor",
            value=f"{profit_factor:.2f}",
            help="Gross winning trade profits divided by gross losing trade losses.",
        )

    with r_col2:
        st.metric(
            label="Win / Loss Ratio",
            value=f"{win_loss_ratio:.2f}",
            help="Ratio of winning trade count to losing trade count (Winning Trades / Losing Trades).",
        )
        st.metric(
            label="Sortino Ratio",
            value=f"{sortino:.2f}",
            help="Measures return per unit of downside risk, ignoring positive volatility.",
        )
        st.metric(
            label="Risk-Adjusted Return",
            value=f"{risk_adj_return:.2f}",
            help="Total Net Return (%) divided by Max Percentage Drawdown (Calmar ratio equivalent).",
        )
        st.metric(
            label="Trade Expectancy",
            value=f"${expectancy:,.2f}",
            help="Expected average monetary outcome per executed trade: (Win Rate * Avg Win) - (Loss Rate * Avg Loss).",
        )

    with r_col3:
        st.metric(
            label="Average Win",
            value=f"${avg_win:,.2f}",
            help="Average monetary profit across all winning trades.",
        )
        st.metric(
            label="Average Loss",
            value=f"${avg_loss:,.2f}",
            help="Average monetary loss across all losing trades.",
        )
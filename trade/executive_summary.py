import streamlit as st
import numpy as np
from modules.charts.equity_charts import render_equity_and_drawdown_charts

def compute_sharpe(pnl_series, rf=0.0, annualize=365):
    """Calculates annualized Sharpe Ratio based on trade-by-trade return series."""
    if len(pnl_series) < 2 or pnl_series.std() == 0:
        return 0.0
    return float((pnl_series.mean() - rf) / pnl_series.std() * np.sqrt(annualize))

# In trade/executive_summary.py

def render_executive_summary_tab(trades_df, timeline_df, seg_start_cap, selected_seg_name, has_blown, first_blowout_time):
    if has_blown:
        st.error(f"⚠️ **Account Blowout Triggered:** Balance hit $0 or lower on **{first_blowout_time.strftime('%Y-%m-%d %H:%M UTC')}**.")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # 1. Fees Tracking (Informational display only - NOT deducted from trade PnL)
    tot_open_fees = abs(trades_df['fees_entry'].sum()) if 'fees_entry' in trades_df.columns else abs(trades_df['fees'].sum() / 2)
    tot_close_fees = abs(trades_df['fees_exit'].sum()) if 'fees_exit' in trades_df.columns else abs(trades_df['fees'].sum() / 2)
    total_fees = abs(trades_df['fees_total'].sum()) if 'fees_total' in trades_df.columns else (tot_open_fees + tot_close_fees)

    # 2. Net Realized PnL (Direct sum of trade PnL; zero fee deductions in Python)
    tot_pnl = trades_df['pnl'].sum()

    # 3. Account Equity = Starting Capital + Realized PnL
    if not timeline_df.empty and 'equity' in timeline_df.columns:
        final_equity = timeline_df['equity'].iloc[-1]
    else:
        final_equity = seg_start_cap + tot_pnl

    win_rate = (trades_df['pnl'] > 0).mean() * 100 if len(trades_df) > 0 else 0.0
    sharpe = compute_sharpe(trades_df['pnl'])

    # Render Metrics
    col1.metric(
        label="Realized P/L",
        value=f"${tot_pnl:,.2f}",
        help="Cumulative net profit and loss generated across all closed trades in this segment. Excludes initial capital."
    )
    col2.metric(
        label="Account Equity",
        value=f"${final_equity:,.2f}",
        help="Total current account balance: Initial Capital + Realized P/L."
    )
    col3.metric(
        label="Win Rate",
        value=f"{win_rate:.1f}%",
        help="Percentage of closed trades that resulted in a positive profit."
    )
    col4.metric(
        label="Sharpe Ratio",
        value=f"{sharpe:.2f}",
        help="Risk-adjusted return ratio calculated as (Mean Trade P/L / Standard Deviation of P/L) * sqrt(365)."
    )
    col5.metric(
        label="Open Fees",
        value=f"${tot_open_fees:,.2f}",
        help="Total execution commission and fees paid on margin when opening position entries."
    )
    col6.metric(
        label="Close Fees",
        value=f"${tot_close_fees:,.2f}",
        help="Total execution commission and fees paid when closing position exits."
    )

    st.markdown(f"### Cumulative Equity & Drawdown — `{selected_seg_name}`")
    render_equity_and_drawdown_charts(timeline_df, seg_start_cap, selected_seg_name, has_blown, first_blowout_time)
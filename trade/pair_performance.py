import streamlit as st
import pandas as pd
import numpy as np
from modules.charts.pair_charts import render_pair_performance_charts

def compute_sharpe(pnl_series, rf=0.0, annualize=365):
    if len(pnl_series) < 2 or pnl_series.std() == 0:
        return 0.0
    return float((pnl_series.mean() - rf) / pnl_series.std() * np.sqrt(annualize))

def render_pair_performance_tab(trades_df, selected_seg_name):
    st.markdown(f"### Instrument Performance Metrics — `{selected_seg_name}`")
    pair_summary = []

    for pair, grp in trades_df.groupby('pair'):
        pnl = grp['pnl']
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]

        open_fees = abs(grp['fees_entry'].sum()) if 'fees_entry' in grp.columns else 0.0
        close_fees = abs(grp['fees_exit'].sum()) if 'fees_exit' in grp.columns else 0.0

        pair_summary.append({
            "Pair": pair,
            "Trades": len(grp),
            "Win Rate %": round((len(wins)/len(pnl))*100, 1) if len(pnl) else 0,
            "TP": int((grp['exit_type'] == 'TP').sum()),
            "SL": int((grp['exit_type'] == 'SL').sum()),
            "Realized P/L": round(grp['pnl'].sum(), 2),
            "Open Fees": round(open_fees, 2),
            "Close Fees": round(close_fees, 2),
            "Avg Win": round(wins.mean(), 2) if len(wins) else 0,
            "Avg Loss": round(losses.mean(), 2) if len(losses) else 0,
            "Sharpe": round(compute_sharpe(pnl), 2)
        })
    pair_df = pd.DataFrame(pair_summary)

    tot_wins = trades_df[trades_df['pnl'] > 0]['pnl']
    tot_losses = trades_df[trades_df['pnl'] < 0]['pnl']
    tot_open_fees = abs(trades_df['fees_entry'].sum()) if 'fees_entry' in trades_df.columns else 0.0
    tot_close_fees = abs(trades_df['fees_exit'].sum()) if 'fees_exit' in trades_df.columns else 0.0

    tot_row = pd.DataFrame([{
        "Pair": "TOTAL",
        "Trades": len(trades_df),
        "Win Rate %": round((len(tot_wins)/len(trades_df))*100, 1) if len(trades_df) else 0,
        "TP": int((trades_df['exit_type'] == 'TP').sum()),
        "SL": int((trades_df['exit_type'] == 'SL').sum()),
        "Realized P/L": round(trades_df['pnl'].sum(), 2),
        "Open Fees": round(tot_open_fees, 2),
        "Close Fees": round(tot_close_fees, 2),
        "Avg Win": round(tot_wins.mean(), 2) if len(tot_wins) else 0,
        "Avg Loss": round(tot_losses.mean(), 2) if len(tot_losses) else 0,
        "Sharpe": round(compute_sharpe(trades_df['pnl']), 2)
    }])

    st.dataframe(pd.concat([pair_df, tot_row], ignore_index=True), use_container_width=True)
    render_pair_performance_charts(pair_df)
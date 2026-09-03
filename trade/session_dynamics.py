import streamlit as st
import pandas as pd
import numpy as np
from modules.charts.session_charts import render_session_duration_chart

def compute_sharpe(pnl_series, rf=0.0, annualize=365):
    if len(pnl_series) < 2 or pnl_series.std() == 0:
        return 0.0
    return float((pnl_series.mean() - rf) / pnl_series.std() * np.sqrt(annualize))

def render_session_dynamics_tab(trades_df, selected_seg_name):
    st.markdown(f"### Session Breakdown — `{selected_seg_name}`")
    sessions_dict = {
        'Sydney': (21, 6), 'Tokyo': (0, 9), 'Hong Kong': (1, 10),
        'London': (8, 16), 'New York': (13, 22)
    }
    sess_rows = []
    for name in sessions_dict.keys():
        sess_col = f'session_{name}'
        subset = trades_df[trades_df[sess_col]] if sess_col in trades_df.columns else pd.DataFrame()

        if not subset.empty:
            pnl = subset['pnl']
            wins = pnl[pnl > 0]
            avg_hold = round(subset['hold_minutes'].mean(), 1) if 'hold_minutes' in subset.columns else 0
            sess_rows.append({
                "Session": name,
                "Trades": len(subset),
                "Win Rate %": round(len(wins)/len(pnl)*100, 1) if len(pnl) else 0,
                "Total P/L": round(pnl.sum(), 2),
                "Avg Hold (min)": avg_hold,
                "Sharpe": round(compute_sharpe(pnl), 2)
            })
        else:
            sess_rows.append({
                "Session": name, "Trades": 0, "Win Rate %": 0,
                "Total P/L": 0.0, "Avg Hold (min)": 0, "Sharpe": 0.0
            })

    sess_df = pd.DataFrame(sess_rows)
    tot_sess_wins = trades_df[trades_df['pnl'] > 0]['pnl']
    avg_hold_total = round(trades_df['hold_minutes'].mean(), 1) if 'hold_minutes' in trades_df.columns else 0

    sess_tot_row = pd.DataFrame([{
        "Session": "TOTAL",
        "Trades": len(trades_df),
        "Win Rate %": round((len(tot_sess_wins)/len(trades_df))*100, 1) if len(trades_df) else 0,
        "Total P/L": round(trades_df['pnl'].sum(), 2),
        "Avg Hold (min)": avg_hold_total,
        "Sharpe": round(compute_sharpe(trades_df['pnl']), 2)
    }])

    st.dataframe(pd.concat([sess_df, sess_tot_row], ignore_index=True), use_container_width=True)
    render_session_duration_chart(trades_df)
import streamlit as st
import pandas as pd

def render_audit_trade_logs_tab(trades_df, blown_trades, has_blown, selected_seg_name):
    st.markdown(f"### 📜 Complete Trade Log & Blowout Audit — `{selected_seg_name}`")

    if has_blown:
        st.error(f"🚨 **{len(blown_trades)} Blowout Trade Event(s) Detected**")
        blowout_logs = []
        for idx, b_row in blown_trades.reset_index().iterrows():
            blowout_logs.append({
                "Event #": idx + 1,
                "Timestamp (UTC)": b_row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                "Pair": b_row['pair'],
                "Exit Reason": b_row['exit_type'],
                "Net Change": f"${b_row['net_change']:,.2f}",
                "Breached Balance": f"${b_row['equity']:,.2f}"
            })
        st.dataframe(pd.DataFrame(blowout_logs), use_container_width=True)
    else:
        st.success("✅ **NO BLOWOUTS DETECTED:** Account balance maintained positive capital throughout this segment window.")

    st.markdown("#### Matched Trade Executions")
    st.dataframe(trades_df, use_container_width=True)
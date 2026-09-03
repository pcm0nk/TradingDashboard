import streamlit as st

def render_settings_risk_tab(trades_df, timeline_df, seg_start_cap, selected_seg_name):
    st.markdown(f"### ⚙️ Risk Parameters & Segment Configuration — `{selected_seg_name}`")
    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.markdown("#### Account Parameters")
        st.write(f"**Segment Start Capital:** `${seg_start_cap:,.2f}`")
        st.write(f"**Current Ending Equity:** `${timeline_df['equity'].iloc[-1]:,.2f}`")
        st.write(f"**Max Peak Equity:** `${timeline_df['peak'].max():,.2f}`")

    with r_col2:
        st.markdown("#### Risk & Drawdown Thresholds")
        max_dd_val = timeline_df['drawdown'].min()
        max_dd_pct = timeline_df['drawdown_pct'].min()
        st.write(f"**Max Dollar Drawdown:** `${max_dd_val:,.2f}`")
        st.write(f"**Max Percentage Drawdown:** `{max_dd_pct:.2f}%`")
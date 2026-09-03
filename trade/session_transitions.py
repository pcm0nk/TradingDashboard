import streamlit as st
from modules.session_transition import build_session_lifecycle_dataframe
from modules.charts.session_transition_charts import render_session_gantt_chart

def render_session_transitions_tab(trades_df, selected_seg_name):
    st.markdown(f"### ⏳ Session Transition & Lifecycle Timeline — `{selected_seg_name}`")
    
    lifecycle_df = build_session_lifecycle_dataframe(trades_df.copy())

    if lifecycle_df is not None and not lifecycle_df.empty:
        render_session_gantt_chart(lifecycle_df)
    else:
        st.info("No session lifecycle data available for this segment.")
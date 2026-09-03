import streamlit as st
import plotly.express as px

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor='#0E1117',
    plot_bgcolor='#131722',
    font=dict(color='#E0E0E0'),
    xaxis=dict(gridcolor='#2A2E39', zerolinecolor='#2A2E39'),
    yaxis=dict(gridcolor='#2A2E39', zerolinecolor='#2A2E39')
)

def render_session_duration_chart(trades_df):
    fig_box = px.box(
        trades_df, x='exit_type', y='hold_minutes', points="all", 
        title="Hold Duration by Exit Type (Minutes)", color='exit_type', 
        color_discrete_sequence=['#00E676', '#FF5252', '#F1C40F', '#E74C3C']
    )
    fig_box.update_layout(**PLOTLY_DARK_LAYOUT)
    st.plotly_chart(fig_box, use_container_width=True)
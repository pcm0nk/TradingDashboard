import streamlit as st
import plotly.graph_objects as go

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor='#0E1117',
    plot_bgcolor='#131722',
    font=dict(color='#E0E0E0'),
    xaxis=dict(gridcolor='#2A2E39', zerolinecolor='#2A2E39'),
    yaxis=dict(gridcolor='#2A2E39', zerolinecolor='#2A2E39')
)

def render_equity_and_drawdown_charts(timeline_df, seg_start_cap, selected_seg_name, has_blown, first_blowout_time):
    # Equity Curve
    fig_eq = go.Figure()
    
    # Line 1: Net Account Balance (Yellow)
    fig_eq.add_trace(go.Scatter(
        x=timeline_df['time'], 
        y=timeline_df['equity'], 
        mode='lines', 
        name='Net Account Balance ($)', 
        line=dict(color='#F1C40F', width=2),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d %H:%M}<br>" +
                      "<b>Net Account Balance:</b> $%{y:,.2f}<br>" +
                      "<i>(Includes starting capital + trade PnL - total fees)</i><extra></extra>"
    ))
    
    # Line 2: Realized Pure PnL (Green Dotted)
    fig_eq.add_trace(go.Scatter(
        x=timeline_df['time'], 
        y=timeline_df['cum_pnl'], 
        mode='lines', 
        name='Realized PnL ($)', 
        line=dict(color='#00E676', width=1.5, dash='dot'),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d %H:%M}<br>" +
                      "<b>Realized Trade PnL:</b> $%{y:,.2f}<br>" +
                      "<i>(Pure trade profit/loss excluding fees)</i><extra></extra>"
    ))
    
    if has_blown:
        fig_eq.add_vline(
            x=first_blowout_time, line_width=2, line_dash="dash", line_color="#FF5252", 
            annotation_text="Account Blown ($0)"
        )

    fig_eq.update_layout(
        **PLOTLY_DARK_LAYOUT, 
        title=f"Segment Growth Curve (Starting Balance: ${seg_start_cap:,.2f}) — {selected_seg_name}", 
        height=400,
        hovermode="x unified"
    )
    st.plotly_chart(fig_eq, use_container_width=True)

    # Drawdown Chart
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=timeline_df['time'], 
        y=timeline_df['drawdown_pct'], 
        fill='tozeroy', 
        name='Drawdown %', 
        line=dict(color='#FF5252', width=1),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d %H:%M}<br>" +
                      "<b>Drawdown:</b> %{y:.2f}%<extra></extra>"
    ))
    fig_dd.update_layout(**PLOTLY_DARK_LAYOUT, title="Peak-to-Trough Drawdown (%)", height=250)
    st.plotly_chart(fig_dd, use_container_width=True)
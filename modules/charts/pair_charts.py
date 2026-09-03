import streamlit as st
import plotly.graph_objects as go

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor='#0E1117',
    plot_bgcolor='#131722',
    font=dict(color='#E0E0E0'),
    xaxis=dict(gridcolor='#2A2E39', zerolinecolor='#2A2E39'),
    yaxis=dict(gridcolor='#2A2E39', zerolinecolor='#2A2E39')
)

def render_pair_performance_charts(pair_df):
    """
    Renders pair performance bar charts in standalone full-width single rows.
    All text labels are explicitly pinned OUTSIDE the bars for consistent visuals.
    """
    if pair_df.empty:
        st.info("No pair data available for charting.")
        return

    # Filter out TOTAL row if present in pair_df
    chart_df = pair_df[pair_df['Pair'] != 'TOTAL'].copy()
    if chart_df.empty:
        return

    st.markdown("---")
    st.markdown("### 📈 Visual Breakdown Per Pair")

    # -------------------------------------------------------------------------
    # ROW 1: Realized PnL per Pair (Full Width Single Row)
    # -------------------------------------------------------------------------
    st.markdown("#### Realized P/L by Instrument")
    
    # Sort pairs by Realized PnL descending for consistent presentation
    pnl_df = chart_df.sort_values(by='Realized P/L', ascending=False)
    
    fig_pnl = go.Figure()
    colors = ['#00E676' if val >= 0 else '#FF5252' for val in pnl_df['Realized P/L']]
    
    fig_pnl.add_trace(go.Bar(
        x=pnl_df['Pair'],
        y=pnl_df['Realized P/L'],
        marker_color=colors,
        text=pnl_df['Realized P/L'].apply(lambda v: f"${v:,.2f}"),
        textposition='outside',  # <--- Forces numbers strictly OUTSIDE the bars
        cliponaxis=False,       # Prevents text labels outside axis boundary from getting clipped
        hovertemplate="<b>Pair:</b> %{x}<br><b>Realized PnL:</b> $%{y:,.2f}<extra></extra>"
    ))
    
    fig_pnl.update_layout(
        **PLOTLY_DARK_LAYOUT,
        title="Realized PnL ($) per Trading Instrument",
        xaxis_title="Trading Pair",
        yaxis_title="Realized PnL ($)",
        height=450,
        margin=dict(l=40, r=40, t=60, b=80),  # Top margin buffer for outside labels
        hovermode="x unified"
    )
    # Give the Y-axis padding so labels above tall bars are never cropped
    fig_pnl.update_yaxes(automargin=True)
    fig_pnl.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_pnl, use_container_width=True)

    # -------------------------------------------------------------------------
    # ROW 2: Fee Breakdown per Pair (Full Width Single Row)
    # -------------------------------------------------------------------------
    st.markdown("#### Execution Fee Distribution (Open vs. Close Fees)")
    
    # Sort pairs by total fee impact descending
    fee_df = chart_df.copy()
    fee_df['Total_Fees'] = fee_df['Open Fees'] + fee_df['Close Fees']
    fee_df = fee_df.sort_values(by='Total_Fees', ascending=False)
    
    fig_fees = go.Figure()
    
    # Stacked bar: Open Fees
    fig_fees.add_trace(go.Bar(
        x=fee_df['Pair'],
        y=fee_df['Open Fees'],
        name='Open Fees ($)',
        marker_color='#FFB74D',
        text=fee_df['Open Fees'].apply(lambda v: f"${v:,.2f}" if v > 0 else ""),
        textposition='outside',  # <--- Forces numbers strictly OUTSIDE the bars
        cliponaxis=False,
        hovertemplate="<b>Pair:</b> %{x}<br><b>Open Fees:</b> $%{y:,.2f}<extra></extra>"
    ))
    
    # Stacked bar: Close Fees
    fig_fees.add_trace(go.Bar(
        x=fee_df['Pair'],
        y=fee_df['Close Fees'],
        name='Close Fees ($)',
        marker_color='#FF7043',
        text=fee_df['Close Fees'].apply(lambda v: f"${v:,.2f}" if v > 0 else ""),
        textposition='outside',  # <--- Forces numbers strictly OUTSIDE the bars
        cliponaxis=False,
        hovertemplate="<b>Pair:</b> %{x}<br><b>Close Fees:</b> $%{y:,.2f}<extra></extra>"
    ))
    
    fig_fees.update_layout(
        **PLOTLY_DARK_LAYOUT,
        barmode='group',  # Changed to grouped mode so outside text labels do not collide
        title="Cumulative Execution Fees ($) by Pair",
        xaxis_title="Trading Pair",
        yaxis_title="Fees Paid ($)",
        height=450,
        margin=dict(l=40, r=40, t=60, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_fees.update_yaxes(automargin=True)
    fig_fees.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_fees, use_container_width=True)
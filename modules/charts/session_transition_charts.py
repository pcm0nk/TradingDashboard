import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor='#0E1117',
    plot_bgcolor='#131722',
    font=dict(color='#E0E0E0'),
)

EXIT_TYPE_COLORS = {
    'TP': '#00E676',  # Green
    'SL': '#FF5252',  # Red
    'BE': '#FFD600',  # Yellow
    'Manual': '#AA00FF',  # Purple
    'N/A': '#9E9E9E',  # Grey
}


def render_session_gantt_chart(session_trades_df: pd.DataFrame):
    """Renders display controls and Gantt chart for session transitions."""
    if session_trades_df.empty:
        st.info("No trades available for session transition charting.")
        return

    # Total trades count in dataset
    total_trades_count = len(session_trades_df)

    # 1. Render Side-by-Side Controls inside a bordered container
    with st.container(border=True):
        st.markdown("##### ⚙️ Chart Display Controls")

        col_left, col_right = st.columns(2)

        with col_left:
            trade_input_str = st.text_input(
                "Number of Recent Trades to Display",
                value="30",
                key="gantt_chart_trade_text_box",
                help="Type any number (e.g. 10, 20, 50) or check 'Show All Trades'.",
            )

            show_all_trades = st.checkbox(
                f"Show All Trades (Total: {total_trades_count})",
                value=False,
                key="gantt_chart_show_all_cb",
            )

        with col_right:
            chart_height = st.slider(
                "Adjust Chart Height (px)",
                min_value=400,
                max_value=1500,
                value=520,
                step=50,
                key="gantt_chart_height_slider",
            )

    # 2. Slice dataset based on user controls
    if show_all_trades:
        chart_df = session_trades_df.copy()
    else:
        try:
            num_trades = int(trade_input_str.strip())
            num_trades = max(1, min(num_trades, total_trades_count))
        except (ValueError, AttributeError):
            num_trades = min(20, total_trades_count)

        chart_df = session_trades_df.tail(num_trades).copy()

    # Store sliced result back into attrs for the audit log table
    session_trades_df.attrs["filtered_df"] = chart_df

    if chart_df.empty:
        st.info("No trades found for selected view.")
        return

    fig = go.Figure()

    # 3. Add Trade Lifecycles as horizontal Gantt lines
    for idx, row in chart_df.iterrows():
        exit_reason = str(row.get('exit_type', row.get('Exit Type', 'N/A')))
        line_color = EXIT_TYPE_COLORS.get(exit_reason, '#9E9E9E')

        pair_val = str(row.get('pair', 'Unknown'))
        trade_id_val = row.get('trade_id', idx)
        entry_sess = str(
            row.get('entry_session', row.get('Entry Session', 'N/A'))
        )
        hold_path = str(
            row.get('hold_sessions_str', row.get('Hold Path (Sessions)', 'N/A'))
        )
        exit_sess = str(
            row.get('exit_session', row.get('Exit Session', 'N/A'))
        )
        overlap_exit_val = str(
            row.get('is_overlap_exit', row.get('Overlap Exit?', 'N/A'))
        )
        pnl_val = float(row.get('pnl', row.get('Realized PnL', 0.0)))

        y_label = f'{pair_val} (#{trade_id_val})'
        entry_time = pd.to_datetime(row['entry_time'])
        exit_time = pd.to_datetime(row['exit_time'])

        fig.add_trace(
            go.Scatter(
                x=[entry_time, exit_time],
                y=[y_label, y_label],
                mode='lines+markers',
                line=dict(color=line_color, width=6),
                marker=dict(size=8, symbol=['circle', 'x']),
                name=y_label,
                showlegend=False,
                hovertemplate=(
                    f'<b>Pair:</b> {pair_val}<br>'
                    f'<b>Exit Type:</b> <span style="color:{line_color}"><b>{exit_reason}</b></span><br>'
                    f'<b>Entry Session:</b> {entry_sess}<br>'
                    f'<b>Hold Path:</b> {hold_path}<br>'
                    f'<b>Exit Session:</b> {exit_sess}<br>'
                    f'<b>Overlap Exit:</b> {overlap_exit_val}<br>'
                    f'<b>PnL:</b> ${pnl_val:,.2f}<extra></extra>'
                ),
            )
        )

    # 4. Add Exit Type Legend traces
    for exit_code, hex_color in EXIT_TYPE_COLORS.items():
        if (
            exit_code in chart_df['exit_type'].values
            or exit_code in chart_df.get('Exit Type', pd.Series()).values
        ):
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode='markers',
                    marker=dict(size=8, color=hex_color),
                    name=f'Exit: {exit_code}',
                    showlegend=True,
                )
            )

    min_time = pd.to_datetime(chart_df['entry_time'].min())
    max_time = pd.to_datetime(chart_df['exit_time'].max())

    x_start = min_time - pd.Timedelta(minutes=15)
    x_end = max_time + pd.Timedelta(minutes=15)

    # 5. Apply layout settings with legend anchored OUTSIDE the plotting canvas
    fig.update_layout(
        **PLOTLY_DARK_LAYOUT,
        title=dict(
            text=f'Trade Duration Timeline ({len(chart_df)} of {total_trades_count} Trades)',
            y=0.98,
            x=0,
            xanchor='left',
            yanchor='top',
        ),
        xaxis=dict(
            type='date',
            range=[x_start, x_end],
            gridcolor='#2A2E39',
            zerolinecolor='#2A2E39',
            title='Timeline (UTC)',
        ),
        yaxis=dict(
            title='Pair & Trade ID',
            gridcolor='#2A2E39',
            zerolinecolor='#2A2E39',
            tickfont=dict(size=11),
            automargin=True,
        ),
        height=chart_height,
        margin=dict(l=40, r=40, t=110, b=50),  # Expanded top margin to prevent overlapping
        hovermode='closest',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,  # Places legend directly above plot boundary
            xanchor='left',
            x=0,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'scrollZoom': True,
            'displayModeBar': True,
        },
    )
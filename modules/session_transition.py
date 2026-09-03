from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from modules.charts.session_transition_charts import (
    render_session_gantt_chart,
)


def get_active_sessions_at_hour(hour: int) -> list:
    """Returns active global market sessions for a given UTC hour."""
    sessions = {
        'Sydney': (21, 6),
        'Tokyo': (0, 9),
        'Hong Kong': (1, 10),
        'Frankfurt': (7, 15),
        'London': (8, 16),
        'New York': (13, 22),
    }

    active = []
    for name, (start_h, end_h) in sessions.items():
        if start_h < end_h:
            if start_h <= hour < end_h:
                active.append(name)
        else:
            if hour >= start_h or hour < end_h:
                active.append(name)
    return active


def build_session_lifecycle_dataframe(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Processes completed trade records and maps session transitions."""
    if trades_df.empty:
        return pd.DataFrame()

    session_trade_logs = []

    for trade_idx, trow in trades_df.iterrows():
        entry_dt = pd.to_datetime(trow['entry_time'])
        exit_dt = pd.to_datetime(trow['exit_time'])

        entry_sessions = get_active_sessions_at_hour(entry_dt.hour)
        entry_session_str = (
            '/'.join(entry_sessions) if entry_sessions else 'Off-Hours'
        )

        exit_sessions = get_active_sessions_at_hour(exit_dt.hour)
        exit_session_str = (
            '/'.join(exit_sessions) if exit_sessions else 'Off-Hours'
        )
        is_overlap_exit = 'Yes' if len(exit_sessions) > 1 else 'No'

        hourly_range = pd.date_range(
            start=entry_dt.floor('h'), end=exit_dt.floor('h'), freq='h'
        )
        all_held_sessions = set()
        overlap_periods_held = set()

        for h_dt in hourly_range:
            active_h = get_active_sessions_at_hour(h_dt.hour)
            all_held_sessions.update(active_h)
            if len(active_h) > 1:
                overlap_periods_held.add('+'.join(sorted(active_h)))

        hold_path_str = (
            ' ➔ '.join(sorted(all_held_sessions))
            if all_held_sessions
            else 'Intra-Hour Exit'
        )
        overlaps_str = (
            ', '.join(sorted(overlap_periods_held))
            if overlap_periods_held
            else 'None'
        )

        exit_type_val = trow.get('exit_type', trow.get('Exit Type', 'N/A'))
        pnl_val = trow.get('pnl', trow.get('Realized PnL', 0.0))

        session_trade_logs.append({
            'trade_id': trade_idx + 1,
            'pair': trow.get('pair', 'Unknown'),
            'entry_time': entry_dt,
            'exit_time': exit_dt,
            'pnl': pnl_val,
            'exit_type': exit_type_val,
            'Exit Type': exit_type_val,
            'Realized PnL': round(pnl_val, 2),
            'Entry Session': entry_session_str,
            'Hold Path (Sessions)': hold_path_str,
            'Overlap Exposures': overlaps_str,
            'Exit Session': exit_session_str,
            'Overlap Exit?': is_overlap_exit,
            'entry_session': entry_session_str,
            'exit_session': exit_session_str,
            'is_overlap_exit': is_overlap_exit,
            'hold_sessions_str': hold_path_str,
        })

    return pd.DataFrame(session_trade_logs)


def render_session_transitions_tab(
    trades_df: pd.DataFrame, selected_seg_name: str
):
    """Renders Tab 4: Session Transitions & Holds analysis."""
    st.markdown(
        f'### ⏳ Session Transition & Lifecycle Timeline — `{selected_seg_name}`'
    )

    if trades_df.empty:
        st.info('No trade data available.')
        return

    lifecycle_df = build_session_lifecycle_dataframe(trades_df.copy())

    if lifecycle_df.empty:
        st.info('No lifecycle data built.')
        return

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # 1. Render Chart (Controls run inside render_session_gantt_chart)
    render_session_gantt_chart(lifecycle_df)

    # 2. Retrieve filtered_df attached during chart rendering
    filtered_df = lifecycle_df.attrs.get('filtered_df', lifecycle_df)

    # 3. Detailed Audit Log Table
    st.markdown('#### Detailed Session Transition Log')
    display_cols = [
        'trade_id',
        'pair',
        'entry_time',
        'exit_time',
        'Entry Session',
        'Hold Path (Sessions)',
        'Overlap Exposures',
        'Exit Session',
        'Overlap Exit?',
        'Exit Type',
        'Realized PnL',
    ]
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    st.dataframe(filtered_df[available_cols], use_container_width=True)
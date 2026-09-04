import time
import pandas as pd
import streamlit as st

# Root-level Sub-Module Imports (sibling to modules/)
from trade.audit_trade_logs import render_audit_trade_logs_tab
from trade.executive_summary import render_executive_summary_tab
from trade.pair_performance import render_pair_performance_tab
from trade.session_dynamics import render_session_dynamics_tab
from trade.session_transitions import render_session_transitions_tab
from trade.settings_risk import render_settings_risk_tab


st.markdown(
    """
    <style>
    /* 1. Force the parent tab container to flex-wrap and span 100% width */
    div[data-baseweb="tab-highlight-container"] {
        width: 100% !important;
    }
    
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        width: 100% !important;
        gap: 4px !important;
    }

    /* 2. Style each tab button so they scale evenly across the screen */
    div[data-baseweb="tab-list"] button {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding-left: 6px !important;
        padding-right: 6px !important;
        font-size: 13px !important;
        white-space: nowrap !important;
        text-align: center !important;
    }

    /* 3. Hide Streamlit's tab pagination scroll arrows completely */
    button[aria-label="Previous tab"],
    button[aria-label="Next tab"],
    div[data-testid="stTabOverflowIndicator"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def prepare_session_flags(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Applies session flags to already-matched FIFO trade records."""
    if trades_df.empty or 'exit_time' not in trades_df.columns:
        return trades_df

    df = trades_df.copy()

    sessions_config = {
        'Sydney': (21, 6),
        'Tokyo': (0, 9),
        'Hong Kong': (1, 10),
        'London': (8, 16),
        'New York': (13, 22),
    }

    for name, (start_h, end_h) in sessions_config.items():
        if start_h < end_h:
            df[f'session_{name}'] = df['exit_time'].dt.hour.between(
                start_h, end_h - 1
            )
        else:
            df[f'session_{name}'] = (df['exit_time'].dt.hour >= start_h) | (
                df['exit_time'].dt.hour < end_h
            )

    return df


@st.dialog("⚠️ Run Trading Analysis Confirmation")
def confirm_and_run_analysis_dialog(clean_trades_df: pd.DataFrame):
    """Modal pop-up dialog with trade scope warning, progress bar, and OK button."""
    st.warning(
        "ℹ️ **Notice:** Trading analysis will **only be run on validated trades** "
        "processed through the FIFO order matching engine. Unmatched or orphan orders will be excluded."
    )

    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

    if not st.session_state.processing_complete:
        if st.button(
            "▶️ Proceed with Analysis", type="primary", use_container_width=True
        ):
            progress_text = (
                "Processing validated FIFO trade sessions and timelines..."
            )
            my_bar = st.progress(0, text=progress_text)

            for percent_complete in range(1, 101, 20):
                time.sleep(0.05)
                my_bar.progress(percent_complete, text=progress_text)

            st.session_state.full_trades_df = prepare_session_flags(
                clean_trades_df
            )
            st.session_state.analysis_ran = True
            st.session_state.processing_complete = True

            my_bar.progress(
                100, text="✅ Trading Analysis successfully completed!"
            )
            st.rerun()
    else:
        st.success(
            "✅ Analysis complete! Click OK to dismiss and view your dashboard."
        )
        if st.button("OK", type="primary", use_container_width=True):
            del st.session_state.processing_complete
            st.rerun()


def run_trade_analysis_phase(
    clean_trades_df: pd.DataFrame, meta: dict, ledger_df: pd.DataFrame
):
    """Executes Phase 2: Trade Analysis."""
    if st.button("🚀 Run Trading Analysis", use_container_width=True):
        confirm_and_run_analysis_dialog(clean_trades_df)

    if meta.get('passed', True) and not st.session_state.get('analysis_ran'):
        if (
            'full_trades_df' not in st.session_state
            or st.session_state.full_trades_df is None
        ):
            st.session_state.full_trades_df = prepare_session_flags(clean_trades_df)
            st.session_state.analysis_ran = True

    if (
        st.session_state.get('analysis_ran')
        and st.session_state.get('full_trades_df') is not None
    ):
        full_trades_df = st.session_state.full_trades_df

        if full_trades_df.empty:
            st.error("No valid matched trade data passed into Trade Analysis.")
            return

        # 1. Deposit Boundary Slicing Engine
        ledger_clean = (
            ledger_df.dropna(how='all').copy()
            if ledger_df is not None
            else pd.DataFrame()
        )
        dep_events = []
        has_ledger_error = False

        if not ledger_clean.empty:
            for row_idx, lrow in ledger_clean.iterrows():
                if pd.isna(lrow.get('Date')) or pd.isna(lrow.get('Amount ($)')):
                    continue

                if lrow.get('Type') == 'Deposit':
                    raw_date = str(lrow['Date']).strip()
                    raw_amount = str(lrow['Amount ($)']).strip()

                    try:
                        dep_dt = (
                            pd.to_datetime(raw_date).tz_localize('UTC')
                            if pd.to_datetime(raw_date).tzinfo is None
                            else pd.to_datetime(raw_date)
                        )
                    except Exception:
                        st.sidebar.error(
                            f"⚠️ **Invalid Deposit Date** at row {row_idx + 1}: `'{raw_date}'`."
                        )
                        has_ledger_error = True
                        continue

                    try:
                        dep_amt = float(raw_amount)
                        if dep_amt < 0:
                            raise ValueError("Negative deposit")
                    except Exception:
                        st.sidebar.error(
                            f"⚠️ **Invalid Deposit Amount** at row {row_idx + 1}: `'{raw_amount}'`."
                        )
                        has_ledger_error = True
                        continue

                    dep_events.append({'time': dep_dt, 'amount': dep_amt})

        if has_ledger_error:
            st.warning(
                "Please correct invalid deposit entries in the sidebar to recalculate segment boundaries."
            )
            return

        dep_events = sorted(dep_events, key=lambda x: x['time'])

        if dep_events:
            initial_capital = dep_events[0]['amount']
        else:
            initial_capital = 10.0

        segments = {}
        first_trade_time = full_trades_df['exit_time'].min()
        running_carried_equity = initial_capital

        if not dep_events:
            segments["Segment 1: Full History"] = {
                'trades': full_trades_df,
                'start_cap': initial_capital,
                'start_date': first_trade_time,
            }
        else:
            for i in range(len(dep_events)):
                curr_dep = dep_events[i]
                start_t = curr_dep['time']
                end_t = (
                    dep_events[i + 1]['time']
                    if (i + 1) < len(dep_events)
                    else pd.Timestamp('2099-12-31').tz_localize('UTC')
                )
                date_label = (
                    f"{start_t.strftime('%Y-%m-%d')} to {end_t.strftime('%Y-%m-%d')}"
                    if (i + 1) < len(dep_events)
                    else f"From {start_t.strftime('%Y-%m-%d')} (Current Lifecycle)"
                )

                sub_trades = full_trades_df[
                    (full_trades_df['exit_time'] >= start_t)
                    & (full_trades_df['exit_time'] < end_t)
                ].reset_index(drop=True)

                if i == 0:
                    seg_start_cap = curr_dep['amount']
                else:
                    seg_start_cap = running_carried_equity + curr_dep['amount']

                seg_name = f"Segment {len(segments)+1}: {date_label} [Start Equity: ${seg_start_cap:,.2f}]"
                segments[seg_name] = {
                    'trades': sub_trades,
                    'start_cap': seg_start_cap,
                    'start_date': start_t,
                }

                pnl_col = (
                    'net_pnl' if 'net_pnl' in sub_trades.columns else 'pnl'
                )
                seg_net_pnl = (
                    sub_trades[pnl_col].sum() if not sub_trades.empty else 0.0
                )
                running_carried_equity = max(
                    0.0, seg_start_cap + seg_net_pnl
                )

            segments["All Segments (Combined View)"] = {
                'trades': full_trades_df,
                'start_cap': initial_capital,
                'start_date': first_trade_time,
            }

        # 2. Sidebar Segment Switcher
        st.sidebar.markdown("---")
        segment_names = list(segments.keys())
        default_index = (
            segment_names.index("All Segments (Combined View)")
            if "All Segments (Combined View)" in segment_names
            else 0
        )

        selected_seg_name = st.sidebar.selectbox(
            "🎯 Select Active Segment",
            options=segment_names,
            index=default_index,
            key="active_segment_select",
        )

        active_segment = segments[selected_seg_name]
        trades_df = active_segment['trades']
        seg_start_cap = active_segment['start_cap']

        if trades_df.empty:
            st.warning(
                f"No trades recorded within **{selected_seg_name}**."
            )
            return

        # 3. Prepare Segment Timeline
        timeline_pnl_col = (
            'net_pnl' if 'net_pnl' in trades_df.columns else 'pnl'
        )
        timeline_df = trades_df[
            ['exit_time', 'pnl', timeline_pnl_col, 'pair', 'exit_type']
        ].copy()
        timeline_df = timeline_df.rename(
            columns={'exit_time': 'time', timeline_pnl_col: 'net_change'}
        ).sort_values('time')

        timeline_df['cum_pnl'] = timeline_df['pnl'].cumsum()
        timeline_df['equity'] = (
            seg_start_cap + timeline_df['net_change'].cumsum()
        )

        blown_trades = timeline_df[timeline_df['equity'] <= 0].copy()
        has_blown = not blown_trades.empty
        first_blowout_time = (
            blown_trades['time'].iloc[0] if has_blown else None
        )

        timeline_df['peak'] = timeline_df['equity'].cummax()
        timeline_df['drawdown'] = timeline_df['equity'] - timeline_df['peak']
        timeline_df['drawdown_pct'] = (
            timeline_df['drawdown'] / timeline_df['peak']
        ) * 100.0

        # 4. Streamlit Tabs Layout
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Executive Summary",
            "🔀 Pair Performance",
            "⏰ Session Dynamics",
            "⏳ Session Transitions & Holds",
            "📜 Audit & Trade Logs",
            "⚙️ Settings & Risk",
        ])

        # 5. Delegate directly to root-level trade/ modules
        with tab1:
            render_executive_summary_tab(
                trades_df,
                timeline_df,
                seg_start_cap,
                selected_seg_name,
                has_blown,
                first_blowout_time,
            )
        with tab2:
            render_pair_performance_tab(trades_df, selected_seg_name)
        with tab3:
            render_session_dynamics_tab(trades_df, selected_seg_name)
        with tab4:
            render_session_transitions_tab(trades_df, selected_seg_name)
        with tab5:
            render_audit_trade_logs_tab(
                trades_df, blown_trades, has_blown, selected_seg_name
            )
        with tab6:
            render_settings_risk_tab(
                trades_df, timeline_df, seg_start_cap, selected_seg_name
            )
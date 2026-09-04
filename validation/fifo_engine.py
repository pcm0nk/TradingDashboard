import pandas as pd
import numpy as np
from typing import Tuple


def consolidate_position_trades(clean_trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups sub-fragment FIFO matched executions (partial TPs, scaled entries)
    into single consolidated position records representing full entry-to-flat lifecycles.
    """
    if clean_trades_df is None or clean_trades_df.empty:
        return pd.DataFrame()

    df = clean_trades_df.copy()
    consolidated_positions = []

    for pair, grp in df.groupby('pair'):
        # Sort chronologically by entry time
        grp = grp.sort_values(['entry_time', 'exit_time']).reset_index(drop=True)

        current_group = []
        pos_direction = None

        for _, row in grp.iterrows():
            if not current_group:
                current_group.append(row)
                pos_direction = row['direction']
                continue

            prev_row = current_group[-1]

            # Group condition: contiguous trade in same pair & direction where
            # the next entry occurs before or during the previous exit window
            if row['direction'] == pos_direction and row['entry_time'] <= prev_row['exit_time']:
                current_group.append(row)
            else:
                # Flush existing grouped position
                consolidated_positions.append(_aggregate_group(current_group))
                current_group = [row]
                pos_direction = row['direction']

        if current_group:
            consolidated_positions.append(_aggregate_group(current_group))

    cons_df = pd.DataFrame(consolidated_positions)
    if not cons_df.empty:
        cons_df = cons_df.sort_values('exit_time').reset_index(drop=True)

    return cons_df


def _aggregate_group(group_rows: list) -> dict:
    """Helper function to aggregate multiple partial fill records into one position."""
    grp_df = pd.DataFrame(group_rows)
    total_qty = grp_df['quantity'].sum()

    # Weighted average entry and exit prices
    weighted_entry = (grp_df['entry_price'] * grp_df['quantity']).sum() / total_qty if total_qty > 0 else grp_df['entry_price'].iloc[0]
    weighted_exit = (grp_df['exit_price'] * grp_df['quantity']).sum() / total_qty if total_qty > 0 else grp_df['exit_price'].iloc[-1]

    total_pnl = grp_df['pnl'].sum()
    total_fees_entry = grp_df['fees_entry'].sum()
    total_fees_exit = grp_df['fees_exit'].sum()
    total_fees = grp_df['fees_total'].sum()

    entry_time = grp_df['entry_time'].min()
    exit_time = grp_df['exit_time'].max()

    hold_minutes = 0.0
    if pd.notnull(entry_time) and pd.notnull(exit_time):
        hold_minutes = max(0.0, (exit_time - entry_time).total_seconds() / 60.0)

    # Classify position exit outcome
    if (grp_df['exit_type'] == 'Liquidation').any():
        exit_type = 'Liquidation'
    elif total_pnl > 0:
        exit_type = 'TP'
    elif total_pnl < 0:
        exit_type = 'SL'
    else:
        exit_type = 'Breakeven'

    return {
        'pair': grp_df['pair'].iloc[0],
        'entry_time': entry_time,
        'exit_time': exit_time,
        'direction': grp_df['direction'].iloc[0],
        'exit_direction': grp_df['exit_direction'].iloc[-1],
        'entry_price': weighted_entry,
        'exit_price': weighted_exit,
        'quantity': total_qty,
        'pnl': total_pnl,
        'fees_entry': total_fees_entry,
        'fees_exit': total_fees_exit,
        'fees_total': total_fees,
        'net_pnl': total_pnl,
        'hold_minutes': hold_minutes,
        'exit_type': exit_type,
        'sub_fill_count': len(grp_df)  # Tracks how many partial fills were merged
    }


def process_fifo_trades(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes First-In-First-Out (FIFO) trade matching across pairs.

    Returns:
        tuple: (clean_trades_df, consolidated_trades_df, anomalies_df)
    """
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df = df.copy()

    # Standardize direction sets
    open_dirs = {
        "OPEN_LONG", "OPEN_SHORT", "OPEN LONG", "OPEN SHORT",
        "BUY", "LONG", "Open Long", "Open Short"
    }
    close_dirs = {
        "CLOSE_LONG", "CLOSE_SHORT", "CLOSE LONG", "CLOSE SHORT",
        "BURST_LIQUIDATE_LONG", "BURST_LIQUIDATE_SHORT",
        "OFFSET_LIQUIDATE_SHORT", "FORCE_LIQUIDATE_SHORT",
        "FORCE_LIQUIDATE_LONG", "OFFSET_LIQUIDATE_LONG",
        "SELL", "SHORT", "Close Long", "Close Short"
    }

    clean_trades = []
    anomalies = []

    # Process each trading symbol/pair independently
    for pair, grp in df.groupby('pair'):
        open_queue = []

        for row_idx, row in grp.iterrows():
            direction = str(row.get('direction', '')).strip()
            fill_time = row.get('fill_time')
            price = float(row.get('price', 0.0))
            quantity = float(row.get('quantity', 0.0))
            pnl = float(row.get('pnl', 0.0))
            fees = float(row.get('fees', 0.0))

            # ── 1. HANDLE ENTRY FILLS ───────────────────────────────────────
            if direction in open_dirs:
                open_queue.append({
                    'source_row': row_idx,
                    'pair': pair,
                    'fill_time': fill_time,
                    'direction': direction,
                    'price': price,
                    'original_qty': quantity,
                    'remaining_qty': quantity,
                    'fees': fees
                })

            # ── 2. HANDLE EXIT FILLS ────────────────────────────────────────
            elif direction in close_dirs:
                if not open_queue:
                    anomalies.append({
                        'source_row': row_idx,
                        'pair': pair,
                        'fill_time': fill_time,
                        'direction': direction,
                        'price': price,
                        'quantity': quantity,
                        'anomaly_type': 'Orphan Close',
                        'reason': 'Missing prior opening trade entry in dataset'
                    })
                    continue

                close_qty_remaining = quantity
                original_close_qty = quantity

                while close_qty_remaining > 1e-8 and open_queue:
                    entry = open_queue[0]
                    matched_qty = min(entry['remaining_qty'], close_qty_remaining)

                    qty_ratio_entry = matched_qty / entry['original_qty'] if entry['original_qty'] > 0 else 1.0
                    qty_ratio_exit = matched_qty / original_close_qty if original_close_qty > 0 else 1.0

                    fees_entry = entry['fees'] * qty_ratio_entry
                    fees_exit = fees * qty_ratio_exit
                    pnl_allocated = pnl * qty_ratio_exit

                    hold_minutes = 0.0
                    if pd.notnull(fill_time) and pd.notnull(entry['fill_time']):
                        hold_minutes = max(0.0, (fill_time - entry['fill_time']).total_seconds() / 60.0)

                    if 'LIQUIDATE' in direction.upper():
                        exit_type = 'Liquidation'
                    elif pnl_allocated > 0:
                        exit_type = 'TP'
                    elif pnl_allocated < 0:
                        exit_type = 'SL'
                    else:
                        exit_type = 'Breakeven'

                    clean_trades.append({
                        'pair': pair,
                        'entry_time': entry['fill_time'],
                        'exit_time': fill_time,
                        'direction': entry['direction'],
                        'exit_direction': direction,
                        'entry_price': entry['price'],
                        'exit_price': price,
                        'quantity': matched_qty,
                        'pnl': pnl_allocated,
                        'fees_entry': fees_entry,
                        'fees_exit': fees_exit,
                        'fees_total': fees_entry + fees_exit,
                        'net_pnl': pnl_allocated,
                        'hold_minutes': hold_minutes,
                        'exit_type': exit_type
                    })

                    entry['remaining_qty'] -= matched_qty
                    close_qty_remaining -= matched_qty

                    if entry['remaining_qty'] <= 1e-8:
                        open_queue.pop(0)

                if close_qty_remaining > 1e-8:
                    anomalies.append({
                        'source_row': row_idx,
                        'pair': pair,
                        'fill_time': fill_time,
                        'direction': direction,
                        'price': price,
                        'quantity': round(close_qty_remaining, 8),
                        'anomaly_type': 'Orphan Close (Partial)',
                        'reason': 'Exhausted open order queue before fully matching exit quantity'
                    })

        # ── 3. HANDLE UNCLOSED OPEN INVENTORY ───────────────────────────────
        for unclosed_entry in open_queue:
            if unclosed_entry['remaining_qty'] > 1e-8:
                anomalies.append({
                    'source_row': unclosed_entry['source_row'],
                    'pair': pair,
                    'fill_time': unclosed_entry['fill_time'],
                    'direction': unclosed_entry['direction'],
                    'price': unclosed_entry['price'],
                    'quantity': round(unclosed_entry['remaining_qty'], 8),
                    'anomaly_type': 'Orphan Open',
                    'reason': 'Unmatched position inventory remaining at end of dataset window'
                })

    clean_trades_df = pd.DataFrame(clean_trades)
    if not clean_trades_df.empty:
        clean_trades_df = clean_trades_df.sort_values('exit_time').reset_index(drop=True)

    # Generate consolidated position dataset
    consolidated_trades_df = consolidate_position_trades(clean_trades_df)

    anomalies_df = pd.DataFrame(anomalies)
    if not anomalies_df.empty:
        anomalies_df = anomalies_df.sort_values('source_row').reset_index(drop=True)

    return clean_trades_df, consolidated_trades_df, anomalies_df
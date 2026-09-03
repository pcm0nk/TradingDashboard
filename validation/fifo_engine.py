import pandas as pd
import numpy as np
from typing import Tuple


def process_fifo_trades(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes First-In-First-Out (FIFO) trade matching across pairs.

    Returns:
        tuple: (clean_trades_df, anomalies_df)
            - clean_trades_df: Only fully resolved matched entry-exit trade pairs.
            - anomalies_df: Table of orphan closes (missing opens) and unclosed opens.
    """
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame()

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
                # ANOMALY: Exit fill occurs with NO prior open inventory
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

                    # Pro-rate entry/exit fees and PnL for partial fills
                    qty_ratio_entry = matched_qty / entry['original_qty'] if entry['original_qty'] > 0 else 1.0
                    qty_ratio_exit = matched_qty / original_close_qty if original_close_qty > 0 else 1.0

                    fees_entry = entry['fees'] * qty_ratio_entry
                    fees_exit = fees * qty_ratio_exit
                    pnl_allocated = pnl * qty_ratio_exit

                    hold_minutes = 0.0
                    if pd.notnull(fill_time) and pd.notnull(entry['fill_time']):
                        hold_minutes = max(0.0, (fill_time - entry['fill_time']).total_seconds() / 60.0)

                    # Categorize Exit Reason
                    if 'LIQUIDATE' in direction.upper():
                        exit_type = 'Liquidation'
                    elif pnl_allocated > 0:
                        exit_type = 'TP'
                    elif pnl_allocated < 0:
                        exit_type = 'SL'
                    else:
                        exit_type = 'Breakeven'

                    # Record clean matched trade pair
                    # Fees are tracked separately; PnL is untouched (fees settled against margin)
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
                        'net_pnl': pnl_allocated,  # Untouched PnL (fees deducted from margin/wallet)
                        'hold_minutes': hold_minutes,
                        'exit_type': exit_type
                    })

                    # Deduct matched quantity from queue & current close order
                    entry['remaining_qty'] -= matched_qty
                    close_qty_remaining -= matched_qty

                    if entry['remaining_qty'] <= 1e-8:
                        open_queue.pop(0)

                # ANOMALY: Exit fill had partial or total quantity remaining after exhausting open queue
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

        # ── 3. HANDLE UNCLOSED OPEN INVENTORY AT END OF FILE ───────────────
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

    # Construct Clean Trades DataFrame
    clean_trades_df = pd.DataFrame(clean_trades)
    if not clean_trades_df.empty:
        clean_trades_df = clean_trades_df.sort_values('exit_time').reset_index(drop=True)

    # Construct Anomalies DataFrame
    anomalies_df = pd.DataFrame(anomalies)
    if not anomalies_df.empty:
        anomalies_df = anomalies_df.sort_values('source_row').reset_index(drop=True)

    return clean_trades_df, anomalies_df
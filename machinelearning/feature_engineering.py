import numpy as np
import pandas as pd


def extract_trade_features(
    trades_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Transforms trade records into a scikit-learn feature matrix X and target label y.

    Note on Fees: PnL values are consumed directly from the input DataFrame
    without secondary fee deductions, matching exchange margin/equity settlement logic.

    Target (y): 1 for Win (net_pnl > 0), 0 for Loss/Breakeven
    Features (X): Hold duration, entry hour, day of week, fee ratio burden,
                  trade direction, and one-hot encoded trading pairs.
    """
    if trades_df is None or trades_df.empty:
        return pd.DataFrame(), pd.Series(dtype=int)

    df = trades_df.copy()

    # 1. Target Vector Definition (1 = Win, 0 = Loss/BE)
    pnl_col = 'net_pnl' if 'net_pnl' in df.columns else 'pnl'
    y = (df[pnl_col] > 0).astype(int)

    # 2. Extract Numerical Features
    X = pd.DataFrame(index=df.index)

    X['hold_minutes'] = df.get('hold_minutes', 0.0)
    X['quantity'] = df.get('quantity', 0.0)
    X['entry_price'] = df.get('entry_price', 0.0)

    # Fee Impact Ratio (Total Open + Close Fees relative to PnL magnitude)
    if 'fees_total' in df.columns and pnl_col in df.columns:
        pnl_abs = df[pnl_col].abs()
        X['fee_ratio'] = np.where(
            pnl_abs > 0, df['fees_total'].abs() / pnl_abs, 0.0
        )
    else:
        X['fee_ratio'] = 0.0

    # 3. Extract Temporal Features from Entry Time
    if 'entry_time' in df.columns:
        entry_dt = pd.to_datetime(df['entry_time'], errors='coerce')
        X['entry_hour'] = entry_dt.dt.hour.fillna(0).astype(int)
        X['entry_dayofweek'] = entry_dt.dt.dayofweek.fillna(0).astype(int)

    # 4. Binary Direction Encoding (1 = LONG/BUY, 0 = SHORT/SELL)
    if 'direction' in df.columns:
        X['direction_LONG'] = (
            df['direction']
            .astype(str)
            .str.contains('LONG|BUY', case=False, na=False)
            .astype(int)
        )

    # 5. One-Hot Encoding for Trading Pairs
    if 'pair' in df.columns:
        pair_dummies = pd.get_dummies(
            df['pair'], prefix='pair', drop_first=False
        ).astype(int)
        X = pd.concat([X, pair_dummies], axis=1)

    # 6. Fill NaN values safely
    X = X.fillna(0.0)

    return X, y
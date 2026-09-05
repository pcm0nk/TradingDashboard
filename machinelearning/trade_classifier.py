import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit


def train_trade_classifier(X: pd.DataFrame, y: pd.Series) -> dict:
    """Trains a Random Forest classifier to predict trade outcomes (Win vs Loss)

    and computes feature importance metrics using TimeSeriesSplit cross-validation.
    """
    if X.empty or y.empty or len(X) < 10:
        return {"status": "insufficient_data"}

    # Use TimeSeriesSplit cross-validation to preserve temporal order
    n_samples = len(X)
    n_splits = min(3, max(2, n_samples // 5))

    tscv = TimeSeriesSplit(n_splits=n_splits)
    model = RandomForestClassifier(
        n_estimators=100, max_depth=5, random_state=42
    )

    accuracies = []
    for train_index, test_index in tscv.split(X):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        # Skip split if training set only contains 1 class
        if len(y_train.unique()) < 2:
            continue

        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        accuracies.append(accuracy_score(y_test, preds))

    mean_cv_acc = float(np.mean(accuracies)) if accuracies else 0.0

    # Fit final model on full dataset for feature importances
    model.fit(X, y)
    feature_importances = pd.Series(
        model.feature_importances_, index=X.columns
    ).sort_values(ascending=False)

    return {
        "status": "success",
        "model": model,
        "mean_cv_accuracy": mean_cv_acc,
        "feature_importances": feature_importances,
    }


def resolve_trade_columns(df: pd.DataFrame) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Helper utility to dynamically locate PnL, Volume, Open Time, Exit Time, and Direction

    columns regardless of whether data comes from FIFO engines or trades_df.
    """
    # 1. PnL Column Resolution
    pnl_col = next(
        (
            c
            for c in [
                "net_pnl",
                "pnl",
                "net_change",
                "PnL",
                "Profit",
                "net_profit",
                "realized_pnl",
            ]
            if c in df.columns
        ),
        None,
    )

    # 2. Volume Column Resolution
    vol_col = next(
        (
            c
            for c in [
                "volume",
                "vol",
                "size",
                "lots",
                "Volume",
                "Size",
                "position_size",
                "qty",
                "quantity",
            ]
            if c in df.columns
        ),
        None,
    )

    # 3. Open/Entry Time Column Resolution
    open_col = next(
        (
            c
            for c in [
                "entry_time",
                "open_time",
                "Open Time",
                "open_date",
                "time",
                "Entry Time",
            ]
            if c in df.columns
        ),
        None,
    )

    # 4. Exit/Close Time Column Resolution
    exit_col = next(
        (
            c
            for c in [
                "exit_time",
                "close_time",
                "Close Time",
                "close_date",
                "Exit Time",
            ]
            if c in df.columns
        ),
        None,
    )

    # 5. Direction Column Resolution
    dir_col = next(
        (
            c
            for c in [
                "type",
                "direction",
                "side",
                "Type",
                "Side",
                "trade_type",
                "Direction",
            ]
            if c in df.columns
        ),
        None,
    )

    return pnl_col, vol_col, open_col, exit_col, dir_col
# Algorithmic Trading Analytics Dashboard (FIFO Engine)

An end-to-end, high-performance trading analytics platform built with Streamlit and Python. This system ingests raw trade fill logs from crypto and futures exchanges, executes precise **First-In-First-Out (FIFO)** order matching to reconstruct individual trade lifecycles, and provides deep institutional-grade performance analytics, interactive equity charts, and drawdown modeling.

---

## Architecture & Project Structure

The project is modularized into dedicated engines for data ingestion, trade matching, mathematical calculations, and Streamlit visualization components.

```text
.
├── app.py                      # Main Streamlit application entry point & layout routing
├── modules/
│   ├── engine/
│   │   ├── fifo_engine.py      # Core FIFO trade-matching algorithm & anomaly detection
│   │   └── processing.py       # Data cleaning, normalization, & timeline builder
│   ├── tabs/
│   │   ├── executive_summary.py# High-level KPIs, equity curve, & fee breakdown
│   │   ├── trade_analysis.py   # Individual trade log table, duration, & win/loss stats
│   │   └── anomalies.py        # Table and breakdown of orphan opens/closes
│   └── charts/
│       └── equity_charts.py    # Plotly interactive cumulative equity & drawdown visualizers
├── requirements.txt            # Python dependencies (pandas, streamlit, plotly, numpy)
└── README.md                   # Project documentation

```

---

## Core Features & Technical Capabilities

* **First-In-First-Out (FIFO) Order Matching Engine:**
* Matches partial and full position entries (`OPEN_LONG`, `OPEN_SHORT`, `BUY`) against closing fills (`CLOSE_LONG`, `CLOSE_SHORT`, `SELL`, `LIQUIDATION`).
* Pro-rates entry and exit fees dynamically for partial position fills.


* **Exchange Fee & Settlement Precision:**
* Handles exchanges where opening fees are settled against allocated margin/wallet balance and exit fees are billed separately upon close.
* Preserves raw trade P&L without double-deducting execution commissions.


* **Anomaly & Exception Detection:**
* Tracks and isolates **Orphan Closes** (exits without preceding entry fills in the dataset window) and **Orphan Opens** (unclosed inventory remaining at dataset end).


* **Interactive Visualization:**
* Real-time equity curve tracking starting from segment initial capital.
* Peak-to-trough drawdown visualization with account blowout detection (equity $\le \$0$).


* **Flexible Multi-Segment Filtering:**
* Symbol/pair filtering and time-window segmentations for targeted strategy backtesting analysis.



---

## Interactive Analytics & Tab Breakdown

### 1. Executive Summary

* **Realized P/L:** Cumulative net profit/loss across all closed trade fills.
* **Account Equity:** Current total account equity ($\text{Starting Capital} + \text{Realized P/L}$).
* **Win Rate & Sharpe Ratio:** Key risk-adjusted return and performance metrics.
* **Execution Fees:** Separate cards for **Open Fees** and **Close Fees** for accounting transparency.
* **Interactive Equity Curve & Drawdown Chart:** Built using Plotly for zooming and inspection.

### 2. Trade Analysis

* **Trade Log Table:** Complete list of matched trades showing pair, direction, entry/exit price, position size, P&L, hold duration, and exit type (`TP`, `SL`, `Breakeven`, `Liquidation`).
* **Performance Distribution:** Granular win/loss statistics, average hold times, and payout ratios.

### 3. Anomalies & Data Diagnostics

* Inspects data gaps, missing execution logs, or partial queue mismatches to ensure absolute data integrity.

---

## Core Concepts & Key Formulas

### 1. FIFO Trade Allocation & Pro-Rating

For a matched quantity $Q_{\text{match}}$ between an entry fill of size $Q_{\text{entry}}$ and exit fill of size $Q_{\text{exit}}$:

$$\text{Fee}_{\text{entry, allocated}} = \text{Fee}_{\text{entry, raw}} \times \left( \frac{Q_{\text{match}}}{Q_{\text{entry}}} \right)$$

$$\text{Fee}_{\text{exit, allocated}} = \text{Fee}_{\text{exit, raw}} \times \left( \frac{Q_{\text{match}}}{Q_{\text{exit}}} \right)$$

$$\text{PnL}_{\text{allocated}} = \text{PnL}_{\text{exit, raw}} \times \left( \frac{Q_{\text{match}}}{Q_{\text{exit}}} \right)$$

### 2. Annualized Sharpe Ratio

Calculated trade-by-trade across the trade return series:

$$\text{Sharpe Ratio} = \frac{\bar{R}_{\text{trade}} - R_f}{\sigma_{\text{trade}}} \times \sqrt{365}$$

Where $\bar{R}_{\text{trade}}$ is the mean trade P&L, $\sigma_{\text{trade}}$ is the standard deviation of trade P&L, and $R_f$ is the risk-free rate ($0.0$).

### 3. Drawdown Percentage

At any point $t$ along the timeline:

$$\text{Drawdown}_t = \frac{\text{Equity}_t - \text{Peak Equity}_t}{\text{Peak Equity}_t}$$

---

## Installation & Deployment

### Local Setup

1. **Clone the Repository:**
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

```


2. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


3. **Run the Streamlit Dashboard:**
```bash
streamlit run app.py

```

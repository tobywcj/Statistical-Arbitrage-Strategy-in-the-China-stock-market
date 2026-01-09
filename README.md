# SSE Statistical Arbitrage Strategy MVP

A professional quantitative trading system designed for the Shanghai Stock Exchange (SSE). This project identifies statistical co-movements between stocks and executes a dollar-neutral mean-reversion strategy based on cluster residuals.

## 🚀 Overview

This system automates the end-to-end pipeline of a Statistical Arbitrage strategy:
1.  **Data Ingestion**: Automated backfilling of historical OHLCV data from Yahoo Finance into MongoDB.
2.  **Asset Clustering**: Grouping stocks using **Spectral** or **Hierarchical** clustering to identify statistical "neighborhoods."
3.  **Signal Generation**: Calculating spread Z-scores based on cumulative residuals from cluster benchmarks.
4.  **Vectorized Backtesting**: Rapid performance simulation with adjustable thresholds and risk metrics.
5.  **Interactive Dashboard**: A Streamlit-based UI for research and analysis.

## 🛠 Tech Stack

- **Lanuage**: Python 3.12+
- **Database**: MongoDB (Time-series storage)
- **API**: FastAPI (Programmatic data access)
- **Frontend**: Streamlit (Interactive Research Dashboard)
- **Data Source**: yfinance (Yahoo Finance)
- **Math/Stats**: Pandas, NumPy, Scikit-Learn

## 📂 Project Structure

- `app/`: Core logic including database connections, data providers, and analytics.
- `dashboard/`: Streamlit pages for Data Exploration, Clustering, and Backtesting.
- `scripts/`: Utility scripts for loading instruments and backfilling historical data.
- `docker-compose.yml`: Database orchestration.

## ⚙️ Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+ (Conda recommended)

### 2. Environment Setup
Clone the repo and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Start Database
```bash
docker compose up -d
```

### 4. Load Data
Populate the database with the SSE stock universe and fetch history:
```bash
# Load instrument list
python -m scripts.load_instruments

# Backfill 2 years of daily bars
python -m scripts.backfill_bars --years 2
```

### 5. Launch Dashboard
```bash
streamlit run dashboard/Home.py
```

## 📈 Methodology

- **Cointegration vs Correlation**: The strategy moves beyond simple correlation by focusing on co-movement stability within identified clusters.
- **Spectral Clustering**: Uses the Laplacian matrix of the correlation graph to find natural, non-linear groupings of stocks.
- **Mean Reversion**: Trades the **Z-Score** of the integrated residuals. A standard threshold of **Z=2.0** (95% outlier) is used for high-conviction entries.

## 📝 License
MIT License

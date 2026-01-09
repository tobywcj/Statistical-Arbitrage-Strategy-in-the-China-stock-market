# SSE Statistical Arbitrage Strategy MVP

A professional quantitative trading system designed for the Shanghai Stock Exchange (SSE). This project identifies statistical co-movements between stocks and executes a dollar-neutral mean-reversion strategy based on cluster residuals.

## 🚀 Overview

This system automates the end-to-end pipeline of a Statistical Arbitrage strategy:
1.  **Data Ingestion**: High-performance MongoDB storage for local research, with an automatic **Real-time Fallback Mode** via Yahoo Finance for cloud deployment.
2.  **Asset Clustering**: Identifying statistical "neighborhoods" using **Spectral** or **Hierarchical** clustering, moving beyond traditional sector classifications.
3.  **Signal Generation**: Calculating spread Z-scores based on cumulative residuals from cluster benchmarks.
4.  **Vectorized Backtesting**: Rapid performance simulation with adjustable outliers (Z=2.0) and risk metrics.
5.  **Interactive Dashboard**: A multi-mode Streamlit UI for deep-dive research and strategy validation.

## ✨ Key Features

- **🔌 Hybrid Data Backend**: 
    - **Database Mode**: Uses local MongoDB for sub-second data loading and high-performance research.
    - **Direct-Fetch Mode**: Fetches data on-the-fly from Yahoo Finance. Perfect for Streamlit Cloud and instant demos without DB setup.
- **📅 8-Year Data Reach**: Selectable lookback periods from 1 to 8 years across all modules.
- **🛡️ Data Stewardship**: Live database coverage indicators show you exactly what dates are stored in your local repository.
- **🧬 Advanced Analytics**: Comparison between graph-based (Spectral) and tree-based (Hierarchical) clustering.
- **🧪 Strategy Prototyping**: Adjustable Z-score thresholds and lookback windows for signal refinement.

## 📂 Project Structure

- `app/`: Core logic including database connections, fallback providers, and analytics engine.
- `dashboard/`: Streamlit pages for Data Exploration, Clustering, and Backtesting.
- `scripts/`: Utility scripts for instrument loading and historical backfilling.
- `docker-compose.yml`: Local MongoDB orchestration.

## ⚙️ Getting Started

### 1. Prerequisites
- Docker & Docker Compose (Optional for Demo Mode)
- Python 3.12+ (Conda recommended)

### 2. Environment Setup
```bash
# Clone the repository and install dependencies
pip install -r requirements.txt
```

### 3. Usage Modes

#### A. Instant Demo (No DB needed)
Simply launch the dashboard and select **"Real-time Yahoo"** in the sidebar:
```bash
streamlit run dashboard/Home.py
```

#### B. High-Performance Research (With DB)
```bash
# 1. Start MongoDB
docker compose up -d

# 2. Load instrument list
python -m scripts.load_instruments

# 3. Backfill data (e.g., 2 years)
python -m scripts.backfill_bars --years 2

# 4. Launch Dashboard
streamlit run dashboard/Home.py
```

## 📈 Methodology

- **Integrated Residuals**: The strategy trades the **cumulative sum of residuals** (the spread), ensuring stable mean-reversion signals.
- **Spectral Clustering**: Uses the Laplacian matrix of the correlation graph to find natural, non-linear groupings of stocks, capturing hidden statistical relationships.
- **High-Conviction Entry**: Recommends a threshold of **Z=2.0** (95% outlier) to ensure statistical significance and minimize noise.

## 📝 License
MIT License

import pandas as pd
import numpy as np
def run_backtest(returns: pd.DataFrame, signals: pd.DataFrame, clusters: dict) -> dict:
    """
    Vectorized backtest.
    signals: DataFrame of 1, -1, 0 at time t.
    returns: DataFrame of returns at time t.
    
    Strategy: 
    rebalance at t based on signal(t). Return realized at t+1.
    """
    # Shift signals to align with returns. 
    # Signal calculated at Close t uses data up to t. 
    # We enter position at Close t (or Open t+1).
    # Return realized is r_{t+1}.
    
    # Weights: Equal weight within cluster?
    # Spec says: "Equal-weight longs and equal-weight shorts within each cluster"
    # To keep it dollar neutral per cluster implies complex weighting.
    # MVP simplification: 
    # For each stock, if signal is 1, weight = 1/N_total in portfolio? Or 1/N_cluster?
    # Let's simplify: 
    # Just assume unit investment per signal for raw pnl, then normalize?
    
    # Let's implementation:
    # positions = signals.shift(1) (positions held at t, determined by signal t-1)
    
    positions = signals.shift(1).fillna(0)
    
    # Strategy Return = positions * returns
    # But wait, we need to handle weighting.
    # If we just sum(positions * returns), that assumes variable leverage.
    # Let's normalize leverage daily to 1 (gross magnitude).
    
    gross_exposure = positions.abs().sum(axis=1)
    
    # Avoid div by zero
    weights = positions.div(gross_exposure, axis=0).fillna(0)
    
    # Portfolio Return
    port_rets = (weights * returns).sum(axis=1)
    
    # Metrics
    cumulative_ret = (1 + port_rets).cumprod()
    
    total_return = cumulative_ret.iloc[-1] - 1 if not cumulative_ret.empty else 0
    annualized_return = port_rets.mean() * 252
    sharpe = (port_rets.mean() / port_rets.std()) * (252**0.5) if port_rets.std() != 0 else 0
    
    # Drawdown
    running_max = cumulative_ret.cummax()
    drawdown = (cumulative_ret - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Turnover
    # change in weights
    turnover = weights.diff().abs().sum(axis=1).mean()
    
    return {
        "cumulative_returns": cumulative_ret,
        "daily_returns": port_rets,
        "metrics": {
            "Total Return": total_return,
            "Annualized Return": annualized_return,
            "Sharpe Ratio": sharpe,
            "Max Drawdown": max_drawdown,
            "Daily Turnover": turnover
        }
    }
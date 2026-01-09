import pandas as pd
import numpy as np


def calculate_cluster_returns(returns: pd.DataFrame, clusters: dict) -> pd.DataFrame:
    """
    Calculate average return for each cluster.
    """
    cluster_rets = pd.DataFrame(index=returns.index)
    
    for c_id, tickers in clusters.items():
        # Only use tickers required (some might not be in returns if missing data)
        valid_tickers = [t for t in tickers if t in returns.columns]
        if not valid_tickers:
            continue
        cluster_rets[c_id] = returns[valid_tickers].mean(axis=1)
        
    return cluster_rets

def calculate_residuals(returns: pd.DataFrame, cluster_returns: pd.DataFrame, clusters: dict) -> pd.DataFrame:
    """
    Calculate residuals: r_i - r_cluster_mean
    """
    residuals = pd.DataFrame(index=returns.index)
    
    for c_id, tickers in clusters.items():
        if c_id not in cluster_returns.columns:
            continue
            
        valid_tickers = [t for t in tickers if t in returns.columns]
        for t in valid_tickers:
            residuals[t] = returns[t] - cluster_returns[c_id]
            
    return residuals

def calculate_z_scores(residuals: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    Calculate Z-Score of the integrated residuals (spread).
    Spread s_t = sum(residuals)
    Z = (s_t - roll_mean(s)) / roll_std(s)
    """
    # Integrate residuals -> spread
    spread = residuals.cumsum()
    
    # Rolling stats
    roll_mean = spread.rolling(window=lookback).mean()
    roll_std = spread.rolling(window=lookback).std()
    
    z_scores = (spread - roll_mean) / roll_std
    return z_scores
    
def generate_signals(z_scores: pd.DataFrame, entry_threshold: float) -> pd.DataFrame:
    """
    Long if Z < -entry
    Short if Z > entry
    Values: 1 (Long), -1 (Short), 0 (Neutral)
    """
    signals = pd.DataFrame(0, index=z_scores.index, columns=z_scores.columns)
    
    signals[z_scores < -entry_threshold] = 1
    signals[z_scores > entry_threshold] = -1
    
    return signals

import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import SpectralClustering



def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate log returns from a price matrix (Date Index, Ticker Columns).
    """
    return np.log(prices / prices.shift(1)).dropna()

def get_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix from returns.
    """
    return returns.corr()

def cluster_hierarchical(corr_matrix: pd.DataFrame, num_clusters: int) -> dict:
    """
    Perform Hierarchical Clustering using Ward linkage.
    Returns a dict mapping cluster_id -> list of tickers.
    """
    # Distance matrix
    # Typically dist = 1 - |corr| or sqrt(2*(1-corr))
    # Using 1 - |corr| as per spec
    dist = 1 - np.abs(corr_matrix)
    
    # Squareform is needed for linkage if input is distance matrix, 
    # but scipy linkage handles condensed distance matrix.
    # We need to extract the upper triangle.
    from scipy.spatial.distance import squareform
    condensed_dist = squareform(dist, checks=False) # checks=False to avoid error if not perfectly symmetric due to float
    
    Z = linkage(condensed_dist, method='ward')
    labels = fcluster(Z, t=num_clusters, criterion='maxclust')
    
    clusters = {}
    tickers = corr_matrix.index.tolist()
    
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(tickers[i])
        
    return clusters
    
def cluster_spectral(corr_matrix: pd.DataFrame, num_clusters: int) -> dict:
    """
    Perform Spectral Clustering.
    Returns a dict mapping cluster_id -> list of tickers.
    """
    # Affinity matrix A = (C + 1) / 2
    affinity = (corr_matrix + 1) / 2
    
    sc = SpectralClustering(
        n_clusters=num_clusters,
        affinity='precomputed',
        random_state=42,
        n_init=10
    )
    
    labels = sc.fit_predict(affinity)
    
    clusters = {}
    tickers = corr_matrix.index.tolist()
    
    for i, label in enumerate(labels):
        # make label int
        label = int(label)
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(tickers[i])
        
    return clusters
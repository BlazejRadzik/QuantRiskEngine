import numpy as np
import pandas as pd

def get_optimal_weights(returns: pd.DataFrame, strategy: str) -> list:
    num_assets = len(returns.columns)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    # Wymuszamy dywersyfikację: min 5%, max 45% (jeśli jest >=3 spółek)
    if num_assets >= 3:
        min_w, max_w = 0.05, 0.45
    else:
        min_w, max_w = 0.05, 0.95

    # GWARANCJA STABILNOŚCI: Zamiast zawodnego Scipy używamy siatki Monte Carlo.
    np.random.seed(42)
    # Generujemy 100 000 kombinacji wag w ułamku sekundy
    random_w = np.random.uniform(min_w, max_w, (100000, num_assets))
    random_w = random_w / random_w.sum(axis=1, keepdims=True)
    
    # Zostawiamy TYLKO te portfele, które rygorystycznie trzymają się limitów (żadnego 100%!)
    valid_indices = np.where((random_w >= min_w).all(axis=1) & (random_w <= max_w).all(axis=1))[0]
    
    if len(valid_indices) == 0:
        return [1.0 / num_assets] * num_assets
        
    valid_w = random_w[valid_indices]
    
    # Obliczamy zysk i ryzyko dla poprawnych portfeli
    port_returns = valid_w.dot(mean_returns.values)
    port_vols = np.sqrt(np.einsum('ij,ji->i', valid_w.dot(cov_matrix.values), valid_w.T))
    
    # Wybieramy zwycięzcę
    if strategy == 'min_vol':
        best_idx = np.argmin(port_vols)
    elif strategy == 'max_sharpe':
        best_idx = np.argmax(port_returns / port_vols)
    else:  # max_return
        best_idx = np.argmax(port_returns)
        
    best_weights = valid_w[best_idx]
    
    # Docięcie do 4 miejsc po przecinku, żeby wykres Plotly nigdy nie zwariował
    return np.round(best_weights, 4).tolist()


def simulate_monte_carlo(portfolio_returns, days=252, simulations=1000):
    mean_ret = portfolio_returns.mean()
    std_ret = portfolio_returns.std()
    
    if std_ret == 0 or pd.isna(std_ret):
        std_ret = 0.01
        
    drift = mean_ret - (0.5 * std_ret**2)
    
    np.random.seed(42)
    simulated_paths = np.random.normal(drift, std_ret, (days, simulations))
    price_paths = np.exp(np.cumsum(simulated_paths, axis=0))
    
    start = np.ones((1, simulations))
    price_paths = np.vstack([start, price_paths])
    
    mean_path = np.mean(price_paths, axis=1)
    worst_path = np.percentile(price_paths, 5, axis=1)
    best_path = np.percentile(price_paths, 95, axis=1)
    
    return mean_path, worst_path, best_path
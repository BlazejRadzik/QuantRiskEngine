import numpy as np
import pandas as pd
from scipy.optimize import minimize

def get_optimal_weights(returns: pd.DataFrame, strategy: str) -> np.ndarray:
    num_assets = len(returns.columns)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    def portfolio_vol(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    def portfolio_ret(weights):
        return np.sum(mean_returns * weights)

    # Wymuszamy dywersyfikację: min 5%, max 45% (jeśli jest >=3 spółek)
    if num_assets >= 3:
        bounds = tuple((0.05, 0.45) for _ in range(num_assets))
    else:
        bounds = tuple((0.05, 0.95) for _ in range(num_assets))
        
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    init_guess = np.array([1.0 / num_assets] * num_assets)

    if strategy == 'min_vol':
        res = minimize(lambda w: portfolio_vol(w), init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    elif strategy == 'max_sharpe':
        res = minimize(lambda w: -portfolio_ret(w)/portfolio_vol(w), init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    else:  # max_return
        res = minimize(lambda w: -portfolio_ret(w), init_guess, method='SLSQP', bounds=bounds, constraints=constraints)

    # BEZPIECZNIK NUMERYCZNY: Czyszczenie śmieci i wymuszenie sumy 100%
    weights = np.clip(res.x, 0.0, 1.0)
    weights = np.round(weights, 4)
    weights = weights / np.sum(weights) 
    
    return weights

def simulate_monte_carlo(portfolio_returns, days=252, simulations=1000):
    mean_ret = portfolio_returns.mean()
    std_ret = portfolio_returns.std()
    
    # Wzór Blacka-Scholesa z dryfem, żeby symulacja zachowywała się jak prawdziwa giełda
    drift = mean_ret - (0.5 * std_ret**2)
    
    simulated_paths = np.random.normal(drift, std_ret, (days, simulations))
    price_paths = np.exp(np.cumsum(simulated_paths, axis=0))
    
    # Zaczynamy wykres od punktu 1.0 (Dzień 0)
    start = np.ones((1, simulations))
    price_paths = np.vstack([start, price_paths])
    
    mean_path = np.mean(price_paths, axis=1)
    worst_path = np.percentile(price_paths, 5, axis=1)
    best_path = np.percentile(price_paths, 95, axis=1)
    
    return mean_path, worst_path, best_path
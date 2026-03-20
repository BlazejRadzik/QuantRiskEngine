import numpy as np
import pandas as pd

import numpy as np
import pandas as pd
from scipy.optimize import minimize

def get_optimal_weights(returns: pd.DataFrame, strategy: str) -> list:
    num_assets = len(returns.columns)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    
    # 1. Funkcje celu (to co minimalizujemy)
    def portfolio_volatility(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    def negative_sharpe(weights):
        p_ret = np.dot(weights, mean_returns)
        p_vol = portfolio_volatility(weights)
        return -p_ret / p_vol  # Minimalizujemy ujemny Sharpe = Maksymalizujemy dodatni

    def negative_return(weights):
        return -np.dot(weights, mean_returns)

    # 2. Ograniczenia i granice (Constraints & Bounds)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1}) # Suma wag = 100%
    
    # Dynamiczne granice: min 5%, max 45% (zabezpiecza przed ładowaniem wszystkiego w jedną spółkę)
    bound_val = (0.05, 0.45) if num_assets >= 3 else (0.05, 0.95)
    bounds = tuple(bound_val for _ in range(num_assets))
    
    # Startujemy od równego podziału
    init_guess = num_assets * [1. / num_assets]

    # 3. Wybór strategii
    if strategy == 'min_vol':
        target_func = portfolio_volatility
    elif strategy == 'max_sharpe':
        target_func = negative_sharpe
    else:  # max_return
        target_func = negative_return

    # 4. Optymalizacja
    result = minimize(target_func, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)

    if not result.success:
        # Fallback na równe wagi, jeśli solver zawiedzie
        return np.round(init_guess, 4).tolist()

    return np.round(result.x, 4).tolist()


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
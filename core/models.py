import numpy as np
import pandas as pd
from scipy.optimize import minimize

def get_optimal_weights(returns: pd.DataFrame, strategy: str) -> np.ndarray:
    """
    Oblicza optymalne wagi portfela za pomocą minimalizacji funkcji kosztu.
    """
    num_assets = len(returns.columns)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    # Funkcje pomocnicze dla optymalizatora
    def portfolio_performance(weights, mean_returns, cov_matrix):
        p_ret = np.sum(mean_returns * weights)
        p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return p_vol, p_ret

    def min_volatility_objective(weights, mean_returns, cov_matrix):
        return portfolio_performance(weights, mean_returns, cov_matrix)[0]

    def neg_sharpe_objective(weights, mean_returns, cov_matrix, risk_free=0):
        p_vol, p_ret = portfolio_performance(weights, mean_returns, cov_matrix)
        return -(p_ret - risk_free) / p_vol

    def max_return_objective(weights, mean_returns, cov_matrix):
        return -portfolio_performance(weights, mean_returns, cov_matrix)[1]

    # Ograniczenia: suma wag musi wynosić 1 (100%), żadna waga nie może być ujemna (brak shortowania)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    init_guess = np.array(num_assets * [1. / num_assets])

    # Wybór strategii
    if strategy == 'min_vol':
        result = minimize(min_volatility_objective, init_guess, args=(mean_returns, cov_matrix),
                          method='SLSQP', bounds=bounds, constraints=constraints)
    elif strategy == 'max_sharpe':
        result = minimize(neg_sharpe_objective, init_guess, args=(mean_returns, cov_matrix),
                          method='SLSQP', bounds=bounds, constraints=constraints)
    else:  # max_return
        result = minimize(max_return_objective, init_guess, args=(mean_returns, cov_matrix),
                          method='SLSQP', bounds=bounds, constraints=constraints)

    return result.x

def simulate_monte_carlo(portfolio_returns, days=252, simulations=1000):
    """Generuje wiele ścieżek Monte Carlo zamiast jednej."""
    mean_ret = portfolio_returns.mean()
    std_ret = portfolio_returns.std()
    
    # Symulacja na rozkładzie normalnym dla wielu ścieżek
    simulated_paths = np.random.normal(mean_ret, std_ret, (days, simulations))
    price_paths = np.exp(np.cumsum(simulated_paths, axis=0))
    
    # Zwracamy średnią, najgorszą (5%) i najlepszą (95%) ścieżkę
    mean_path = np.mean(price_paths, axis=1)
    worst_path = np.percentile(price_paths, 5, axis=1)
    best_path = np.percentile(price_paths, 95, axis=1)
    
    return mean_path, worst_path, best_path
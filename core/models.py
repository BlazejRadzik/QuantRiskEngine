import numpy as np
import pandas as pd
from scipy.optimize import minimize

def get_optimal_weights(returns: pd.DataFrame, strategy: str) -> np.ndarray:
    num_assets = len(returns.columns)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    # Elastyczne granice - min 5%, max 45% (żeby wymusić dywersyfikację)
    if num_assets >= 3:
        bnd = (0.05, 0.45)
    else:
        bnd = (0.05, 0.95)
    bounds = tuple(bnd for _ in range(num_assets))

    def portfolio_vol(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    def portfolio_ret(weights):
        return np.sum(mean_returns * weights)

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    init_guess = np.array([1.0 / num_assets] * num_assets)

    try:
        # 1. Próba głównego silnika Scipy
        if strategy == 'min_vol':
            res = minimize(lambda w: portfolio_vol(w), init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        elif strategy == 'max_sharpe':
            res = minimize(lambda w: -(portfolio_ret(w)/portfolio_vol(w)), init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        else:
            res = minimize(lambda w: -portfolio_ret(w), init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        weights = res.x
        
        # Weryfikacja: Jeśli Scipy zwariował i zignorował granice (dał np. 100%), odrzucamy go
        if not res.success or np.any(weights < bnd[0] - 0.01) or np.any(weights > bnd[1] + 0.01):
            raise ValueError("Scipy zignorował ramy, przechodzę na wektoryzację.")
            
    except Exception:
        # 2. PANCERNY FALLBACK: Wektoryzowana siatka Monte Carlo (Zawsze działa, 0 błędów)
        # Losuje 20 000 układów wag na raz
        random_w = np.random.uniform(bnd[0], bnd[1], (20000, num_assets))
        random_w = random_w / random_w.sum(axis=1)[:, np.newaxis] # Normalizacja do 100%
        
        # Odsiewamy te, które po normalizacji przekroczyły granice 5-45%
        valid_idx = np.where((random_w >= bnd[0]).all(axis=1) & (random_w <= bnd[1]).all(axis=1))[0]
        
        if len(valid_idx) == 0:
            weights = init_guess
        else:
            valid_w = random_w[valid_idx]
            vols = np.sqrt(np.einsum('ij,ji->i', valid_w.dot(cov_matrix), valid_w.T))
            rets = valid_w.dot(mean_returns)
            
            if strategy == 'min_vol':
                best_idx = np.argmin(vols)
            elif strategy == 'max_sharpe':
                best_idx = np.argmax(rets / vols)
            else:
                best_idx = np.argmax(rets)
                
            weights = valid_w[best_idx]

    # Ostateczne docięcie i wyczyszczenie śmieciowych ułamków
    weights = np.clip(weights, bnd[0], bnd[1])
    weights = np.round(weights, 4)
    weights = weights / np.sum(weights) 
    
    return weights

def simulate_monte_carlo(portfolio_returns, days=252, simulations=1000):
    mean_ret = portfolio_returns.mean()
    std_ret = portfolio_returns.std()
    drift = mean_ret - (0.5 * std_ret**2)
    
    simulated_paths = np.random.normal(drift, std_ret, (days, simulations))
    price_paths = np.exp(np.cumsum(simulated_paths, axis=0))
    
    start = np.ones((1, simulations))
    price_paths = np.vstack([start, price_paths])
    
    mean_path = np.mean(price_paths, axis=1)
    worst_path = np.percentile(price_paths, 5, axis=1)
    best_path = np.percentile(price_paths, 95, axis=1)
    
    return mean_path, worst_path, best_path
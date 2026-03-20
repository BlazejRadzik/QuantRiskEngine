import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import List

def optimize_portfolio_weights(returns_df: pd.DataFrame, annualization_factor: int = 252) -> List[float]:
    """
    Modern Portfolio Theory: Maximize Sharpe Ratio.
    """
    num_assets = len(returns_df.columns)
    if num_assets < 2: 
        return [1.0]
    
    def objective(w: np.ndarray) -> float:
        # Zannualizowany zwrot i zmienność
        p_ret = np.sum(returns_df.mean() * w) * annualization_factor
        p_vol = np.sqrt(np.dot(w.T, np.dot(returns_df.cov() * annualization_factor, w)))
        # Zwracamy wartość ujemną, ponieważ funkcja minimize szuka minimum
        return -p_ret / p_vol

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    initial_guess = [1. / num_assets] * num_assets
    
    res = minimize(
        objective, 
        initial_guess, 
        method='SLSQP', 
        bounds=bounds, 
        constraints=constraints
    )
    
    return [round(weight, 4) for weight in res.x.tolist()]
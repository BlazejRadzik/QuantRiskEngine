import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def calculate_portfolio_metrics(weights, returns: pd.DataFrame):
    """Kompleksowe obliczenia ryzyka dla portfela."""
    # 1. Szereg zwrotów całego portfela
    portfolio_returns = returns.dot(weights)
    
    # 2. Podstawowe statystyki
    ann_return = portfolio_returns.mean() * 252
    ann_volatility = portfolio_returns.std() * np.sqrt(252)
    
    # 3. Value at Risk (95% Historyczny)
    var_95 = np.percentile(portfolio_returns, 5)
    
    # 4. CVaR (Expected Shortfall) - to 'sprzedaje' projekt na LinkedIn!
    cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
    
    # 5. Sortino & Sharpe
    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    sortino = ann_return / downside_std if downside_std > 0 else 0
    
    return {
        "portfolio_returns_series": portfolio_returns,
        "annual_return": ann_return,
        "annual_volatility": ann_volatility,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "sortino_ratio": sortino,
        "skewness": skew(portfolio_returns),
        "kurtosis": kurtosis(portfolio_returns)
    }
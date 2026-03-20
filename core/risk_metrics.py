import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def calculate_portfolio_metrics(weights, returns: pd.DataFrame):
    """Wylicza metryki dla już zważonego portfela."""
    # 1. Zbudowanie jednego, spójnego szeregu czasowego dla całego portfela
    portfolio_returns = returns.dot(weights)
    
    # Zysk i Zmienność
    annual_return = portfolio_returns.mean() * 252
    annual_volatility = portfolio_returns.std() * np.sqrt(252)
    
    # Prawidłowe Sortino Ratio
    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    sortino_ratio = annual_return / downside_std if downside_std > 0 else 0
    
    # Skewness & Kurtosis
    skewness_val = skew(portfolio_returns)
    kurt_val = kurtosis(portfolio_returns)
    
    return {
        "portfolio_returns_series": portfolio_returns,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sortino_ratio": sortino_ratio,
        "skewness": skewness_val,
        "kurtosis": kurt_val
    }
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def calculate_portfolio_metrics(weights, returns: pd.DataFrame):
    """Wylicza metryki dla już zważonego portfela."""
    # 1. Zbudowanie jednego, spójnego szeregu czasowego dla całego portfela
    portfolio_returns = returns.dot(weights)
    
    # Zysk i Zmienność
    annual_return = portfolio_returns.mean() * 252
    annual_volatility = portfolio_returns.std() * np.sqrt(252)
    
    # Prawidłowe Sortino Ratio
    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    sortino_ratio = annual_return / downside_std if downside_std > 0 else 0
    
    # Skewness & Kurtosis
    skewness_val = skew(portfolio_returns)
    kurt_val = kurtosis(portfolio_returns)
    
    return {
        "portfolio_returns_series": portfolio_returns,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sortino_ratio": sortino_ratio,
        "skewness": skewness_val,
        "kurtosis": kurt_val
    }
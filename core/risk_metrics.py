import numpy as np
import pandas as pd
from scipy.stats import norm
from arch import arch_model

def get_garch_volatility(returns):
    try:
        model = arch_model(returns * 100, vol='Garch', p=1, q=1, rescale=False)
        res = model.fit(disp='off', show_warning=False)
        forecast = res.forecast(horizon=1)
        return np.sqrt(forecast.variance.values[-1, :])[0] / 100
    except:
        return returns.std()

def calculate_risk_metrics(returns, confidence_level=0.95):
    """
    calculates parametric var and expected shortfall for a series.
    """
    mu = returns.mean()
    sigma = get_garch_volatility(returns)
    z_score = norm.ppf(1 - confidence_level)
    
    var_param = -(mu + z_score * sigma)
    
    # expected shortfall (parametric)
    # formula: ES = mu + sigma * (pdf(z) / (1-alpha))
    pdf_z = norm.pdf(z_score)
    es_param = -(mu - sigma * (pdf_z / (1 - confidence_level)))
    
    return {
        "var_95": round(float(var_param), 4),
        "es_95": round(float(es_param), 4),
        "volatility": round(float(sigma), 4)
    }

def calculate_portfolio_variance(returns_df, weights):
    """
    calculates portfolio volatility using the covariance matrix.
    """
    cov_matrix = returns_df.cov()
    weights = np.array(weights)
    port_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    return np.sqrt(port_variance)
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize
from core.monte_carlo import run_monte_carlo_simulation # zakładamy istnienie

def calculate_historical_metrics(returns, confidence_level=0.95):
    """calculates historical var and es."""
    var_h = -np.percentile(returns, (1 - confidence_level) * 100)
    tail_losses = returns[returns <= -var_h]
    es_h = -tail_losses.mean() if not tail_losses.empty else var_h
    return {"var": round(var_h, 4), "es": round(es_h, 4)}

def calculate_monte_carlo_metrics(s0, mu, sigma, confidence_level=0.95):
    """calculates var and es using simulated paths."""
    # simulating 10,000 paths for next day
    sim_returns = np.random.normal(mu, sigma, 10000)
    var_mc = -np.percentile(sim_returns, (1 - confidence_level) * 100)
    tail_losses = sim_returns[sim_returns <= -var_mc]
    es_mc = -tail_losses.mean() if not tail_losses.empty else var_mc
    return {"var": round(var_mc, 4), "es": round(es_mc, 4)}

def optimize_portfolio(returns_df):
    """
    markowitz portfolio optimization (max sharpe ratio).
    """
    num_assets = len(returns_df.columns)
    args = (returns_df.mean(), returns_df.cov())
    
    def get_sharpe(weights, mean_returns, cov_matrix):
        p_ret = np.sum(mean_returns * weights) * 252
        p_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
        return -p_ret / p_std # negative for minimization

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    initial_guess = num_assets * [1. / num_assets]
    
    optimized = minimize(get_sharpe, initial_guess, args=args, 
                         method='SLSQP', bounds=bounds, constraints=constraints)
    return optimized.x.tolist()
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize
from arch import arch_model

def get_garch_volatility(returns):
    try:
        model = arch_model(returns * 100, vol='Garch', p=1, q=1, rescale=False)
        res = model.fit(disp='off', show_warning=False)
        forecast = res.forecast(horizon=1)
        return np.sqrt(forecast.variance.values[-1, :])[0] / 100
    except:
        return returns.std()

def calculate_comprehensive_metrics(returns, confidence_level=0.95):
    mu = returns.mean()
    sigma = get_garch_volatility(returns)
    z_score = norm.ppf(1 - confidence_level)
    
    # 1. Parametric Metrics
    var_p = -(mu + z_score * sigma)
    pdf_z = norm.pdf(z_score)
    es_p = -(mu - sigma * (pdf_z / (1 - confidence_level)))
    
    # 2. Historical Metrics
    var_h = -np.percentile(returns, (1 - confidence_level) * 100)
    es_h = -returns[returns <= -var_h].mean() if not returns[returns <= -var_h].empty else var_h
    
    # 3. Monte Carlo Metrics (Simple MC for single asset/index)
    sim_returns = np.random.normal(mu, sigma, 10000)
    var_mc = -np.percentile(sim_returns, (1 - confidence_level) * 100)
    es_mc = -sim_returns[sim_returns <= -var_mc].mean()
    
    return {
        "parametric": {"var": round(float(var_p), 4), "es": round(float(es_p), 4)},
        "historical": {"var": round(float(var_h), 4), "es": round(float(es_h), 4)},
        "monte_carlo": {"var": round(float(var_mc), 4), "es": round(float(es_mc), 4)},
        "volatility": round(float(sigma), 4)
    }

def optimize_portfolio_weights(returns_df):
    """Modern Portfolio Theory: Maximize Sharpe Ratio."""
    num_assets = len(returns_df.columns)
    if num_assets < 2: return [1.0]
    
    def objective(w):
        p_ret = np.sum(returns_df.mean() * w) * 252
        p_vol = np.sqrt(np.dot(w.T, np.dot(returns_df.cov() * 252, w)))
        return -p_ret / p_vol

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    res = minimize(objective, num_assets * [1./num_assets], method='SLSQP', bounds=bounds, constraints=constraints)
    return res.x.tolist()
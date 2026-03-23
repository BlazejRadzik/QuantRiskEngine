import os
from typing import Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

try:
    from arch import arch_model
except ImportError:
    arch_model = None

if os.environ.get("QUANT_DISABLE_CPP", "").lower() in ("1", "true", "yes"):
    monte_carlo_cpp = None
else:
    try:
        import monte_carlo_cpp
    except ImportError:
        monte_carlo_cpp = None

from core.models import get_nn_adjusted_volatility

try:
    import torch
except ImportError:
    torch = None

def _as_return_series(returns: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    if isinstance(returns, pd.Series):
        return returns.dropna()
    if isinstance(returns, pd.DataFrame):
        if returns.shape[1] == 1:
            return returns.iloc[:, 0].dropna()
        return returns.mean(axis=1).dropna()
    raise TypeError("returns must be a pandas Series or DataFrame")

def _ewma_cov_matrix(returns_df: pd.DataFrame, span: int = 60) -> pd.DataFrame:
    """EWMA covariance with lambda = 1 - 2/(span+1)."""
    if returns_df.empty:
        return returns_df.cov()

    x = returns_df.dropna().values
    n_obs, n_assets = x.shape
    if n_obs < 2:
        return returns_df.cov()

    lam = 1.0 - (2.0 / (span + 1.0))
    cov = np.cov(x[: min(20, n_obs)].T)

    for t in range(1, n_obs):
        r = x[t][:, None]
        cov = lam * cov + (1.0 - lam) * (r @ r.T)

    return pd.DataFrame(cov, index=returns_df.columns, columns=returns_df.columns)

def optimize_portfolio_weights(
    returns_df: pd.DataFrame,
    strategy: str = "max_sharpe",
    min_weight: float = 0.05,
    max_weight: float = 0.45,
    ewma_span: int = 60,
) -> np.ndarray:
    """
    Markowitz MPT (SLSQP) with institutional bounds and EWMA covariance.
    """
    num_assets = len(returns_df.columns)
    if num_assets == 0:
        return np.array([])
    if num_assets == 1:
        return np.array([1.0])

    avg_returns = returns_df.mean()
    cov_matrix = _ewma_cov_matrix(returns_df, span=ewma_span)

    eff_min = min(min_weight, 1.0 / num_assets)
    eff_max = max(max_weight, 1.0 / num_assets)
    if eff_min * num_assets > 1.0:
        eff_min = 0.0

    def get_stats(weights: np.ndarray) -> Tuple[float, float, float]:
        p_ret = float(np.sum(avg_returns * weights) * 252)
        p_vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights))))
        sharpe = p_ret / p_vol if p_vol > 0 else 0.0
        return p_ret, p_vol, sharpe

    if strategy == "max_sharpe":
        objective = lambda w: -get_stats(w)[2]
    elif strategy == "min_vol":
        objective = lambda w: get_stats(w)[1]
    else:
        objective = lambda w: -get_stats(w)[0]

    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    bounds = tuple((eff_min, eff_max) for _ in range(num_assets))
    init_guess = np.array([1.0 / num_assets] * num_assets)

    res = minimize(objective, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)
    if res.success:
        return res.x
    return init_guess

def _get_garch_volatility(returns: pd.Series) -> float:
    """One-step GARCH(1,1) volatility forecast (fallback to std)."""
    r = returns.dropna()
    if len(r) < 50 or arch_model is None:
        return float(r.std(ddof=1)) if len(r) > 1 else float(abs(r.mean()))
    try:
        model = arch_model(r * 100, vol="Garch", p=1, q=1, rescale=False)
        fit = model.fit(disp="off", show_warning=False)
        fcst = fit.forecast(horizon=1)
        sigma = np.sqrt(fcst.variance.values[-1, :])[0] / 100.0
        return float(sigma)
    except Exception:
        return float(r.std(ddof=1)) if len(r) > 1 else float(abs(r.mean()))

def _parametric_var_es(mu: float, sigma: float, confidence_level: float = 0.95) -> Tuple[float, float]:
    z = norm.ppf(1.0 - confidence_level)
    var_p = -(mu + z * sigma)
    pdf_z = norm.pdf(z)
    es_p = -(mu - sigma * (pdf_z / (1.0 - confidence_level)))
    return float(var_p), float(es_p)

def _mc_terminal_returns_cpp(mu: float, sigma: float, days: int, num_paths: int) -> np.ndarray:
    sim = monte_carlo_cpp.simulate_paths(100.0, mu, sigma, days, num_paths)
    return np.asarray(sim, dtype=np.float64)

def _mc_terminal_returns_numpy(mu: float, sigma: float, days: int, num_paths: int) -> np.ndarray:
    rng = np.random.default_rng()
    dt = 1.0 / 252.0
    drift_adj = (mu - 0.5 * sigma * sigma) * dt
    vol_adj = sigma * np.sqrt(dt)
    z = rng.standard_normal((num_paths, days))
    log_r = np.sum(drift_adj + vol_adj * z, axis=1)
    return np.expm1(log_r)

def calculate_comprehensive_metrics(
    returns: Union[pd.Series, pd.DataFrame],
    confidence_level: float = 0.95,
    mc_paths: Optional[int] = None,
    mc_days: Optional[int] = None,
) -> Tuple[Dict, float]:
    """
    Returns tuple: (metrics_dict_for_api, parametric_var_float_for_backtest).
    """
    r = _as_return_series(returns)
    mu = float(r.mean())
    vol_historical = float(r.std(ddof=1)) if len(r) > 1 else float(abs(mu))

    sigma_garch = _get_garch_volatility(r)

    if torch is not None:
        t = torch.tensor(r.values, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
        sigma_ai = get_nn_adjusted_volatility(sigma_garch, t)
    else:
        sigma_ai = get_nn_adjusted_volatility(sigma_garch, None)

    var_p, es_p = _parametric_var_es(mu, sigma_ai, confidence_level)

    q = (1.0 - confidence_level) * 100.0
    hist_thresh = float(np.percentile(r, q))
    var_h = float(-hist_thresh)
    tail = r[r <= hist_thresh]
    es_h = float(-tail.mean()) if len(tail) else var_h

    if mc_paths is None:
        mc_paths = int(os.environ.get("QUANT_MC_PATHS", "500000"))
    if mc_days is None:
        mc_days = int(os.environ.get("QUANT_MC_DAYS", "1"))

    num_paths = max(10_000, min(int(mc_paths), 20_000_000))
    days_mc = max(1, min(int(mc_days), 30))

    if monte_carlo_cpp is not None:
        sim_returns = _mc_terminal_returns_cpp(mu, sigma_ai, days_mc, num_paths)
    else:
        sim_returns = _mc_terminal_returns_numpy(mu, sigma_ai, days_mc, num_paths)

    var_mc = float(-np.percentile(sim_returns, q))
    tail_mc = sim_returns[sim_returns <= -var_mc]
    es_mc = float(-tail_mc.mean()) if len(tail_mc) else var_mc

    hpc_info = {}
    if monte_carlo_cpp is not None and hasattr(monte_carlo_cpp, "get_omp_info"):
        try:
            hpc_info = monte_carlo_cpp.get_omp_info()
        except Exception:
            hpc_info = {}

    metrics = {
        "volatility": f"{vol_historical * 100:.2f}%",
        "garch_volatility": f"{sigma_garch * 100:.2f}%",
        "ai_adjusted_volatility": f"{sigma_ai * 100:.2f}%",
        "hpc": hpc_info,
        "parametric": {"var": f"{var_p * 100:.2f}%", "es": f"{es_p * 100:.2f}%"},
        "historical": {"var": f"{var_h * 100:.2f}%", "es": f"{es_h * 100:.2f}%"},
        "monte_carlo": {"var": f"{var_mc * 100:.2f}%", "es": f"{es_mc * 100:.2f}%"},
    }
    return metrics, var_p

def calculate_portfolio_metrics(weights, returns_df):
    """Pomocnicza funkcja dla zakładki Doradca + metryki pod PDF factsheet."""
    p_returns = returns_df.dot(weights)
    p_vol = float(p_returns.std(ddof=1) * np.sqrt(252)) if len(p_returns) > 1 else 0.0
    p_ret = float(p_returns.mean() * 252)

    var_95 = float(-np.percentile(p_returns, 5)) if len(p_returns) else 0.0
    tail = p_returns[p_returns <= np.percentile(p_returns, 5)] if len(p_returns) else pd.Series(dtype=float)
    cvar_95 = float(-tail.mean()) if len(tail) else var_95

    downside = p_returns[p_returns < 0]
    downside_vol = float(downside.std(ddof=1) * np.sqrt(252)) if len(downside) > 1 else 0.0
    sortino = p_ret / downside_vol if downside_vol > 0 else 0.0

    return {
        "annual_return": p_ret,
        "annual_volatility": p_vol,
        "sortino_ratio": sortino,
        "skewness": float(p_returns.skew()) if len(p_returns) > 2 else 0.0,
        "kurtosis": float(p_returns.kurtosis()) if len(p_returns) > 3 else 0.0,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "portfolio_returns_series": p_returns,
    }

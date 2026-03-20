import numpy as np
import pandas as pd
from scipy.stats import norm
from arch import arch_model
from typing import Dict, Any

def get_garch_volatility(returns: pd.Series) -> float:
    """
    Estymuje zmienność jednodniową używając modelu GARCH(1,1).
    W przypadku braku zbieżności modelu, jako fallback używa standardowego odchylenia.
    """
    try:
        # Przeskalowanie x100 często pomaga algorytmom optymalizacyjnym w arch
        model = arch_model(returns * 100, vol='Garch', p=1, q=1, rescale=False)
        res = model.fit(disp='off', show_warning=False)
        forecast = res.forecast(horizon=1)
        # Zwracamy zmienność od-skalowaną (/100)
        return float(np.sqrt(forecast.variance.values[-1, :])[0] / 100)
    except Exception as e:
        # Fallback do klasycznego odchylenia standardowego w przypadku błędu
        return float(returns.std())

def calculate_comprehensive_metrics(returns: pd.Series, confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Oblicza VaR oraz ES używając trzech niezależnych podejść.
    """
    mu = returns.mean()
    sigma = get_garch_volatility(returns)
    z_score = norm.ppf(1 - confidence_level)
    
    # 1. Parametric Metrics
    var_p = -(mu + z_score * sigma)
    pdf_z = norm.pdf(z_score)
    es_p = -(mu - sigma * (pdf_z / (1 - confidence_level)))
    
    # 2. Historical Metrics
    var_h = -np.percentile(returns, (1 - confidence_level) * 100)
    tail_losses = returns[returns <= -var_h]
    es_h = -tail_losses.mean() if not tail_losses.empty else var_h
    
    # 3. Monte Carlo Metrics (Simple MC dla zsumowanego portfela)
    sim_returns = np.random.normal(mu, sigma, 10000)
    var_mc = -np.percentile(sim_returns, (1 - confidence_level) * 100)
    sim_tail = sim_returns[sim_returns <= -var_mc]
    es_mc = -sim_tail.mean() if len(sim_tail) > 0 else var_mc
    
    return {
        "parametric": {"var": round(float(var_p), 4), "es": round(float(es_p), 4)},
        "historical": {"var": round(float(var_h), 4), "es": round(float(es_h), 4)},
        "monte_carlo": {"var": round(float(var_mc), 4), "es": round(float(es_mc), 4)},
        "volatility": round(float(sigma), 4)
    }
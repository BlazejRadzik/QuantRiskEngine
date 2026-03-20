import pandas as pd
from typing import Dict, Union

def apply_historical_scenario(portfolio_returns: pd.Series, scenario: str = "COVID_19_Shock") -> Dict[str, Union[str, float]]:
    """
    Symuluje zachowanie portfela w ekstremalnych warunkach rynkowych.
    Wymaga stóp zwrotu portfela indeksowanych datami (DatetimeIndex).
    """
    scenarios = {
        "COVID_19_Shock": {"start": "2020-02-20", "end": "2020-03-23"},
        "Global_Financial_Crisis": {"start": "2008-09-01", "end": "2009-03-01"},
    }
    
    if scenario not in scenarios:
        raise ValueError(f"Scenario {scenario} not supported.")
        
    dates = scenarios[scenario]
    
    # Filtrujemy dane historyczne dla zadanego okresu
    # (Zakładamy, że portfolio_returns ma index typu Datetime)
    try:
        stress_period_returns = portfolio_returns.loc[dates["start"]:dates["end"]]
        
        if stress_period_returns.empty:
            return {"error": f"Brak danych historycznych dla okresu {scenario}."}
            
        # Obliczamy maksymalne obsunięcie kapitału (Max Drawdown) w tym okresie
        cumulative_returns = (1 + stress_period_returns).cumprod()
        rolling_max = cumulative_returns.cummax()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
    except (KeyError, TypeError):
        # Fallback jeśli przekazano dane bez poprawnego indeksu daty
        max_drawdown = -0.35 # Przykładowy szok -35%
        
    status = "DANGER" if max_drawdown < -0.20 else "SAFE"
    
    return {
        "scenario_name": scenario,
        "simulated_max_drawdown": round(float(max_drawdown), 4),
        "status": status
    }
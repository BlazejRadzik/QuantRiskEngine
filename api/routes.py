from fastapi import APIRouter, Query, HTTPException
from typing import List
from data.ingestor import fetch_data
from core.models import optimize_portfolio_weights
from core.risk_metrics import calculate_comprehensive_metrics
from core.backtesting import run_full_backtest
import pandas as pd

router = APIRouter()

@router.get("/v1/portfolio/risk")
async def get_portfolio_risk(tickers: List[str] = Query(...)):
    try:
        # 1. Pobranie danych z giełdy
        returns_df = fetch_data(tickers)
        if returns_df.empty:
            raise HTTPException(status_code=400, detail="Nie znaleziono danych dla podanych tickerów.")

        # 2. Optymalizacja Markowitza (szukamy najlepszych wag portfela)
        weights = optimize_portfolio_weights(returns_df)

        # 3. Zbudowanie portfela (mnożymy stopy zwrotu przez wagi)
        # Wynikiem jest jeden szereg czasowy reprezentujący cały portfel
        portfolio_returns = returns_df.dot(weights)

        # 4. Wyliczenie metryk ryzyka (VaR, ES, Volatility)
        metrics = calculate_comprehensive_metrics(portfolio_returns)

        # 5. Walidacja modelu (Backtesting historycznego VaR)
        # Parametr VaR musi być dodatni do logiki backtestu
        var_threshold = abs(metrics["historical"]["var"]) 
        backtest = run_full_backtest(portfolio_returns, var_value=var_threshold)

        # 6. Formatowanie wyników pod Frontend (Streamlit)
        def to_pct(value: float) -> str:
            return f"{value * 100:.2f}%"

        return {
            "risk_metrics": {
                "volatility": to_pct(metrics["volatility"]),
                "parametric": {
                    "var": to_pct(metrics["parametric"]["var"]),
                    "es": to_pct(metrics["parametric"]["es"])
                },
                "historical": {
                    "var": to_pct(metrics["historical"]["var"]),
                    "es": to_pct(metrics["historical"]["es"])
                },
                "monte_carlo": {
                    "var": to_pct(metrics["monte_carlo"]["var"]),
                    "es": to_pct(metrics["monte_carlo"]["es"])
                }
            },
            "backtest": {
                "violations": backtest["violations"],
                "violation_ratio": to_pct(backtest["violation_ratio"]),
                "kupiec_p": str(backtest["kupiec_p"]),
                "christ_p": str(backtest["christ_p"]),
                "status": backtest["status"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
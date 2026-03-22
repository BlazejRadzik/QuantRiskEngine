# api/routes.py
from fastapi import APIRouter, HTTPException, Query
from core.risk_metrics import calculate_comprehensive_metrics, optimize_portfolio_weights
from core.backtesting import run_full_backtest
from data.ingestor import DataIngestor
import pandas as pd
import numpy as np
from typing import List
from fastapi import APIRouter, Query
from typing import List
router = APIRouter()

@router.get("/portfolio/risk")
async def get_portfolio_risk(tickers: List[str] = Query(...)):
    try:
        # Inicjalizujemy nasz nowy system pobierania z wbudowanym Cache (SQLite)
        ingestor = DataIngestor(tickers)
        data = ingestor.fetch_historical_data(period="2y")
        
        if data is None or len(data) < 30:
            msg = f"Insufficient data: only {len(data) if data is not None else 0} overlapping days found."
            raise HTTPException(status_code=404, detail=msg)
            
        returns_df = np.log(data / data.shift(1)).dropna()
        
        weights = optimize_portfolio_weights(returns_df)
        port_returns = returns_df.dot(weights)
        
        risk = calculate_comprehensive_metrics(port_returns)
        
        # Pobieramy VaR do walidacji modelu
        var_value = risk.get('parametric', {}).get('var', 0.0)
        backtest = run_full_backtest(port_returns, var_value)
        
        return {
            "status": "success",
            "assets": {t: round(w, 4) for t, w in zip(tickers, weights)},
            "risk_metrics": risk,
            "backtest": backtest
        }
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")
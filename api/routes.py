import time
from typing import List, Optional
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from core.backtesting import run_full_backtest
from core.risk_metrics import calculate_comprehensive_metrics, optimize_portfolio_weights
from core.stress_testing import apply_historical_scenario
from data.ingestor import DataIngestor

try:
    import monte_carlo_cpp
except ImportError:
    monte_carlo_cpp = None

router = APIRouter()

def _simulate_numpy_returns(mu: float, sigma: float, days: int, num_paths: int) -> np.ndarray:
    dt = 1.0 / 252.0
    drift_adj = (mu - 0.5 * sigma * sigma) * dt
    vol_adj = sigma * np.sqrt(dt)
    z = np.random.standard_normal((num_paths, days))
    return np.expm1(np.sum(drift_adj + vol_adj * z, axis=1))

def _benchmark_engine(mu: float, sigma: float, days: int, paths: int, runs: int) -> dict:
    omp_times = []
    np_times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        if monte_carlo_cpp is not None:
            _ = monte_carlo_cpp.simulate_paths(100.0, mu, sigma, days, paths)
        else:
            _ = _simulate_numpy_returns(mu, sigma, days, paths)
        omp_times.append(time.perf_counter() - t0)
        t1 = time.perf_counter()
        _ = _simulate_numpy_returns(mu, sigma, days, paths)
        np_times.append(time.perf_counter() - t1)

    omp_avg = float(np.mean(omp_times))
    np_avg = float(np.mean(np_times))
    speedup = (np_avg / omp_avg) if omp_avg > 0 else 0.0
    omp_info = {}
   
    if monte_carlo_cpp is not None and hasattr(monte_carlo_cpp, "get_omp_info"):
        try:
            omp_info = monte_carlo_cpp.get_omp_info()
        except Exception:
            omp_info = {}

    return {
        "paths": int(paths),
        "days": int(days),
        "runs": int(runs),
        "openmp_avg_s": round(omp_avg, 6),
        "numpy_avg_s": round(np_avg, 6),
        "speedup_x": round(float(speedup), 2),
        "omp_info": omp_info,
    }

@router.get("/portfolio/risk")
async def get_portfolio_risk(
    tickers: List[str] = Query(...),
    mc_paths: Optional[int] = Query(None),
    mc_days: Optional[int] = Query(None),
    stress_scenario: str = Query("COVID_19_Shock"),
):
    try:
        ingestor = DataIngestor(tickers)
        data = ingestor.fetch_historical_data(period="2y")

        if data is None or len(data) < 30:
            msg = f"Insufficient data: only {len(data) if data is not None else 0} overlapping days found."
            raise HTTPException(status_code=404, detail=msg)
        returns_df = np.log(data / data.shift(1)).dropna()
        weights = optimize_portfolio_weights(returns_df)
        port_returns = returns_df.dot(weights)
        risk_metrics, var_parametric_daily = calculate_comprehensive_metrics(
            port_returns,
            mc_paths=mc_paths,
            mc_days=mc_days,
        )
        backtest = run_full_backtest(port_returns, var_parametric_daily)
        stress_test = apply_historical_scenario(port_returns, scenario=stress_scenario)
        return {
            "status": "success",
            "assets": {t: round(float(w), 4) for t, w in zip(tickers, weights)},
            "risk_metrics": risk_metrics,
            "backtest": backtest,
            "stress_test": stress_test,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")

@router.get("/benchmark/openmp")
async def benchmark_openmp(
    paths: int = Query(500000, ge=10000, le=20000000),
    days: int = Query(10, ge=1, le=30),
    runs: int = Query(3, ge=1, le=10),
):
    """
    Benchmark OpenMP (C++ engine) vs NumPy fallback.
    Returns average time over `runs` for the same workload.
    """
    try:
        mu = 0.0005
        sigma = 0.02
        result = _benchmark_engine(mu=mu, sigma=sigma, days=days, paths=paths, runs=runs)
        return {"status": "success", "benchmark": result}
    except Exception as e:
        print(f"BENCHMARK ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmark Error: {str(e)}")

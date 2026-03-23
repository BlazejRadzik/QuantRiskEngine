try:
    import torch
    import torch.nn as nn

    class VolatilityLSTM(nn.Module):
        def __init__(self, input_size=1, hidden_size=32):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])

    _TORCH_AVAILABLE = True
except ImportError:
    torch = None
    VolatilityLSTM = None
    _TORCH_AVAILABLE = False

def get_nn_adjusted_volatility(historical_vol, returns_tensor):
    """
    Koreguje zmienność historyczną za pomocą sieci LSTM.
    Bez PyTorch zwraca wyłącznie zmienność historyczną.
    """
    if not _TORCH_AVAILABLE or returns_tensor is None:
        return float(historical_vol)
    try:
        model = VolatilityLSTM()
        with torch.no_grad():
            ai_adjustment = model(returns_tensor).item()
            adjusted_vol = historical_vol * (1 + abs(ai_adjustment) * 0.1)
            return float(adjusted_vol)
    except Exception as e:
        print(f"[AI ERROR] Fallback to historical volatility: {e}")
        return float(historical_vol)

def get_optimal_weights(returns_df, strategy="max_sharpe"):
    """Alias używany przez dashboard (delegacja do risk_metrics)."""
    from core.risk_metrics import optimize_portfolio_weights

    return optimize_portfolio_weights(returns_df, strategy=strategy)

def simulate_monte_carlo(port_returns, horizon=252, simulations=2000):
    """
    Zwraca trzy ścieżki wartości portfela (średnia, percentyl 5%, percentyl 95%) dla wykresów Streamlit.
    """
    import numpy as np

    from core.monte_carlo import run_monte_carlo_simulation

    r = port_returns.dropna()
    mu = float(r.mean()) if len(r) else 0.0
    sigma = float(r.std(ddof=1)) if len(r) > 1 else 0.01
    if sigma <= 0 or np.isnan(sigma):
        sigma = 0.01

    paths = run_monte_carlo_simulation(100.0, mu, sigma, horizon=horizon, simulations=simulations)
    mean_path = np.mean(paths, axis=0)
    worst_path = np.percentile(paths, 5, axis=0)
    best_path = np.percentile(paths, 95, axis=0)
    return mean_path.tolist(), worst_path.tolist(), best_path.tolist()

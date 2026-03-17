import numpy as np
import pandas as pd

def run_monte_carlo_simulation(s0, mu, sigma, horizon=30, simulations=10000):
    """
    performs monte carlo simulation using geometric brownian motion.
    s0: initial price
    mu: expected return (drift)
    sigma: volatility
    horizon: forecast period in days
    """
    dt = 1 / 252  

    stoch_component = np.random.normal(0, 1, (simulations, horizon))
    
    # calculate daily drift and diffusion
    drift = (mu - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt) * stoch_component
    
    daily_returns = np.exp(drift + diffusion)
    price_paths = np.zeros_like(daily_returns)
    price_paths[:, 0] = s0 * daily_returns[:, 0]
    
    for t in range(1, horizon):
        price_paths[:, t] = price_paths[:, t-1] * daily_returns[:, t]
        
    return price_paths

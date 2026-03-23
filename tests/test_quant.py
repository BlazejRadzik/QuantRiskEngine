import numpy as np
import pandas as pd
from core.risk_metrics import calculate_comprehensive_metrics

def test_var_is_positive():
    """Test if VaR is always returned as a positive loss magnitude."""
    mock_returns = pd.Series(np.random.normal(0, 0.02, 500))
    metrics = calculate_comprehensive_metrics(mock_returns)
    assert metrics['parametric']['var'] > 0
    assert metrics['historical']['var'] > 0

def test_es_is_greater_than_var():
    """Tail risk (ES) should logically be greater than or equal to VaR."""
    mock_returns = pd.Series(np.random.normal(0, 0.05, 1000))
    metrics = calculate_comprehensive_metrics(mock_returns)
    assert metrics['parametric']['es'] >= metrics['parametric']['var']

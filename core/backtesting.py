import numpy as np
import pandas as pd
from scipy.stats import chi2
from typing import Dict, Union

def run_full_backtest(returns: pd.Series, var_value: float, confidence_level: float = 0.95) -> Dict[str, Union[int, float, str]]:
    """
    Przeprowadza walidację modelu ryzyka (Testy Kupca i Christoffersena).
    """
    n = len(returns)
    alpha = 1 - confidence_level
    hits = (returns < -var_value).astype(int)
    x = hits.sum()

    ratio = x / n if x > 0 else 0.0001
    lr_pof = -2 * ((n - x) * np.log(1 - alpha) + x * np.log(alpha) - (n - x) * np.log(1 - ratio) - x * np.log(ratio))
    p_kupiec = 1 - chi2.cdf(lr_pof, df=1)
    p_christ = 0.5 
    christ_stat = 0.0
    if x > 1:
        n00 = n01 = n10 = n11 = 0
        hits_list = hits.tolist()
        for i in range(len(hits_list) - 1):
            if hits_list[i] == 0 and hits_list[i+1] == 0: n00 += 1
            elif hits_list[i] == 0 and hits_list[i+1] == 1: n01 += 1
            elif hits_list[i] == 1 and hits_list[i+1] == 0: n10 += 1
            else: n11 += 1
        try:
            pi0 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
            pi1 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
            pi = (n01 + n11) / n
            if 0 < pi < 1 and 0 < pi0 < 1 and 0 < pi1 < 1:
                ln_alt = n00 * np.log(1 - pi0) + n01 * np.log(pi0) + n10 * np.log(1 - pi1) + n11 * np.log(pi1)
                ln_null = (n00 + n10) * np.log(1 - pi) + (n01 + n11) * np.log(pi)
                christ_stat = -2 * (ln_null - ln_alt)
                p_christ = 1 - chi2.cdf(christ_stat, df=1)
        except Exception:
            pass

    status = "PASS" if p_kupiec > 0.05 else "FAIL"
    kupiec_verdict = "PASS" if p_kupiec > 0.05 else "FAIL"
    christ_verdict = "PASS" if p_christ > 0.05 else "FAIL"

    return {
        "violations": int(x),
        "violation_ratio": round(float(x / (n * alpha)), 2) if n > 0 else 0.0,
        "kupiec_stat": round(float(lr_pof), 4),
        "kupiec_p": round(float(p_kupiec), 4),
        "kupiec_verdict": kupiec_verdict,
        "christ_stat": round(float(christ_stat), 4),
        "christ_p": round(float(p_christ), 4),
        "christ_verdict": christ_verdict,
        "status": status
    }

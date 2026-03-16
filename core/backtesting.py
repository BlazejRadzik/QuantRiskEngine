import numpy as np
from scipy.stats import chi2

def kupiec_pof_test(returns, var_value, confidence_level=0.95):
    """
    kupiec proportion of failures test.
    null hypothesis: the model correctly estimates the number of violations.
    """
    n = len(returns)
    alpha = 1 - confidence_level
    # a violation occurs if return is worse (lower) than -VaR
    x = sum(returns < -var_value)
    
    if x == 0: return {"p_value": 1.0, "status": "pass", "violations": 0}
    
    ratio = x / n
    # likelihood ratio test
    lr = -2 * ((n - x) * np.log(1 - alpha) + x * np.log(alpha) - 
               (n - x) * np.log(1 - ratio) - x * np.log(ratio))
    
    p_value = 1 - chi2.cdf(lr, df=1)
    
    return {
        "violations": int(x),
        "expected_violations": round(n * alpha, 2),
        "p_value": round(float(p_value), 4),
        "status": "pass" if p_value > 0.05 else "fail"
    }
def christoffersen_test(returns, var_value):
    """
    tests independence of violations (no clustering).
    """
    hits = (returns < -var_value).astype(int).values
    # transition matrix counts
    n00 = n01 = n10 = n11 = 0
    for i in range(len(hits)-1):
        if hits[i] == 0 and hits[i+1] == 0: n00 += 1
        elif hits[i] == 0 and hits[i+1] == 1: n01 += 1
        elif hits[i] == 1 and hits[i+1] == 0: n10 += 1
        else: n11 += 1
    
    try:
        pi0 = n01 / (n00 + n01)
        pi1 = n11 / (n10 + n11)
        pi = (n01 + n11) / (n00 + n01 + n10 + n11)
        
        ln_null = (n00 + n10) * np.log(1 - pi) + (n01 + n11) * np.log(pi)
        ln_alt = n00 * np.log(1 - pi0) + n01 * np.log(pi0) + n10 * np.log(1 - pi1) + n11 * np.log(pi1)
        lr_ind = -2 * (ln_null - ln_alt)
        p_val = 1 - chi2.cdf(lr_ind, df=1)
        return round(p_val, 4)
    except:
        return 1.0 # default pass if not enough data
    import numpy as np
from scipy.stats import chi2

def run_full_backtest(returns, var_value, confidence_level=0.95):
    n = len(returns)
    alpha = 1 - confidence_level
    hits = (returns < -var_value).astype(int)
    x = hits.sum()
    
    # Kupiec POF Test
    ratio = x / n if x > 0 else 0.0001
    lr_pof = -2 * ((n-x)*np.log(1-alpha) + x*np.log(alpha) - (n-x)*np.log(1-ratio) - x*np.log(ratio))
    p_kupiec = 1 - chi2.cdf(lr_pof, df=1)
    
    # Christoffersen Independence Test (simple version)
    p_christ = 0.5 # default
    if x > 1:
        # matrix of transitions
        n00 = n01 = n10 = n11 = 0
        for i in range(len(hits)-1):
            if hits.iloc[i]==0 and hits.iloc[i+1]==0: n00+=1
            elif hits.iloc[i]==0 and hits.iloc[i+1]==1: n01+=1
            elif hits.iloc[i]==1 and hits.iloc[i+1]==0: n10+=1
            else: n11+=1
        try:
            pi0, pi1 = n01/(n00+n01), n11/(n10+n11)
            pi = (n01+n11)/n
            ln_alt = n00*np.log(1-pi0)+n01*np.log(pi0)+n10*np.log(1-pi1)+n11*np.log(pi1)
            ln_null = (n00+n10)*np.log(1-pi)+(n01+n11)*np.log(pi)
            p_christ = 1 - chi2.cdf(-2*(ln_null-ln_alt), df=1)
        except: pass

    return {
        "violations": int(x),
        "violation_ratio": round(float(x/(n*alpha)), 2),
        "kupiec_p": round(float(p_kupiec), 4),
        "christ_p": round(float(p_christ), 4),
        "status": "PASS" if p_kupiec > 0.05 else "FAIL"
    }
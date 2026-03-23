# **Mathematical Background** 

This document outlines the core quantitative models implemented in the **QuantRisk Suite**.

---

## **1. Path Generation: Geometric Brownian Motion (GBM)**
The Monte Carlo engine simulates asset prices using the standard SDE:

$$dS_t = \mu S_t dt + \sigma S_t dW_t$$

Where:
* $S_t$ is the asset price.
* $\mu$ is the drift (expected return).
* $\sigma$ is the volatility.
* $dW_t$ is the Wiener process increment.

**C++ Optimization:** The discretized version $S_{t+\Delta t} = S_t \exp\left((\mu - \frac{\sigma^2}{2})\Delta t + \sigma \sqrt{\Delta t} Z\right)$ is implemented using **AVX2 SIMD** to generate multiple paths in a single CPU cycle.

---

## **2. Volatility Modeling: GARCH(1,1) + LSTM**
To capture "Volatility Clustering", we use a hybrid approach. The conditional variance $\sigma_t^2$ is initially modeled via GARCH(1,1):

$$\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$$

**The LSTM Correction:** The residuals from the GARCH model are fed into a **Long Short-Term Memory (LSTM)** network to predict non-linear shocks:

$$\hat{\sigma}_{total} = \sigma_{GARCH} + f_{LSTM}(\epsilon_{t-k}, \dots, \epsilon_{t-1})$$

---

## **3. Model Validation: Kupiec POF Test**
To ensure the **Value at Risk (VaR)** is not underestimating risk, we perform a Likelihood Ratio test:

$$LR_{POF} = -2 \ln \left[ \frac{(1-p)^{n-x} p^x}{(1-\hat{p})^{n-x} \hat{p}^x} \right]$$

Where:
* $n$ is the number of observations.
* $x$ is the number of VaR violations.
* $p$ is the theoretical probability (e.g., 0.05).
* $\hat{p} = x/n$ is the observed failure rate.

We reject the model if $LR_{POF} > \chi^2(1)$.

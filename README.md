# **QuantRisk Suite** 
### **Financial Engine: C++ Core with Python/ML Integration**

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![C++](https://img.shields.io/badge/C++-17/20-00599C)

QuantRisk is a risk management platform that bridges the gap between **computational efficiency** and **modern machine learning**.

> [!IMPORTANT]
> **Performance Milestone:** Achieved a **~400x speedup** on core Monte Carlo simulations compared to native Python loops, and **~9x speedup** over vectorized NumPy implementations using custom C++ SIMD kernels.

---

## **Core Architecture**

### **1. HPC Monte Carlo Engine (C++)**
The heart of the system. Written in **C++17** for maximum throughput.
* **Parallelization:** OpenMP-powered multi-threading across all CPU cores.
* **Binding:** Zero-copy memory transfer via **Pybind11**.
* **Vectorization:** Leveraging **SIMD** instructions for Geometric Brownian Motion (GBM) path generation.

### **2. Hybrid Volatility Forecasting (PyTorch + GARCH)**
A two-stage pipeline for capturing market stress:
* **Stage 1:** Classic **GARCH(1,1)** to model long-term variance persistence.
* **Stage 2:** **LSTM (Recurrent Neural Network)** to correct residuals and capture non-linear "fat-tail" events that standard models miss.

### **3. Institutional Validation Layer**

* **Kupiec’s Proportion of Failures (POF) Test.**
* **Christoffersen’s Independence Test** (Detecting VaR violations clustering).

## **🖼️ Dashboard & Reporting Showcase**

| **Hybrid Volatility Analysis** | **Institutional Risk Report (PDF)** |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/34733444-4f67-49d8-a96b-6f7dc33ff6a9" width="400"> | [📄 **View Sample Report (PDF)**](risk_report.pdf) <br> <img src="https://github.com/user-attachments/assets/9428eba0-e855-4fd2-85a4-0f5651e22a7a" width="250"> |

| **Backtesting & Validation** | **Portfolio Optimization** |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/109bdf00-e640-4be8-bb9a-146f71ef6a82" width="400"> | <img src="https://github.com/user-attachments/assets/62466b68-7a15-4f58-a96d-2438c31a2a3c" width="400"> |

## **Quick Start & Usage**

```python
from quantrisk import MonteCarloEngine, HybridVol

# Generate 2 million paths in milliseconds
engine = MonteCarloEngine(paths=2000000, steps=252)
results = engine.run_simulation(initial_price=100.0, vol=0.2, drift=0.05)

print(f"VaR (95%): {results.calculate_var(0.95)}")

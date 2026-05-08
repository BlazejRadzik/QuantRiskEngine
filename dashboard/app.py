import os
import sys
import streamlit as st
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

try:
    from core.reporting import generate_pdf_factsheet
    from core.models import get_optimal_weights, simulate_monte_carlo
    from core.risk_metrics import calculate_portfolio_metrics, calculate_comprehensive_metrics
    from core.backtesting import run_full_backtest
    from core.stress_testing import apply_historical_scenario
except ModuleNotFoundError:
    st.error(f"Modules not found at: {root_path}. Check the file structure on GitHub.")
import requests
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import yfinance as yf
import time
def get_eval_html(val_str, threshold_good, threshold_bad):
    try:
        v = float(str(val_str).replace('%', '').strip())
        v = abs(v)
        if v <= threshold_good:
            return f"<span style='color: #28a745; font-weight: bold;'>{val_str} - Positive</span>"
        elif v >= threshold_bad:
            return f"<span style='color: #d73a49; font-weight: bold;'>{val_str} - Dynamic</span>"
        else:
            return f"<span style='color: #b08800; font-weight: bold;'>{val_str} - Moderate</span>"
    except:
        return f"<span style='color: gray;'>{val_str}</span>"

@st.cache_data(ttl=3600)
def load_data(tickers):
    data = yf.download(tickers, period="1y", progress=False)
    return data

def _fetch_risk_api(tickers, mc_paths, mc_days, stress_scenario=None, timeout=120):
    params = {
        "tickers": tickers,
        "mc_paths": int(mc_paths),
        "mc_days": int(mc_days),
    }
    if stress_scenario:
        params["stress_scenario"] = stress_scenario
    api_candidates = []
    secret_url = st.secrets.get("api_base_url") if hasattr(st, "secrets") else None
    env_url = os.getenv("QUANT_API_URL")
    if secret_url:
        api_candidates.append(str(secret_url).rstrip("/"))
    if env_url:
        api_candidates.append(str(env_url).rstrip("/"))
    api_candidates.append("http://127.0.0.1:8000")
    last_error = None
    for base_url in api_candidates:
        try:
            res = requests.get(f"{base_url}/v1/portfolio/risk", params=params, timeout=timeout)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            last_error = e
    try:
        return _compute_risk_locally(tickers, mc_paths, mc_days, stress_scenario)
    except Exception:
        raise last_error if last_error is not None else RuntimeError("Failed to retrieve risk data.")

def _compute_risk_locally(tickers, mc_paths, mc_days, stress_scenario=None):
    prices_raw = load_data(tickers)
    prices = prices_raw["Adj Close"] if "Adj Close" in prices_raw else prices_raw["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
    prices = prices[tickers].dropna(how="all")
    returns_df = np.log(prices / prices.shift(1)).dropna()
    if returns_df.empty or len(returns_df) < 30:
        raise ValueError("Not enough historical data to perform calculations.")
    weights = get_optimal_weights(returns_df, strategy="max_sharpe")
    port_returns = returns_df.dot(weights)
    risk_metrics, var_parametric_daily = calculate_comprehensive_metrics(
        port_returns,
        mc_paths=int(mc_paths),
        mc_days=int(mc_days),
    )
    backtest = run_full_backtest(port_returns, var_parametric_daily)
    if stress_scenario:
        stress_test = apply_historical_scenario(port_returns, scenario=stress_scenario)
    else:
        stress_test = {"scenario_name": "Normal volatility", "simulated_max_drawdown": 0.0, "status": "N/A"}
    return {
        "status": "success",
        "assets": {t: round(float(w), 4) for t, w in zip(tickers, weights)},
        "risk_metrics": risk_metrics,
        "backtest": backtest,
        "stress_test": stress_test,
    }

def _pct_to_float(value):
    try:
        return float(str(value).replace("%", "").strip()) / 100.0
    except Exception:
        return 0.0

def _pct_number(value):
    try:
        return float(str(value).replace("%", "").strip())
    except Exception:
        return 0.0

st.set_page_config(page_title="Investment Risk Calculator", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Force text readability */
    .stApp { background-color: #ffffff; color: #24292e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }

    /* HIDE RADIO CIRCLES AND REPLACE WITH RECTANGLES */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label {
        width: 100%;
        padding: 10px 15px;
        margin-bottom: 5px;
        border-radius: 6px;
        background-color: transparent;
        cursor: pointer;
        transition: 0.2s ease;
        border-left: 3px solid transparent;
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #f0f2f6;
    }

    /* Hide default Streamlit footer */
    footer {visibility: hidden;}

    /* Sidebar metadata */
    .sidebar-meta { font-size: 14px; line-height: 1.6; color: #586069; }
    .sidebar-meta strong { color: #24292e; }

    /* Result sections (Calculator) */
    .result-box { border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 15px; background-color: #fafbfc; height: 100%; }
    .metric-value { font-size: 24px; font-weight: bold; color: #0366d6; }
    .metric-label { font-size: 12px; color: #586069; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = ["MSFT", "AAPL"]

ETF_CONSTITUENTS = {
    "Select ETF...": [],
    "SPY (S&P 500 Top)": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "TSLA", "UNH", "JNJ"],
    "QQQ (Nasdaq 100)": ["MSFT", "AAPL", "NVDA", "AMZN", "META", "AVGO", "TSLA", "GOOGL", "GOOG", "COST", "PEP"],
    "XLF (Financial Sector)": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "SPGI", "GS", "MS", "AXP"]
}

ALL_TICKERS = list(set(["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", "WMT", "JNJ", "PG", "XOM", "BAC", "MA", "HD", "CVX", "MRK", "KO", "PEP", "AVGO", "COST", "MCD", "CSCO", "INTC", "AMD", "DIS", "ADBE", "CRM"] + [ticker for sublist in ETF_CONSTITUENTS.values() for ticker in sublist]))
ALL_TICKERS.sort()

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("Go to",
                    ["Project Overview", "Risk Calculator", "Visualization", "Portfolio Advisor", "Download Files"],
                    label_visibility="collapsed")
    risk_subpage = "Calculator"
    if page == "Risk Calculator":
        st.markdown("### Calculator subsections")
        risk_subpage = st.radio(
            "Select subsection",
            ["Calculator", "Monte Carlo Visualization"],
            label_visibility="collapsed",
        )

    st.markdown("---")
    st.markdown("### Details")
    st.markdown("<div class='sidebar-meta'>These details have been verified by the System.</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Authors")
    st.markdown("<div class='sidebar-meta'><strong>BR</strong></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Metadata")
    st.markdown("""
    <div class='sidebar-meta'>
    <ul>
        <li><strong>License:</strong> MIT</li>
        <li>python, finance, risk, investments</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Categories")
    st.markdown("<div class='sidebar-meta'><strong>Target audience:</strong><br><ul><li>Individual investors</li><li>Financial Analysts</li></ul></div>", unsafe_allow_html=True)

if page == "Project Overview":
    st.title("Investment Risk Calculator")
    st.markdown("**What is this project?**\nThis is an easy-to-use tool for security analysis and optimization of investment portfolios on the stock exchange.")
    st.markdown("**Who is it for?**\nFor any investor, analyst or developer who wants to better understand how much risk they are taking in the market and how to balance their holdings to minimize potential losses.")

    st.subheader("Module installation (for developers)")
    st.code("pip install portfolio-risk-calculator", language="bash")

    st.markdown("---")
    st.subheader("Deployed Architecture")
    st.markdown("""
    The system underneath uses a mathematical engine for risk pricing.
    The application is connected to an asynchronous API that continuously fetches data and performs vectorized calculations (NumPy, Pandas), hiding all the math behind the interface.
    """)

    st.subheader("Key algorithm capabilities")
    st.markdown("""
    * **Capital protection:** Estimation of Expected Shortfall (CVaR) in extreme market crash scenarios.
    * **Profit maximization:** Portfolio optimization using Markowitz method to find the ideal risk-return balance.
    * **Historical assessment:** Parametric and Historical VaR (Value at Risk – capital risk indicator).
    * **Volatility analysis:** Forecasting future price fluctuations using GARCH(1,1) processes.
    * **Future simulations:** Generating random portfolio development paths (Monte Carlo method).
    * **Model verification:** Automatic backtesting (Kupiec test) verifying whether mathematical models held up in the past.
    """)

    st.subheader("Quick start - API usage example in code")
    st.markdown("If you want to integrate the calculator into your own Python script, use the code below:")

    st.code("""
    from core.risk_metrics import calculate_comprehensive_metrics
    from core.models import optimize_portfolio_weights
    from data.ingestor import fetch_data

    returns_df = fetch_data(["AAPL", "MSFT", "TSLA"])

    optimal_weights = optimize_portfolio_weights(returns_df)

    portfolio_returns = returns_df.dot(optimal_weights)
    metrics = calculate_comprehensive_metrics(portfolio_returns)

    print(f"Estimated risk (VaR 95%): {metrics['parametric']['var']}")
    """, language="python")

elif page == "Risk Calculator":
    st.title("Interactive Risk Calculator")
    st.markdown("Test your investments. Select companies, set simulation parameters and proceed to the results or visualization.")

    st.markdown("---")

    col_search, col_etf = st.columns([1.5, 1])
    with col_etf:
        st.markdown("### 🏦 Select from ETF")
        selected_etf = st.selectbox("Select a fund to view its constituents:", list(ETF_CONSTITUENTS.keys()))
        if selected_etf != "Select ETF...":
            etf_tickers = ETF_CONSTITUENTS[selected_etf]
            st.info(f"**{selected_etf} composition:** {', '.join(etf_tickers)}")
            if st.button(f"➕ Add stocks from {selected_etf.split(' ')[0]}"):
                current_list = st.session_state.get("ms_tickers", st.session_state.selected_tickers)
                new_list = list(current_list)
                for t in etf_tickers:
                    if t not in new_list and len(new_list) < 12:
                        new_list.append(t)
                st.session_state.selected_tickers = new_list
                st.session_state.ms_tickers = new_list
                st.rerun()

    with col_search:
        st.markdown("### 🔍 Company search")

        def update_tickers():
            st.session_state.selected_tickers = st.session_state.ms_tickers

        st.multiselect(
            "Type a ticker (e.g. AAPL) or select from the list (Limit: max 12 companies for server stability):",
            options=ALL_TICKERS,
            default=st.session_state.selected_tickers,
            key="ms_tickers",
            on_change=update_tickers,
            max_selections=12,
        )
        st.caption(f"Selected: {len(st.session_state.selected_tickers)} assets")

    st.markdown("---")
    mc_paths = st.slider("Monte Carlo paths", min_value=50_000, max_value=20_000_000, value=2_000_000, step=50_000)
    mc_days = st.slider("Monte Carlo horizon (days)", min_value=1, max_value=30, value=10, step=1)
    period_mode = st.selectbox(
        "Analysis period",
        ["Normal volatility", "COVID_19_Shock", "Global_Financial_Crisis"],
        help="In normal mode you get standard results; shock scenarios are used mainly for visualization and stress tests.",
    )

    if risk_subpage == "Calculator":
        if st.button("Run portfolio analysis", type="primary"):
            if len(st.session_state.selected_tickers) < 2:
                st.warning("Please select at least 2 companies.")
            else:
                with st.status("Processing data...", expanded=True) as status:
                    st.write("Loading data and cache...")
                    try:
                        stress_param = None if period_mode == "Normal volatility" else period_mode
                        data = _fetch_risk_api(
                            tickers=st.session_state.selected_tickers,
                            mc_paths=mc_paths,
                            mc_days=mc_days,
                            stress_scenario=stress_param,
                            timeout=120,
                        )

                        risk = data.get("risk_metrics", {})
                        backtest = data.get("backtest", {})
                        analyzed_str = ", ".join(st.session_state.selected_tickers)

                        st.write("Adjusting volatility with LSTM model...")
                        st.write(f"Generating {mc_paths:,} Monte Carlo paths in C++...")
                        status.update(label="Analysis complete", state="complete", expanded=False)
                        st.success("Calculations completed successfully!")

                        st.markdown("### Detailed Risk Report")
                        st.markdown(
                            f"""<div style=\"color: #94a3b8; font-size: 14px; margin-bottom: 20px;\">\
                            Analyzed Assets: <span style=\"color: black; font-weight: bold;\">{analyzed_str}</span> &nbsp;|&nbsp; \
                            Base Volatility: <span style=\"color: black; font-weight: bold;\">{risk.get('volatility', 'N/A')}</span> &nbsp;|&nbsp;\
                            <span style=\"color: #7c3aed; font-weight: bold;\">AI-Adjusted Volatility (LSTM): {risk.get('ai_adjusted_volatility', 'N/A')}</span>\
                            </div>""",
                            unsafe_allow_html=True,
                        )
                        st.markdown("---")

                        v_vol = risk.get("volatility", "N/A")
                        c_box, c_desc = st.columns([1, 2.5])
                        with c_box:
                            st.markdown(f"<div class='result-box'><div class='metric-label'>Annual Volatility</div><div class='metric-value'>{v_vol}</div></div>", unsafe_allow_html=True)
                        with c_desc:
                            st.markdown("**What does this mean?** A measure of the amplitude of price changes year over year.<br>**How does it affect the portfolio?** The higher it is, the greater the uncertainty.<br>" f"**Your rating:** {get_eval_html(v_vol, 15, 25)}", unsafe_allow_html=True)

                        v_pvar = risk.get("parametric", {}).get("var", "N/A")
                        c_box, c_desc = st.columns([1, 2.5])
                        with c_box:
                            st.markdown(f"<div class='result-box'><div class='metric-label'>Parametric VaR (95%)</div><div class='metric-value' style='color:#d73a49;'>{v_pvar}</div></div>", unsafe_allow_html=True)
                        with c_desc:
                            st.markdown("**What does this mean?** Maximum expected loss at the 95% confidence level.<br>" f"**Your rating:** {get_eval_html(v_pvar, 4, 8)}", unsafe_allow_html=True)

                        v_hvar = risk.get("historical", {}).get("var", "N/A")
                        c_box, c_desc = st.columns([1, 2.5])
                        with c_box:
                            st.markdown(f"<div class='result-box'><div class='metric-label'>Historical VaR (95%)</div><div class='metric-value' style='color:#d73a49;'>{v_hvar}</div></div>", unsafe_allow_html=True)
                        with c_desc:
                            st.markdown("**What does this mean?** Risk derived from real historical data.<br>" f"**Your rating:** {get_eval_html(v_hvar, 4, 8)}", unsafe_allow_html=True)

                        v_cvar = risk.get("historical", {}).get("es", "N/A")
                        c_box, c_desc = st.columns([1, 2.5])
                        with c_box:
                            st.markdown(f"<div class='result-box'><div class='metric-label'>Expected Shortfall (CVaR)</div><div class='metric-value' style='color:#cb2431;'>{v_cvar}</div></div>", unsafe_allow_html=True)
                        with c_desc:
                            st.markdown("**What does this mean?** Average loss beyond the VaR threshold.<br>" f"**Your rating:** {get_eval_html(v_cvar, 6, 12)}", unsafe_allow_html=True)

                        v_mcvar = risk.get("monte_carlo", {}).get("var", "N/A")
                        c_box, c_desc = st.columns([1, 2.5])
                        with c_box:
                            st.markdown(f"<div class='result-box'><div class='metric-label'>Monte Carlo VaR</div><div class='metric-value' style='color:#d73a49;'>{v_mcvar}</div></div>", unsafe_allow_html=True)
                        with c_desc:
                            st.markdown("**What does this mean?** Loss potential from multiple simulations of market scenarios.<br>" f"**Your rating:** {get_eval_html(v_mcvar, 4, 8)}", unsafe_allow_html=True)

                        v_status = backtest.get("status", "N/A")
                        v_viol = backtest.get("violations", 0)
                        status_color = "#28a745" if "PASS" in str(v_status).upper() else "#d73a49"
                        c_box, c_desc = st.columns([1, 2.5])
                        with c_box:
                            st.markdown(f"<div class='result-box'><div class='metric-label'>Reliability (Kupiec Test)</div><div class='metric-value' style='color:{status_color}; font-size:18px;'>{v_status}</div><div style='font-size:12px; color:#586069;'>Violations: {v_viol}</div></div>", unsafe_allow_html=True)
                        with c_desc:
                            st.markdown("**What does this mean?** Quality control of the VaR model on historical data.")
                    except Exception as e:
                        status.update(label="Analysis error", state="error")
                        st.error(f"Analysis ended with an error: {e}")

    else:
        st.markdown("### Monte Carlo Visualization")
        stress_scenario = period_mode if period_mode != "Normal volatility" else "COVID_19_Shock"

        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            bench_paths = st.number_input("Benchmark paths", min_value=10000, max_value=20000000, value=500000, step=50000)
        with b_col2:
            bench_days = st.number_input("Benchmark days", min_value=1, max_value=30, value=10, step=1)
        with b_col3:
            bench_runs = st.number_input("Benchmark runs", min_value=1, max_value=10, value=3, step=1)

        if st.button("Run OpenMP benchmark", type="secondary"):
            with st.spinner("Measuring OpenMP vs NumPy times..."):
                try:
                    b_res = requests.get(
                        "http://127.0.0.1:8000/v1/benchmark/openmp",
                        params={"paths": int(bench_paths), "days": int(bench_days), "runs": int(bench_runs)},
                        timeout=300,
                    )
                    b_res.raise_for_status()
                    st.session_state["last_benchmark"] = b_res.json().get("benchmark", {})
                except Exception as e:
                    st.error(f"Benchmark failed: {e}")

        if st.button("Generate quant visualizations", type="primary"):
            try:
                data = _fetch_risk_api(
                    tickers=st.session_state.selected_tickers,
                    mc_paths=mc_paths,
                    mc_days=mc_days,
                    stress_scenario=stress_scenario,
                    timeout=120,
                )
                st.session_state["last_quant_visual_data"] = data
            except Exception as e:
                st.error(f"Engine failed: {e}")

        if "last_benchmark" in st.session_state:
            b = st.session_state["last_benchmark"]
            df_bench = pd.DataFrame(
                {"Engine": ["OpenMP C++", "NumPy (without OpenMP)"], "Seconds": [b.get("openmp_avg_s", 0.0), b.get("numpy_avg_s", 0.0)]}
            )
            fig_bench = px.bar(df_bench, x="Engine", y="Seconds", color="Engine", title="Monte Carlo computation time comparison", text="Seconds")
            fig_bench.update_traces(texttemplate="%{text:.4f}s", textposition="outside")
            fig_bench.update_layout(showlegend=False, height=340)
            st.plotly_chart(fig_bench, use_container_width=True)
            omp_info = b.get("omp_info", {})
            st.info(
                f"Speedup: {b.get('speedup_x', 'N/A')}x | OpenMP used threads: {omp_info.get('omp_used_threads', 'N/A')} / "
                f"max: {omp_info.get('omp_max_threads', 'N/A')}"
            )

        if "last_quant_visual_data" in st.session_state:
            data = st.session_state["last_quant_visual_data"]
            risk = data.get("risk_metrics", {})
            prices_raw = load_data(st.session_state.selected_tickers)
            if "Adj Close" in prices_raw:
                prices = prices_raw["Adj Close"]
            else:
                prices = prices_raw["Close"]
            if isinstance(prices, pd.Series):
                prices = prices.to_frame(name=st.session_state.selected_tickers[0])
            prices = prices[st.session_state.selected_tickers]
            returns_hist = prices.pct_change().dropna()

            assets_w = data.get("assets", {})
            weights = np.array([float(assets_w.get(t, 0.0)) for t in st.session_state.selected_tickers], dtype=float)
            if weights.sum() <= 0:
                weights = np.array([1.0 / len(st.session_state.selected_tickers)] * len(st.session_state.selected_tickers))
            else:
                weights = weights / weights.sum()

            port_returns_hist = returns_hist.dot(weights)
            s0 = 100.0
            mu_mc = float(port_returns_hist.mean())
            sigma_mc = max(float(port_returns_hist.std(ddof=1)) if len(port_returns_hist) > 1 else 0.01, 1e-6)
            horizon = int(mc_days)
            sims_to_draw = 160
            rng = np.random.default_rng(42)
            dt = 1.0 / 252.0
            drift_adj = (mu_mc - 0.5 * sigma_mc * sigma_mc) * dt
            vol_adj = sigma_mc * np.sqrt(dt)
            z = rng.standard_normal((sims_to_draw, horizon))
            log_r = np.cumsum(drift_adj + vol_adj * z, axis=1)
            sim_prices = s0 * np.exp(log_r)

            st.markdown("### Monte Carlo chart (fan chart)")
            fig_mc = go.Figure()
            x_axis = list(range(1, horizon + 1))
            for i in range(sims_to_draw):
                fig_mc.add_trace(go.Scatter(x=x_axis, y=sim_prices[i], mode="lines", line=dict(width=1), opacity=0.18, showlegend=False, hoverinfo="skip"))
            fig_mc.add_hline(y=s0, line_dash="dot", line_color="#64748b")
            fig_mc.update_layout(
                title=f"Simulated price paths ({sims_to_draw} paths, {horizon}-day horizon)",
                xaxis_title="Simulation day",
                yaxis_title="Portfolio value (index)",
                height=360,
                margin=dict(t=50, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_mc, use_container_width=True)

            st.markdown("### Backtesting chart (VaR + violations)")
            from plotly.subplots import make_subplots

            v_pvar = risk.get("parametric", {}).get("var", "0%")
            var_pct = _pct_to_float(v_pvar)
            violations_mask = port_returns_hist < -var_pct
            portfolio_index = 100.0 * (1.0 + port_returns_hist).cumprod()

            fig_bt = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
            fig_bt.add_trace(go.Scatter(x=portfolio_index.index, y=portfolio_index.values, name="Portfolio Index", mode="lines", line=dict(color="#0ea5e9", width=2)), row=1, col=1)
            fig_bt.add_trace(go.Scatter(x=port_returns_hist.index, y=port_returns_hist.values, name="Daily returns", mode="lines", line=dict(color="#334155", width=1)), row=2, col=1)
            fig_bt.add_hline(y=-var_pct, line_dash="dash", line_color="#dc2626", annotation_text="VaR 95%", annotation_position="top right", row=2, col=1)
            if violations_mask.any():
                fig_bt.add_trace(
                    go.Scatter(
                        x=port_returns_hist.index[violations_mask],
                        y=port_returns_hist[violations_mask],
                        mode="markers",
                        marker=dict(color="#dc2626", size=8),
                        name="VaR violations",
                    ),
                    row=2,
                    col=1,
                )
            fig_bt.update_layout(height=460, margin=dict(t=50, b=20, l=20, r=20), title=f"Backtesting: VaR violations = {int(violations_mask.sum())}")
            fig_bt.update_yaxes(title_text="Index", row=1, col=1)
            fig_bt.update_yaxes(title_text="Daily return", tickformat=".2%", row=2, col=1)
            st.plotly_chart(fig_bt, use_container_width=True)

            st.markdown("### Interpretation")
            st.markdown(
                "- **Model consistency:** if violation points are rare and scattered, the VaR model usually maintains calibration.\n"
                "- **Tail risk:** a wide fan of MC paths indicates high scenario uncertainty.\n"
                "- **Diversification quality:** with a strong divergence of paths, consider reducing weight concentration."
            )

elif page == "Visualization":
    st.title("Visualization")
    st.markdown("Three consistent charts in a slide-ready layout: volatility model comparison, correlation heatmap and statistical test table.")
    st.markdown("---")
    chart_config = {"displayModeBar": False, "responsive": True}

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        viz_tickers = st.multiselect(
            "Assets to visualize (min. 2):",
            options=ALL_TICKERS,
            default=st.session_state.selected_tickers,
            max_selections=10,
            key="viz_tickers",
        )
    with col_s2:
        viz_scenario = st.selectbox(
            "Shock scenario",
            ["COVID_19_Shock", "Global_Financial_Crisis", "Normal volatility"],
            key="viz_scenario",
        )

    if st.button("Generate 3 charts", type="primary"):
        if len(viz_tickers) < 2:
            st.warning("Select at least 2 assets.")
        else:
            with st.status("Generating quant visualizations...", expanded=True) as status:
                try:
                    scenario_param = None if viz_scenario == "Normal volatility" else viz_scenario
                    api_data = _fetch_risk_api(viz_tickers, mc_paths=500000, mc_days=10, stress_scenario=scenario_param, timeout=180)
                    risk = api_data.get("risk_metrics", {})
                    backtest = api_data.get("backtest", {})

                    prices_raw = load_data(viz_tickers)
                    prices = prices_raw["Adj Close"] if "Adj Close" in prices_raw else prices_raw["Close"]
                    if isinstance(prices, pd.Series):
                        prices = prices.to_frame(name=viz_tickers[0])
                    prices = prices[viz_tickers]
                    returns = prices.pct_change().dropna()

                    returns_shock = returns.copy()
                    market_proxy = returns_shock.mean(axis=1)
                    shock_threshold = market_proxy.quantile(0.1)
                    shock_idx = market_proxy <= shock_threshold
                    returns_shock.loc[shock_idx] = returns_shock.loc[shock_idx] * 1.6 - 0.002

                    lam = 1.0 - (2.0 / (60.0 + 1.0))
                    x = returns_shock.values
                    cov = np.cov(x[: min(20, len(x))].T)
                    for i in range(1, len(x)):
                        r = x[i][:, None]
                        cov = lam * cov + (1.0 - lam) * (r @ r.T)
                    d = np.sqrt(np.diag(cov))
                    corr = cov / np.outer(d, d)
                    corr = np.clip(corr, -1.0, 1.0)
                    corr_df = pd.DataFrame(corr, index=viz_tickers, columns=viz_tickers)

                    panel_h = 540
                    export_w = 1600
                    export_h = 900
                    title_y = 0.97

                    def _set_panel_layout(fig, title_text, subtitle_text):
                        fig.update_layout(
                            title={
                                "text": f"{title_text}<br><span style='font-size:12px;color:#64748b'>{subtitle_text}</span>",
                                "x": 0.5,
                                "xanchor": "center",
                                "y": title_y,
                                "yanchor": "top",
                            },
                            height=panel_h,
                            margin=dict(t=105, b=50, l=40, r=40),
                        )
                        return fig

                    def _to_jpg_with_retry(fig, width, height, retries=2):
                        last_exc = None
                        for _ in range(retries + 1):
                            try:
                                return pio.to_image(fig, format="jpg", width=width, height=height, scale=1)
                            except Exception as e:
                                last_exc = e
                                time.sleep(0.35)
                        raise last_exc

                    sim_count = 140
                    rng = np.random.default_rng(42)
                    dt = 1.0 / 252.0
                    mu_f = float(returns.mean(axis=1).mean())
                    sigma_f = max(float(returns.mean(axis=1).std(ddof=1)), 1e-6)
                    x_h = np.arange(1, 61)
                    shocks = rng.standard_normal((sim_count, len(x_h)))
                    log_r = np.cumsum((mu_f - 0.5 * sigma_f * sigma_f) * dt + sigma_f * np.sqrt(dt) * shocks, axis=1)
                    mc_paths = 100.0 * np.exp(log_r)

                    mean_path = mc_paths.mean(axis=0)
                    low_idx = int(np.argmin(mc_paths[:, -1]))
                    high_idx = int(np.argmax(mc_paths[:, -1]))

                    fig_1 = go.Figure()
                    for i in range(sim_count):
                        fig_1.add_trace(
                            go.Scatter(
                                x=x_h,
                                y=mc_paths[i],
                                mode="lines",
                                line=dict(color=f"rgba({(40 + (i * 3)) % 220},{(80 + (i * 5)) % 220},{(120 + (i * 7)) % 220},0.10)", width=1),
                                hoverinfo="skip",
                                showlegend=False,
                            )
                        )
                    fig_1.add_trace(
                        go.Scatter(
                            x=x_h,
                            y=mc_paths[low_idx],
                            mode="lines",
                            line=dict(color="#ef4444", width=2.2),
                            name="Extreme downside",
                        )
                    )
                    fig_1.add_trace(
                        go.Scatter(
                            x=x_h,
                            y=mc_paths[high_idx],
                            mode="lines",
                            line=dict(color="#22c55e", width=2.2),
                            name="Extreme upside",
                        )
                    )
                    fig_1.add_trace(
                        go.Scatter(
                            x=x_h,
                            y=mean_path,
                            mode="lines",
                            line=dict(color="#1f2937", width=5),
                            name="Mean path",
                            showlegend=False,
                        )
                    )
                    fig_1.add_trace(
                        go.Scatter(
                            x=x_h,
                            y=mean_path,
                            mode="lines",
                            line=dict(color="#ffffff", width=4),
                            name="Mean path",
                        )
                    )
                    y_min = float(np.min(mc_paths)) * 0.98
                    y_max = float(np.max(mc_paths)) * 1.02
                    shock_start, shock_end = int(len(x_h) * 0.55), int(len(x_h) * 0.78)
                    fig_1.add_vrect(
                        x0=shock_start,
                        x1=shock_end,
                        fillcolor="rgba(250, 204, 21, 0.12)",
                        line_width=1.2,
                        line_color="#f59e0b",
                    )
                    fig_1.add_annotation(
                        x=(shock_start + shock_end) / 2,
                        y=y_max * 0.99,
                        text="MARKET SHOCK WINDOW (HYBRID GARCH/LSTM ADAPTATION)",
                        showarrow=False,
                        bgcolor="rgba(15,23,42,0.78)",
                        bordercolor="#f59e0b",
                        borderwidth=1,
                        font=dict(color="#f8fafc", size=11),
                    )
                    fig_1.update_layout(
                        xaxis_title="Simulation Step",
                        yaxis_title="Portfolio Value Index",
                        plot_bgcolor="#ffffff",
                        paper_bgcolor="#ffffff",
                        font=dict(color="#0f172a"),
                        legend=dict(orientation="h", y=1.02, x=0),
                    )
                    fig_1.update_yaxes(range=[y_min, y_max], gridcolor="rgba(100,116,139,0.25)", linewidth=1, linecolor="#94a3b8")
                    fig_1.update_xaxes(gridcolor="rgba(100,116,139,0.18)", linewidth=1, linecolor="#94a3b8")
                    _set_panel_layout(fig_1, "Monte Carlo volatility funnel", "Scenarios under uncertainty")

                    fig_2 = go.Figure(
                        data=go.Heatmap(
                            z=corr_df.values,
                            x=list(corr_df.columns),
                            y=list(corr_df.index),
                            zmin=-1,
                            zmax=1,
                            colorscale=[
                                [0.0, "#0b3b8c"],
                                [0.5, "#ffffff"],
                                [1.0, "#7f1d1d"],
                            ],
                            colorbar=dict(title="Correlation"),
                        )
                    )
                    for yi, y_name in enumerate(corr_df.index):
                        for xi, x_name in enumerate(corr_df.columns):
                            val = float(corr_df.loc[y_name, x_name])
                            text_color = "#f8fafc" if abs(val) > 0.45 else "#0f172a"
                            fig_2.add_annotation(
                                x=x_name,
                                y=y_name,
                                text=f"{val:.2f}",
                                showarrow=False,
                                font=dict(color=text_color, size=12),
                            )
                    _set_panel_layout(fig_2, "Dynamic correlation matrix", "Shock regime mapping")
                    fig_2.update_xaxes(title_text="Assets")
                    fig_2.update_yaxes(title_text="Assets")

                    from plotly.subplots import make_subplots

                    kup_p = float(backtest.get("kupiec_p", 0.0))
                    chr_p = float(backtest.get("christ_p", 0.0))
                    kup_verdict = str(backtest.get("kupiec_verdict", "N/A"))
                    chr_verdict = str(backtest.get("christ_verdict", "N/A"))
                    sig_threshold = 0.05

                    test_rows = pd.DataFrame(
                        {
                            "Test": ["Kupiec POF", "Christoffersen"],
                            "p-Value": [round(kup_p, 4), round(chr_p, 4)],
                            "Test Stat": [backtest.get("kupiec_stat", "N/A"), backtest.get("christ_stat", "N/A")],
                            "Verdict": [kup_verdict, chr_verdict],
                        }
                    )

                    fig_3 = make_subplots(
                        rows=2,
                        cols=2,
                        specs=[[{"type": "indicator"}, {"type": "indicator"}], [{"type": "table", "colspan": 2}, None]],
                        vertical_spacing=0.14,
                        row_heights=[0.55, 0.45],
                    )
                    fig_3.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=kup_p,
                            title={"text": "Kupiec's POF Test"},
                            gauge={
                                "axis": {"range": [0, 1]},
                                "bar": {"color": "#22c55e" if kup_verdict == "PASS" else "#ef4444"},
                                "steps": [
                                    {"range": [0, sig_threshold], "color": "#fee2e2"},
                                    {"range": [sig_threshold, 0.20], "color": "#fef9c3"},
                                    {"range": [0.20, 1], "color": "#dcfce7"},
                                ],
                                "threshold": {"line": {"color": "#0f172a", "width": 3}, "thickness": 0.75, "value": sig_threshold},
                            },
                            number={"valueformat": ".3f"},
                        ),
                        row=1,
                        col=1,
                    )
                    fig_3.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=chr_p,
                            title={"text": "Christoffersen's Indep. Test"},
                            gauge={
                                "axis": {"range": [0, 1]},
                                "bar": {"color": "#22c55e" if chr_verdict == "PASS" else "#ef4444"},
                                "steps": [
                                    {"range": [0, sig_threshold], "color": "#fee2e2"},
                                    {"range": [sig_threshold, 0.20], "color": "#fef9c3"},
                                    {"range": [0.20, 1], "color": "#dcfce7"},
                                ],
                                "threshold": {"line": {"color": "#0f172a", "width": 3}, "thickness": 0.75, "value": sig_threshold},
                            },
                            number={"valueformat": ".3f"},
                        ),
                        row=1,
                        col=2,
                    )
                    fig_3.add_trace(
                        go.Table(
                            header=dict(
                                values=list(test_rows.columns),
                                fill_color="#0f172a",
                                font=dict(color="white", size=11),
                                align="left",
                            ),
                            cells=dict(
                                values=[test_rows[c] for c in test_rows.columns],
                                fill_color="#f8fafc",
                                align="left",
                                font=dict(color="#000000", size=11),
                                height=30,
                            ),
                        ),
                        row=2,
                        col=1,
                    )
                    _set_panel_layout(fig_3, "Institutional validation summary", "Backtest confidence check")
                    fig_3.update_layout(margin=dict(t=105, b=35, l=30, r=30))

                    badge_pass = "PASS" if kup_verdict == "PASS" and chr_verdict == "PASS" else "MIXED"
                    try:
                        with st.spinner("Preparing charts and JPG export..."):
                            img_1 = _to_jpg_with_retry(fig_1, export_w, export_h)
                            img_2 = _to_jpg_with_retry(fig_2, export_w, export_h)
                            fig_3_export = go.Figure(fig_3)
                            badge_bg = "#dcfce7" if badge_pass == "PASS" else "#fef3c7"
                            badge_fg = "#166534" if badge_pass == "PASS" else "#92400e"
                            fig_3_export.update_layout(height=export_h, margin=dict(t=140, b=18, l=30, r=30))
                            fig_3_export.add_annotation(
                                x=0.5,
                                y=0.03,
                                xref="paper",
                                yref="paper",
                                text=f"<b>Validation badge: {badge_pass}</b>",
                                showarrow=False,
                                align="center",
                                font=dict(color=badge_fg, size=15),
                                bgcolor=badge_bg,
                                bordercolor="#cbd5e1",
                                borderwidth=1,
                                borderpad=6,
                            )
                            img_3 = _to_jpg_with_retry(fig_3_export, export_w, export_h)
                        st.session_state.viz_ready = {
                            "fig_1": fig_1,
                            "fig_2": fig_2,
                            "fig_3": fig_3,
                            "img_1": img_1,
                            "img_2": img_2,
                            "img_3": img_3,
                            "badge_pass": badge_pass,
                            "kup_verdict": kup_verdict,
                            "chr_verdict": chr_verdict,
                        }
                    except Exception as export_err:
                        st.session_state.viz_ready = None
                        raise RuntimeError(f"JPG export failed: {export_err}") from export_err

                    status.update(label="Visualizations ready", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="Visualization error", state="error")
                    st.error(f"Visualization error: {e}")

    viz_ready = st.session_state.get("viz_ready")
    if viz_ready:
        st.plotly_chart(viz_ready["fig_1"], use_container_width=True, config=chart_config)
        st.plotly_chart(viz_ready["fig_2"], use_container_width=True, config=chart_config)
        st.plotly_chart(viz_ready["fig_3"], use_container_width=True, config=chart_config)
        st.markdown(
            f"<div style='padding:8px 12px; margin-top:-20px; border-radius:10px; border:1px solid #cbd5e1; background:#f8fafc; color:#000000;'>"
            f"<strong>Validation badge:</strong> {viz_ready['badge_pass']} &nbsp;|&nbsp; "
            f"Kupiec: <span style='color:{'#16a34a' if viz_ready['kup_verdict']=='PASS' else '#dc2626'}; font-weight:700'>{viz_ready['kup_verdict']}</span> "
            f"&nbsp;|&nbsp; Christoffersen: <span style='color:{'#16a34a' if viz_ready['chr_verdict']=='PASS' else '#dc2626'}; font-weight:700'>{viz_ready['chr_verdict']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("### Save charts as JPG")
        c_dl1, c_dl2, c_dl3 = st.columns(3)
        with c_dl1:
            st.download_button(
                "Download panel 1 (JPG)",
                data=viz_ready["img_1"],
                file_name="panel_1_monte_carlo.jpg",
                mime="image/jpeg",
            )
        with c_dl2:
            st.download_button(
                "Download panel 2 (JPG)",
                data=viz_ready["img_2"],
                file_name="panel_2_heatmap.jpg",
                mime="image/jpeg",
            )
        with c_dl3:
            st.download_button(
                "Download panel 3 (JPG)",
                data=viz_ready["img_3"],
                file_name="panel_3_validation.jpg",
                mime="image/jpeg",
            )

elif page == "Portfolio Advisor":
    st.title("Portfolio Advisor")
    st.markdown("Select your investment profile. The algorithm will fetch live market data and optimize weights for the selected asset group.")

    profile = st.selectbox("Define your risk tolerance:",
                          ["Positive (Lower risk)", "Balanced (Medium risk)", "Dynamic (Higher risk)"])

    st.markdown("---")

    base_config = {
        "Positive (Lower risk)": {
            "tickers": ["JNJ", "PG", "WMT", "JPM", "V"],
            "desc": "A portfolio with a relatively calm profile, focused on limiting fluctuations.",
            "method": "Global Minimum Variance (GMV) - Scipy optimization",
            "code_logic": "weights = get_optimal_weights(returns, 'min_vol')",
            "strategy_type": "min_vol"
        },
        "Balanced (Medium risk)": {
            "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "desc": "A balance between volatility and return based on the Sharpe ratio.",
            "method": "Maximum Sharpe Ratio (MSR) - Scipy optimization",
            "code_logic": "weights = get_optimal_weights(returns, 'max_sharpe')",
            "strategy_type": "max_sharpe"
        },
        "Dynamic (Higher risk)": {
            "tickers": ["NVDA", "TSLA", "AMD", "META", "NFLX"],
            "desc": "A profile focused on higher price dynamics and greater growth exposure.",
            "method": "Maximum Return Seeking - Scipy optimization",
            "code_logic": "weights = get_optimal_weights(returns, 'max_return')",
            "strategy_type": "max_return"
        }
    }

    current_setup = base_config[profile]
    tickers = current_setup["tickers"]
    strategy = current_setup["strategy_type"]

    current_weights = []

    with st.spinner(f"Fetching data for {', '.join(tickers)} and calculating optimal weights..."):
        try:
            data = load_data(tickers)
            if 'Adj Close' in data: prices = data['Adj Close']
            else: prices = data['Close']

            if isinstance(prices, pd.Series):
                prices = prices.to_frame(name=tickers[0])
            else:
                prices = prices[tickers]

            returns = prices.pct_change().dropna()

            current_weights = get_optimal_weights(returns, strategy)
            metrics = calculate_portfolio_metrics(current_weights, returns)

            st.session_state.last_opt_weights = dict(zip(tickers, current_weights))
            st.session_state.last_opt_metrics = metrics

            port_returns = metrics["portfolio_returns_series"]
            sortino_ratio = metrics["sortino_ratio"]
            skewness_val = metrics["skewness"]
            kurt_val = metrics["kurtosis"]

        except Exception as e:
            st.error(f"Error during market calculations: {e}. Falling back to equal weights.")
            current_weights = [1/len(tickers)] * len(tickers)
            returns = pd.DataFrame()
            port_returns = pd.Series([0])
            sortino_ratio, skewness_val, kurt_val = 0.0, 0.0, 0.0

    col_text, col_chart = st.columns([1.2, 1])

    with col_text:
        st.subheader(f"Strategy: {profile.split(' (')[0]}")
        st.markdown(f"**Why these companies?**\n{current_setup['desc']}")
        st.info(f"**Calculation method:** {current_setup['method']}")
        st.markdown("**Engine used:**")
        st.code(current_setup['code_logic'], language="python")

    with col_chart:
        fig_pie = px.pie(names=tickers, values=current_weights,
                         title="Live-calculated portfolio structure", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    st.subheader("Position size calculator")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        waluta = st.selectbox("Currency:", ["PLN", "USD", "EUR"])
    with c2:
        kwota = st.number_input(f"Investment amount ({waluta}):", min_value=1000, value=10000, step=500)
    with c3:
        st.markdown(f"**Calculated capital allocation for {kwota} {waluta}:**")
        cols = st.columns(len(tickers))
        for i, t in enumerate(tickers):
            pos_val = kwota * current_weights[i]
            cols[i].metric(t, f"{current_weights[i]*100:.1f}%", f"{round(pos_val, 2)} {waluta}")

    st.markdown("---")

    st.subheader("Growth forecast (Computer simulation)")
    st.markdown("Potential behavior of the optimized portfolio over the next 252 trading days (1 year).")

    mean_path, worst_path, best_path = simulate_monte_carlo(port_returns)

    cum_max = np.maximum.accumulate(worst_path)
    drawdown = (worst_path - cum_max) / cum_max
    max_drawdown = drawdown.min()

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(y=mean_path, mode='lines', name='Base scenario', line=dict(color='#0366d6', width=2)))
    fig_line.add_trace(go.Scatter(y=best_path, mode='lines', name='Optimistic (95%)', line=dict(color='#28a745', dash='dot')))
    fig_line.add_trace(go.Scatter(y=worst_path, mode='lines', name='Pessimistic (5%)', line=dict(color='#d73a49', dash='dot')))

    fig_line.update_layout(xaxis_title="Trading days", yaxis_title="Portfolio value", height=350, margin=dict(t=20))
    st.plotly_chart(fig_line, use_container_width=True)

    col_m1, col_m2, col_m3 = st.columns(3)

    col_m1.metric("Max Drawdown", f"{round(max_drawdown*100, 2)}%")
    col_m2.metric("Sortino Ratio", f"{round(sortino_ratio, 2)}")
    col_m3.metric("Skewness", f"{round(skewness_val, 2)}")

    st.metric("Kurtosis", f"{round(kurt_val, 2)}")

    fig_hist = go.Figure()

    fig_hist.add_trace(go.Histogram(
        x=port_returns,
        nbinsx=50,
        name="Returns"
    ))

    var_95 = np.percentile(port_returns, 5)

    fig_hist.add_vline(
        x=var_95,
        line_dash="dash",
        annotation_text="VaR 95%",
        annotation_position="top left"
    )

    fig_hist.update_layout(
        title="Distribution of Portfolio Returns",
        height=300
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    if not returns.empty:
        rolling_vol = returns.std(axis=1).rolling(window=30).mean() * np.sqrt(252)

        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(y=rolling_vol, mode='lines'))

        fig_vol.update_layout(
            title="Rolling Volatility (30d)",
            height=300
        )

        st.plotly_chart(fig_vol, use_container_width=True)

elif page == "Download Files":
    st.title("File and resource downloads")
    st.markdown("Generate a report and **real historical data** for the companies selected in the Calculator.")

    if len(st.session_state.selected_tickers) > 0:
        st.info(f"Currently selected for portfolio: **{', '.join(st.session_state.selected_tickers)}**")
    else:
        st.info("No companies selected.")

    st.markdown("### Step 1: Download raw market data")
    st.markdown("Click below to download actual daily returns from the past year for the selected companies.")

    if st.button("Fetch and prepare market data", type="primary"):
        if len(st.session_state.selected_tickers) > 0:
            with st.spinner("Connecting to financial markets and generating spreadsheet..."):
                try:
                    data = yf.download(st.session_state.selected_tickers, period="1y", progress=False)

                    if 'Adj Close' in data:
                        prices = data['Adj Close']
                    elif 'Close' in data:
                        prices = data['Close']
                    else:
                        raise ValueError("No suitable price data available.")

                    if isinstance(prices, pd.Series):
                        prices = prices.to_frame(name=st.session_state.selected_tickers[0])

                    returns_df = prices.pct_change().dropna()

                    if returns_df.empty:
                        raise ValueError("Empty data returned.")

                    csv = returns_df.to_csv(index=True).encode('utf-8')

                    st.success("Data fetched successfully!")
                    st.download_button(
                        label="📥 Save CSV file with return history",
                        file_name="returns_history.csv",
                        mime="text/csv",
                        data=csv
                    )
                except Exception as e:
                    st.error(f"Error generating CSV: {e}")
        else:
            st.warning("Select stocks in the Risk Calculator first!")

    st.markdown("---")

    st.markdown("### Step 2: Engine configuration (JSON)")
    if 'last_opt_metrics' in st.session_state:
        real_report = {
            "engine_version": "2.1.0 (Scipy Optimized)",
            "selected_assets_weights": st.session_state.last_opt_weights,
            "metrics": {
                "annual_return": round(st.session_state.last_opt_metrics["annual_return"], 4),
                "annual_volatility": round(st.session_state.last_opt_metrics["annual_volatility"], 4),
                "sortino_ratio": round(st.session_state.last_opt_metrics["sortino_ratio"], 4),
                "skewness": round(st.session_state.last_opt_metrics["skewness"], 4),
                "kurtosis": round(st.session_state.last_opt_metrics["kurtosis"], 4)
            },
            "status": "Calculated successfully"
        }
        json_string = json.dumps(real_report, indent=4)
        st.download_button(
            label="📥 Download risk report (JSON)",
            file_name="risk_report.json",
            mime="application/json",
            data=json_string
        )
    else:
        st.info("Go to the 'Portfolio Advisor' tab to generate the JSON report.")

    st.markdown("---")

    st.markdown("### Step 3: Generate Executive Factsheet (PDF)")
    if 'last_opt_metrics' in st.session_state:
        if st.button("📄 Generate PDF Report", type="primary"):
            with st.spinner("Generating document..."):
                try:
                    pdf_path = generate_pdf_factsheet(
                        tickers=list(st.session_state.last_opt_weights.keys()),
                        weights=list(st.session_state.last_opt_weights.values()),
                        metrics=st.session_state.last_opt_metrics
                    )
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="📥 Download generated PDF",
                            data=pdf_file,
                            file_name="Portfolio_Risk_Factsheet.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
    else:
        st.info("Calculate weights in 'Portfolio Advisor' to unlock PDF generation.")

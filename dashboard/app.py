import streamlit as st
import requests
import textwrap

# --- 1. KONFIGURACJA I STYLIZACJA ---
st.set_page_config(page_title="Quant Risk Engine", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
    
    .stApp { background-color: white; color: #1e293b; font-family: 'Open Sans', sans-serif; }
    
    /* Nagłówek */
    .header-title { font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 5px; }
    .header-subtitle { font-size: 14px; color: #64748b; margin-bottom: 25px; }
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; color: white; margin-left: 10px; vertical-align: middle; }
    .badge-v { background-color: #10b981; }
    .badge-oas { background-color: #3b82f6; }

    /* Rozwijane panele (Expanders) */
    [data-testid="stExpander"] details {
        border: 1px solid #bfdbfe !important;
        border-radius: 6px !important;
        margin-bottom: 12px !important;
        background-color: white;
        box-shadow: none !important;
    }
    [data-testid="stExpander"] details summary {
        background-color: #eff6ff !important;
        padding: 12px 15px !important;
        border-radius: 6px !important;
        color: #1e3a8a !important;
    }
    [data-testid="stExpander"] details summary p {
        font-family: 'Open Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        margin: 0 !important;
    }
    [data-testid="stExpander"] details summary:hover {
        background-color: #e0f2fe !important;
    }
    [data-testid="stExpander"] details > div {
        padding: 20px !important;
        border-top: 1px solid #bfdbfe !important;
    }

    /* Formularz i przyciski */
    div[data-baseweb="select"] > div { background-color: #f8fafc !important; border-radius: 6px; border: 1px solid #cbd5e1; }
    button[kind="primary"] { background-color: #3b82f6 !important; border-color: #3b82f6 !important; color: white !important; border-radius: 6px; font-weight: 600; }
    button[kind="secondary"] { background-color: white !important; border: 1px solid #cbd5e1 !important; color: #475569 !important; border-radius: 6px; font-weight: 600; }

    /* Jasnoniebieskie Tagi Spółek */
    span[data-baseweb="tag"] { background-color: #bfdbfe !important; color: #1e3a8a !important; border-radius: 4px; }
    span[data-baseweb="tag"] svg { fill: #1e3a8a !important; }

    /* Ciemny panel wyników */
    .result-panel { background-color: #0f172a; color: #f8fafc; padding: 25px; border-radius: 8px; margin-top: 20px; font-family: 'Open Sans', sans-serif; }
    .result-header { font-size: 18px; font-weight: 700; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; }
    .status-200 { color: #10b981; font-size: 14px; font-family: monospace; background: #064e3b; padding: 2px 8px; border-radius: 4px; }
    
    .grid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; }
    .data-card { background-color: #1e293b; padding: 15px; border-radius: 6px; border: 1px solid #334155; }
    .data-card h4 { margin-top: 0; color: #3b82f6; font-size: 15px; margin-bottom: 15px; font-weight: 600; }
    
    .data-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #334155; font-size: 14px; }
    .data-row:last-child { border-bottom: none; }
    .data-label { color: #94a3b8; }
    .data-val { font-family: monospace; font-weight: 600; color: #e2e8f0; }
    
    .risk-ok { color: #10b981; }
    .risk-warn { color: #f59e0b; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BAZA TICKERÓW ---
POPULAR_TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", 
    "WMT", "JNJ", "BAC", "PG", "XOM", "DIS", "CSCO", "ADBE", "CRM", "AMD"
]

# --- 3. NAGŁÓWEK ---
st.markdown("""
    <div class="header-title">
        Quant Risk Management Engine 
        <span class="badge badge-v">v2.0</span>
        <span class="badge badge-oas">OAS 3.1</span>
    </div>
    <div class="header-subtitle">Enterprise-grade API for stochastic simulations and portfolio risk analytics.</div>
""", unsafe_allow_html=True)


# =====================================================================
# ENDPOINT 1: KALKULATOR RYZYKA 
# =====================================================================
with st.expander("/RiskCal  —  Calculate comprehensive portfolio risk metrics", expanded=True):
    
    st.markdown("<div style='font-weight: 600; font-size: 15px; color: #1e293b; margin-bottom: 15px;'>Request Parameters</div>", unsafe_allow_html=True)

    col_input, col_help = st.columns([3, 2])
    with col_input:
        tickers_input = st.multiselect("Asset Tickers", options=POPULAR_TICKERS, default=["TSLA", "MSFT"])

    with col_help:
        st.markdown("<div style='margin-top: 28px; color: #64748b; font-size: 13px;'>Select target assets to include in the portfolio.<br><i>Type to search (e.g., AAPL, TSLA)</i></div>", unsafe_allow_html=True)

    st.write("") 
    col_exec, col_clear = st.columns([8, 2])
    with col_exec:
        execute_btn = st.button("Execute Request", type="primary", use_container_width=True)
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.rerun()

    if execute_btn:
        tickers_list = tickers_input
        if not tickers_list:
            st.warning("Please select at least one ticker.")
        else:
            with st.spinner("Connecting to Quant Engine..."):
                is_mock = False
                try:
                    res = requests.get("http://127.0.0.1:8000/v1/portfolio/risk", params={"tickers": tickers_list}, timeout=3)
                    res.raise_for_status()
                    data = res.json()
                except requests.exceptions.ConnectionError:
                    is_mock = True
                    data = {
                        "risk_metrics": {
                            "volatility": "18.45%",
                            "parametric": {"var": "-2.14%", "es": "-3.01%"},
                            "historical": {"var": "-2.20%", "es": "-3.15%"},
                            "monte_carlo": {"var": "-2.18%", "es": "-3.10%"}
                        },
                        "backtest": {
                            "violations": 12, "violation_ratio": "4.8%", 
                            "kupiec_p": "0.842", "christ_p": "0.615", "status": "PASS"
                        }
                    }
                except Exception as e:
                    st.error(f"Engine failed: {e}")
                    st.stop()

                metrics = data.get("risk_metrics", {})
                param = metrics.get("parametric", {})
                hist = metrics.get("historical", {})
                mc = metrics.get("monte_carlo", {})
                backtest = data.get("backtest", {})
                
                mock_warning = "<span style='color: #f59e0b; font-size: 12px; margin-left: 10px;'>[MOCK DATA - SERVER OFFLINE]</span>" if is_mock else ""
                analyzed_str = ", ".join(tickers_list)

                html_response = textwrap.dedent(f"""
                <div class="result-panel">
                    <div class="result-header">
                        <span>Portfolio Analysis Report {mock_warning}</span>
                        <span class="status-200">HTTP 200 OK</span>
                    </div>
                    <div style="color: #94a3b8; font-size: 14px; margin-bottom: 20px;">
                        Analyzed Assets: <span style="color: white; font-weight: bold;">{analyzed_str}</span> &nbsp;|&nbsp; 
                        Annualized Volatility: <span style="color: white; font-weight: bold;">{metrics.get('volatility', 'N/A')}</span>
                    </div>
                    <div class="grid-container">
                        <div class="data-card">
                            <h4>Value at Risk (VaR) & Expected Shortfall</h4>
                            <div class="data-row"><span class="data-label">Parametric VaR:</span><span class="data-val">{param.get('var', 'N/A')}</span></div>
                            <div class="data-row"><span class="data-label">Parametric ES:</span><span class="data-val">{param.get('es', 'N/A')}</span></div>
                            <div class="data-row" style="margin-top: 10px;"><span class="data-label">Historical VaR:</span><span class="data-val">{hist.get('var', 'N/A')}</span></div>
                            <div class="data-row"><span class="data-label">Historical ES:</span><span class="data-val">{hist.get('es', 'N/A')}</span></div>
                            <div class="data-row" style="margin-top: 10px;"><span class="data-label">Monte Carlo VaR:</span><span class="data-val risk-warn">{mc.get('var', 'N/A')}</span></div>
                        </div>
                        <div class="data-card">
                            <h4>Backtest Validation Model</h4>
                            <div class="data-row"><span class="data-label">Violations Count:</span><span class="data-val">{backtest.get('violations', 'N/A')}</span></div>
                            <div class="data-row"><span class="data-label">Violation Ratio:</span><span class="data-val">{backtest.get('violation_ratio', 'N/A')}</span></div>
                            <div class="data-row" style="margin-top: 10px;"><span class="data-label">Kupiec POF p-value:</span><span class="data-val">{backtest.get('kupiec_p', 'N/A')}</span></div>
                            <div class="data-row"><span class="data-label">Christoffersen p-value:</span><span class="data-val">{backtest.get('christ_p', 'N/A')}</span></div>
                            <div class="data-row" style="margin-top: 15px; background: rgba(16, 185, 129, 0.1); padding: 8px; border-radius: 4px; border: 1px solid #065f46;">
                                <span class="data-label" style="color: #e2e8f0; font-weight: 600;">Backtest Status:</span>
                                <span class="data-val risk-ok">{backtest.get('status', 'N/A')}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """)
                st.markdown(html_response, unsafe_allow_html=True)
                
                if is_mock:
                    st.toast("Backend offline. Displaying mock data.")


# =====================================================================
# ENDPOINT 2: ARCHITEKTURA KODU
# =====================================================================
with st.expander("/RiskCal/architecture  —  API Source Code & System Architecture"):
    st.markdown("""
    ### System Architecture
    Ten silnik ryzyka został zaprojektowany z myślą o maksymalnej wydajności (High-Frequency Trading & Risk Analysis).
    
    * **Backend Framework:** Zbudowany w oparciu o **FastAPI**, co gwarantuje w pełni asynchroniczną (ASGI) obsługę tysięcy zapytań na sekundę.
    * **Server:** Aplikacja serwowana jest przez **Uvicorn**, błyskawiczny serwer WWW dla Pythona.
    * **Data Processing:** Operacje na macierzach i transformacje szeregów czasowych obsługiwane są przez wektoryzowane funkcje bibliotek `NumPy` oraz `Pandas`.
    * **Simulation Engine:** Autorski silnik Monte Carlo, który generuje stochastyczne ścieżki cenowe z użyciem wielowątkowości, omijając wąskie gardła standardowego Pythona.
    """)

# =====================================================================
# ENDPOINT 3: METODOLOGIA MATEMATYCZNA
# =====================================================================
with st.expander("/RiskCal/math_models  —  Mathematical Operations & Formulas"):
    st.markdown("""
    ### Modele Ryzyka i Metodologia
    
    Silnik wylicza metryki ryzyka w oparciu o trzy niezależne podejścia probabilistyczne, stosowane powszechnie w bankowości inwestycyjnej.
    
    #### 1. Value at Risk (VaR)
    Value at Risk określa maksymalną potencjalną stratę portfela w zadanym horyzoncie czasowym, przy określonym poziomie ufności (np. 95%).
    """)
    
    st.markdown("- **Parametric VaR (Wariancja-Kowariancja):** Zakłada, że stopy zwrotu mają rozkład normalny.")
    st.latex(r"VaR_{parametric} = \mu - Z_{\alpha} \cdot \sigma")
    
    st.markdown("- **Historical VaR:** Metoda empiryczna. Sortuje historyczne stopy zwrotu i odcina najgorszy $\alpha$-ty percentyl z wektora zwrotów $R$.")
    st.latex(r"VaR_{historical} = Percentile(R, 1 - \alpha)")

    st.markdown("""
    #### 2. Expected Shortfall (ES)
    Nazywany również *Conditional VaR* (CVaR). Odpowiada na pytanie: "Jeśli strata przekroczy barierę VaR, jak duża średnio ona będzie?". Jest to koherentna miara ryzyka ogona dystrybucji.
    """)
    st.latex(r"ES_{\alpha} = \mathbb{E}[R \mid R < -VaR_{\alpha}]")

    st.markdown("""
    #### 3. Monte Carlo Simulations (GBM)
    Silnik symuluje dziesiątki tysięcy losowych ścieżek cenowych z wykorzystaniem stochastycznego modelu Geometrycznego Ruchu Browna (Geometric Brownian Motion).
    """)
    st.latex(r"S_t = S_0 \exp\left( (\mu - \frac{\sigma^2}{2})t + \sigma W_t \right)")
    st.markdown("*(Gdzie $W_t$ to proces Wienera reprezentujący losowy szok rynkowy).*")

    st.markdown("""
    #### 4. Backtesting (Kupiec POF Test)
    Aby udowodnić kalibrację modeli, silnik wykonuje historyczny Backtest. Test Kupca (Proportion of Failures) weryfikuje za pomocą statystyki opartej na rozkładzie dwumianowym, czy liczba przekroczeń (violations) VaR na danych historycznych zgadza się z teoretycznym poziomem ufności modelu.
    """)
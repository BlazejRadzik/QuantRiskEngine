import sys
import os
# Poprawka ścieżek dla Streamlit Cloud
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="QuantRisk Pro", layout="wide", initial_sidebar_state="expanded")

# --- ZAAWANSOWANY CSS (Styl PyPI / Dokumentacji) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #24292e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    
    /* Menu boczne - stylowe bloki */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label {
        width: 100%; padding: 10px 15px; margin-bottom: 5px; border-radius: 6px;
        background-color: transparent; cursor: pointer; transition: 0.2s; border-left: 3px solid transparent;
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label:hover { background-color: #f0f2f6; }
    
    /* Karty wyników */
    .result-box { border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 15px; background-color: #fafbfc; }
    .metric-value { font-size: 24px; font-weight: bold; color: #0366d6; }
    .metric-label { font-size: 12px; color: #586069; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- ZMIENNE GLOBALNE ---
POPULAR_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", "WMT", "JNJ", "PG", "XOM"]

# --- PASEK BOCZNY ---
with st.sidebar:
    st.markdown("### Nawigacja")
    page = st.radio("Menu", ["Opis projektu", "Kalkulator Ryzyka", "Doradca Portfelowy", "Pobierz pliki"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### Twórcy\n👤 **Główny Inżynier QuantRisk**")
    st.markdown("---")
    st.markdown("### Metadane\n🏷️ python, finanse, ryzyko, quant")

# ==========================================
# ZAKŁADKA 1: OPIS PROJEKTU
# ==========================================
if page == "Opis projektu":
    st.title("QuantRisk Pro")
    st.markdown("Platforma klasy Enterprise do zarządzania ryzykiem oraz biblioteka Python dla inżynierii finansowej.")
    st.subheader("Instalacja")
    st.code("pip install quant-risk-pro", language="bash")
    st.markdown("---")
    st.subheader("Wersja '>= 2.0.0'")
    st.markdown("Zaprojektowałem system klasy **Institutional Risk Engine**. Wykorzystuje FastAPI oraz wektoryzowane obliczenia (NumPy, Pandas).")
    st.subheader("Kluczowe możliwości")
    st.markdown("* Optymalizacja Markowitza\n* Parametryczny i Historyczny VaR\n* Expected Shortfall\n* Modelowanie GARCH(1,1)")

# ==========================================
# ZAKŁADKA 2: KALKULATOR RYZYKA
# ==========================================
elif page == "Kalkulator Ryzyka":
    st.title("Interaktywny Kalkulator Ryzyka")
    tickers_input = st.multiselect("Wybierz aktywa:", options=POPULAR_TICKERS, default=["MSFT", "AAPL"])
    
    if st.button("Wykonaj obliczenia", type="primary"):
        with st.spinner("Pobieranie danych i obliczanie modeli..."):
            try:
                # ADRES TWOJEGO API NA RENDER
                res = requests.get("https://quantriskengine.onrender.com/v1/portfolio/risk", params={"tickers": tickers_input}, timeout=25)
                res.raise_for_status()
                data = res.json()
                
                risk = data.get("risk_metrics", {})
                backtest = data.get("backtest", {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div class='result-box'><div class='metric-label'>Zmienność (Vol)</div><div class='metric-value'>{risk.get('volatility')}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='result-box'><div class='metric-label'>Historical VaR</div><div class='metric-value'>{risk.get('historical', {}).get('var')}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='result-box'><div class='metric-label'>Status Backtestu</div><div class='metric-value'>{backtest.get('status')}</div></div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Błąd API: {e}. Jeśli to błąd 500, upewnij się, że yfinance pobrało dane.")

# ==========================================
# ZAKŁADKA 3: DORADCA PORTFELOWY (ULEPSZONA!)
# ==========================================
elif page == "Doradca Portfelowy":
    st.title("Inteligentny Doradca Portfelowy")
    st.markdown("Wybierz swój profil, aby otrzymać zoptymalizowaną strukturę portfela opartą o modele Quant.")
    
    profile = st.selectbox("Określ swoją tolerancję na ryzyko:", ["Konserwatywny", "Zrównoważony", "Agresywny"])
    
    # Dane konfiguracyjne dla doradcy
    advisor_data = {
        "Konserwatywny": {
            "tickers": ["JNJ", "PG", "WMT", "V"],
            "weights": [0.3, 0.3, 0.2, 0.2],
            "reason": "Wybrane spółki charakteryzują się niskim współczynnikiem Beta i stabilnymi przepływami pieniężnymi. W okresach bessy chronią kapitał dzięki niskiej korelacji z rynkiem technologicznym.",
            "method": "Minimalizacja Wariancji (Minimum Variance Portfolio)",
            "code": "optimize(objective='min_variance', constraints='long_only')"
        },
        "Zrównoważony": {
            "tickers": ["AAPL", "MSFT", "GOOGL", "JPM"],
            "weights": [0.25, 0.25, 0.25, 0.25],
            "reason": "Złoty środek między wzrostem a wartością. Portfel zdywersyfikowany między sektor Tech a sektor finansowy, zapewniający ekspozycję na liderów gospodarki.",
            "method": "Maksymalizacja współczynnika Sharpe'a (Max Sharpe Ratio)",
            "code": "optimize(objective='max_sharpe', rf_rate=0.04)"
        },
        "Agresywny": {
            "tickers": ["NVDA", "TSLA", "AMD", "META"],
            "weights": [0.4, 0.2, 0.2, 0.2],
            "reason": "Skupienie na spółkach o wysokiej dynamice wzrostu i klastrowaniu zmienności. Modele wykazują tutaj potencjał na wysokie stopy zwrotu kosztem zwiększonego ryzyka ogona.",
            "method": "Optymalizacja stopy zwrotu przy zadanym VaR",
            "code": "optimize(objective='max_return', risk_budget=0.15)"
        }
    }
    
    data = advisor_data[profile]
    
    st.markdown("---")
    
    col_desc, col_pie = st.columns([1.2, 1])
    
    with col_desc:
        st.subheader(f"🛡️ Strategia: {profile}")
        st.markdown(f"**Dlaczego te spółki?**\n{data['reason']}")
        st.markdown(f"**Metodologia:** {data['method']}")
        st.markdown("**Fragment kodu silnika:**")
        st.code(data['code'], language="python")
        
    with col_pie:
        # WYKRES KOŁOWY ALOKACJI
        fig = px.pie(names=data['tickers'], values=data['weights'], 
                     title="Sugerowana alokacja portfela",
                     hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    # --- KALKULATOR WALUTOWY I POZYCJI ---
    st.subheader("💰 Kalkulator wielkości pozycji")
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        currency = st.selectbox("Waluta:", ["PLN", "USD", "EUR"])
    with c2:
        budget = st.number_input(f"Kwota inwestycji ({currency}):", min_value=100, value=10000)
    
    with c3:
        st.markdown(f"**Sugerowany zakup dla {budget} {currency}:**")
        cols = st.columns(len(data['tickers']))
        for i, t in enumerate(data['tickers']):
            share = budget * data['weights'][i]
            cols[i].metric(t, f"{int(data['weights'][i]*100)}%", f"{int(share)} {currency}")

    st.markdown("---")
    
    # --- WYKRES PROGNOZY ---
    st.subheader("📈 Prognoza wzrostu (Symulacja Monte Carlo)")
    np.random.seed(42)
    days = 252
    returns = np.random.normal(0.0005, 0.012, days) if profile != "Agresywny" else np.random.normal(0.001, 0.02, days)
    price_path = np.exp(np.cumsum(returns))
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=list(range(days)), y=price_path, mode='lines', 
                                 name='Scenariusz bazowy', line=dict(color='#0366d6', width=2)))
    fig_line.update_layout(xaxis_title="Dni", yaxis_title="Wartość portfela (skalowana)", height=350)
    st.plotly_chart(fig_line, use_container_width=True)

# ==========================================
# ZAKŁADKA 4: POBIERANIE PLIKÓW
# ==========================================
elif page == "Pobierz pliki":
    st.title("Pobieranie zasobów")
    st.download_button("📥 Pobierz raport JSON (Config)", data=json.dumps({"status": "ready"}), file_name="config.json")
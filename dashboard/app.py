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

# --- INICJALIZACJA STANU SESJI ---
if 'selected_profile_tickers' not in st.session_state:
    st.session_state['selected_profile_tickers'] = ["MSFT", "AAPL"]
if 'active_page' not in st.session_state:
    st.session_state['active_page'] = "Opis projektu"

def set_page():
    st.session_state['active_page'] = st.session_state['nav_radio']

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="QuantRisk Pro", layout="wide", initial_sidebar_state="expanded")

# --- ZAAWANSOWANY CSS ---
st.markdown("""
    <style>
    /* TYTUŁY NIŻEJ */
    .block-container { padding-top: 4rem !important; }

    .stApp { background-color: #ffffff; color: #24292e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    
    /* MENU BOCZNE - STYL PyPI */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label {
        width: 100%; padding: 10px 15px; margin-bottom: 5px; border-radius: 6px;
        background-color: transparent; cursor: pointer; transition: 0.2s ease; border-left: 3px solid transparent;
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label:hover { background-color: #f0f2f6; }
    [data-testid="stRadio"] div[role="radiogroup"] > label[data-selected="true"] {
        background-color: #f0f2f6; border-left: 3px solid #0366d6; font-weight: 600;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* WYNIKI KALKULATORA */
    .result-box { border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 10px; background-color: #fafbfc; min-width: 250px; }
    .metric-value { font-size: 26px; font-weight: bold; }
    .metric-label { font-size: 11px; color: #586069; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    .metric-description { font-size: 14px; color: #24292e; line-height: 1.5; padding-left: 20px; padding-top: 5px; }
    
    /* STATUSY KOLORÓW */
    .status-git { color: #28a745; font-weight: bold; }
    .status-alarm { color: #d73a49; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- POMOCNIK: RENDEROWANIE PROSTOKĄTA Z LOGIKĄ KOLORÓW ---
def render_metric_row(label, value_str, limit, desc_text):
    # Logika: jeśli wynik < limit, to jest Dobrze (Zielony)
    try:
        val_num = float(value_str.replace('%', ''))
        is_good = val_num < limit
        color = "#28a745" if is_good else "#d73a49"
        status_label = "<span class='status-git'>Git</span>" if is_good else "<span class='status-alarm'>Dużo</span>"
    except:
        color = "#24292e"
        status_label = ""

    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div class='result-box'>
            <div class='metric-label'>{label}</div>
            <div class='metric-value' style="color: {color};">{value_str}</div>
        </div>
        <div class='metric-description'>
            {desc_text.replace('{status}', status_label)}<br>
            Cel: poniżej <b>{limit}%</b>. Twoja sytuacja: {status_label}.
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- NAWIGACJA ---
POPULAR_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", "WMT", "JNJ", "PG", "XOM"]
pages_list = ["Opis projektu", "Kalkulator Ryzyka", "Doradca Portfelowy", "Pobierz pliki"]

with st.sidebar:
    st.markdown("### Nawigacja")
    page = st.radio("Menu", pages_list, key="nav_radio", 
                    index=pages_list.index(st.session_state['active_page']), 
                    on_change=set_page, label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### Twórcy\n👤 **Główny Inżynier QuantRisk**")
    st.markdown("---")
    st.markdown("### Metadane\n🏷️ python, finanse, ryzyko, quant")

# ==========================================
# ZAKŁADKA 1: OPIS PROJEKTU
# ==========================================
if st.session_state['active_page'] == "Opis projektu":
    st.title("QuantRisk Pro")
    st.markdown("Platforma klasy Enterprise do zarządzania ryzykiem oraz biblioteka Python.")
    st.subheader("Instalacja")
    st.code("pip install quant-risk-pro", language="bash")
    st.markdown("---")
    st.subheader("Wersja '>= 2.0.0'")
    st.markdown("Zaprojektowałem system klasy **Institutional Risk Engine**. Wykorzystuje FastAPI oraz wektoryzowane obliczenia (NumPy, Pandas).")
    st.subheader("Kluczowe możliwości")
    st.markdown("""
    * Optymalizacja portfela metodą Markowitza.
    * Parametryczny i Historyczny VaR (95%).
    * Expected Shortfall (CVaR).
    * Modelowanie zmienności procesem **GARCH(1,1)**.
    """)

# ==========================================
# ZAKŁADKA 2: KALKULATOR RYZYKA (6 PROSTOKĄTÓW)
# ==========================================
elif st.session_state['active_page'] == "Kalkulator Ryzyka":
    st.title("Interaktywny Kalkulator Ryzyka")
    tickers_input = st.multiselect("Wybierz aktywa:", options=POPULAR_TICKERS, default=st.session_state['selected_profile_tickers'])
    
    if st.button("Wykonaj obliczenia", type="primary"):
        with st.spinner("Pobieranie danych i obliczanie modeli..."):
            try:
                res = requests.get("https://quantriskengine.onrender.com/v1/portfolio/risk", params={"tickers": tickers_input}, timeout=25)
                res.raise_for_status()
                data = res.json()
                risk = data.get("risk_metrics", {})
                backtest = data.get("backtest", {})

                st.markdown("### Raport Ryzyka i Optymalizacji (Pełna analiza)")
                
                # 1. Roczna zmienność
                render_metric_row("Roczna Zmienność (Volatility)", risk.get('volatility', '0%'), 2.0, 
                    "Określa stabilność portfela. Wynik {val} oznacza, że jest {status}.")
                
                # 2. Parametryczny VaR
                render_metric_row("Parametryczny VaR (95%)", risk.get('parametric', {}).get('var', '0%'), 3.0, 
                    "Maksymalna oczekiwana strata dzienna w normalnych warunkach. Wynik {val} to {status}.")
                
                # 3. Historyczny VaR
                render_metric_row("Historyczny VaR (95%)", risk.get('historical', {}).get('var', '0%'), 3.0, 
                    "Ryzyko wyliczone na bazie realnych spadków z przeszłości. Wynik {val} to {status}.")
                
                # 4. Expected Shortfall (CVaR)
                render_metric_row("Expected Shortfall (CVaR)", risk.get('historical', {}).get('es', '0%'), 5.0, 
                    "Średnia strata w najgorszych 5% przypadków (podczas krachu). Wynik {val} to {status}.")

                # 5. Monte Carlo VaR
                render_metric_row("Monte Carlo VaR", risk.get('monte_carlo', {}).get('var', '0%'), 3.0, 
                    "Symulacja tysięcy scenariuszy rynkowych. Wynik {val} to {status}.")

                # 6. Status Walidacji
                b_status = backtest.get('status', 'N/A')
                b_color = "#28a745" if b_status == "PASS" else "#d73a49"
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div class='result-box' style="border-left: 5px solid {b_color};">
                        <div class='metric-label'>Status Walidacji (Test Kupca)</div>
                        <div class='metric-value' style="color: {b_color};">{b_status}</div>
                    </div>
                    <div class='metric-description'>
                        Model jest <b>{"Wiarygodny" if b_status == "PASS" else "Mało precyzyjny"}</b>.<br>
                        Liczba przekroczeń VaR w teście: {backtest.get('violations')}. Chcemy wynik PASS.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Błąd API: {e}")

# ==========================================
# ZAKŁADKA 3: DORADCA PORTFELOWY (PRZYWRÓCONE DASHBOARDY)
# ==========================================
elif st.session_state['active_page'] == "Doradca Portfelowy":
    st.title("Inteligentny Doradca Portfelowy")
    profile = st.selectbox("Wybierz profil ryzyka:", ["Konserwatywny", "Zrównoważony", "Agresywny"])
    
    st.markdown("---")
    
    # DANE DLA DORADCY
    advisor_config = {
        "Konserwatywny": {
            "tickers": ['JNJ', 'PG', 'WMT', 'JPM', 'V'],
            "weights": [0.25, 0.25, 0.20, 0.15, 0.15],
            "desc": "🛡️ Wybór defensywny. Minimalizacja wariancji brzegowej.",
            "logic": "optimize(min_variance)",
            "drift": 0.0003
        },
        "Zrównoważony": {
            "tickers": ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
            "weights": [0.3, 0.3, 0.2, 0.2],
            "desc": "⚖️ Złoty środek. Maksymalizacja Sharpe Ratio.",
            "logic": "optimize(max_sharpe)",
            "drift": 0.0006
        },
        "Agresywny": {
            "tickers": ['NVDA', 'TSLA', 'AMD', 'META', 'NFLX'],
            "weights": [0.35, 0.25, 0.15, 0.15, 0.10],
            "desc": "🚀 Wysoki wzrost. Model GARCH(1,1) pod zmienność.",
            "logic": "optimize(risk_parity)",
            "drift": 0.0012
        }
    }
    
    conf = advisor_config[profile]
    
    # DASHBOARD 1: ALOKACJA (PIE CHART)
    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.subheader(f"Strategia: {profile}")
        st.markdown(f"**Dlaczego te spółki?** {conf['desc']}")
        st.info(f"**Metodologia:** {conf['logic']}")
        st.markdown("**Fragment kodu optymalizatora:**")
        st.code(f"weights = {conf['logic']}", language="python")
        
        if st.button(f"🔎 Przeanalizuj strategię {profile} w Kalkulatorze", type="primary"):
            st.session_state['selected_profile_tickers'] = conf['tickers']
            st.session_state['active_page'] = "Kalkulator Ryzyka"
            st.rerun()

    with col_right:
        fig_pie = px.pie(names=conf['tickers'], values=conf['weights'], hole=0.4, title="Sugerowana Alokacja")
        fig_pie.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    
    # DASHBOARD 2: KALKULATOR ZAKUPÓW
    st.subheader("💰 Kalkulator wielkości pozycji")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: cur = st.selectbox("Waluta:", ["PLN", "USD", "EUR"])
    with c2: amt = st.number_input(f"Kwota inwestycji ({cur}):", min_value=1000, value=10000)
    with c3:
        st.markdown(f"**Podział dla Twojego budżetu:**")
        cols = st.columns(len(conf['tickers']))
        for i, t in enumerate(conf['tickers']):
            cols[i].metric(t, f"{int(conf['weights'][i]*100)}%", f"{int(amt * conf['weights'][i])} {cur}")

    st.markdown("---")

    # DASHBOARD 3: MONTE CARLO
    st.subheader("📈 Prognoza wzrostu (Model Monte Carlo)")
    days = 252
    returns = np.random.normal(conf['drift'], 0.012, days)
    path = np.exp(np.cumsum(returns))
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=list(range(days)), y=path, mode='lines', name='Prognozowany trend', line=dict(color='#0366d6', width=2)))
    fig_line.update_layout(height=350, xaxis_title="Dni", yaxis_title="Wartość portfela (skalowana)")
    st.plotly_chart(fig_line, use_container_width=True)

# ==========================================
# ZAKŁADKA 4: POBIERANIE PLIKÓW
# ==========================================
elif st.session_state['active_page'] == "Pobierz pliki":
    st.title("Pobieranie plików")
    st.download_button("📥 Pobierz raport JSON", data=json.dumps({"status": "ready"}), file_name="report.json")
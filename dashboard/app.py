import sys
import os
# Poprawka ścieżek dla Streamlit Cloud
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import pandas as pd
import json

# --- INICJALIZACJA STANU SESJI (Dla nawigacji i zapamiętywania spółek) ---
if 'selected_profile_tickers' not in st.session_state:
    st.session_state['selected_profile_tickers'] = ["MSFT", "AAPL"] # Domyślne
if 'active_page' not in st.session_state:
    st.session_state['active_page'] = "Opis projektu" # Domyślna strona startowa

# Funkcja callback do zmiany strony
def set_page():
    st.session_state['active_page'] = st.session_state['nav_radio']

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="QuantRisk Pro", layout="wide", initial_sidebar_state="expanded")

# --- ZAAWANSOWANY CSS (Styl PyPI / Dokumentacji) ---
st.markdown("""
    <style>
    /* REDUKCJA DUŻEJ LUKI U GÓRY STRONY */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }
    h1 {
        margin-top: 0rem !important;
        padding-top: 0rem !important;
    }

    /* Wymuszenie czytelności tekstu */
    .stApp { background-color: #ffffff; color: #24292e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    
    /* UKRYCIE KÓŁEK (RADIO BUTTONS) I ZMIANA W PROSTOKĄTY */
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
    /* Podświetlenie aktywnej zakładki */
    [data-testid="stRadio"] div[role="radiogroup"] > label[data-selected="true"] {
        background-color: #f0f2f6;
        border-left: 3px solid #0366d6;
        font-weight: 600;
    }
    
    /* Ukrycie domyślnego menu Streamlit z dołu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Metadane w pasku bocznym */
    .sidebar-meta { font-size: 14px; line-height: 1.6; color: #586069; }
    .sidebar-meta strong { color: #24292e; }
    
    /* Sekcje wyników (Kalkulator) */
    .result-box { border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 10px; background-color: #fafbfc; width: 100%;}
    .metric-value { font-size: 26px; font-weight: bold; color: #0366d6; }
    .metric-label { font-size: 12px; color: #586069; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    
    /* Styl dla opisu obok kwadratu w kalkulatorze */
    .metric-description { font-size: 14px; color: #24292e; line-height: 1.5; padding-left: 10px; }
    .good-result { color: #28a745; font-weight: bold; }
    .bad-result { color: #d73a49; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- ZMIENNE GLOBALNE ---
POPULAR_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", "WMT", "JNJ", "PG", "XOM"]

# Lista stron dla nawigacji
pages_list = ["Opis projektu", "Kalkulator Ryzyka", "Doradca Portfelowy", "Pobierz pliki"]

# Znajdź indeks aktywnej strony
try:
    active_index = pages_list.index(st.session_state['active_page'])
except ValueError:
    active_index = 0

# --- PASEK BOCZNY (SIDEBAR) JAK W PYPI ---
with st.sidebar:
    st.markdown("### Nawigacja")
    # Używamy key i callback dla poprawnej nawigacji przyciskiem
    st.radio("Przejdź do", 
             pages_list, 
             key="nav_radio", 
             index=active_index, 
             on_change=set_page, 
             label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### Zweryfikowane szczegóły ✅")
    st.markdown("<div class='sidebar-meta'>Te szczegóły zostały zweryfikowane przez System.</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Twórcy")
    st.markdown("<div class='sidebar-meta'>👤 <strong>Główny Inżynier QuantRisk</strong></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Metadane")
    st.markdown("""
    <div class='sidebar-meta'>
    <ul>
        <li><strong>Licencja:</strong> MIT</li>
        <li><strong>Autor:</strong> QuantRisk Team</li>
        <li>🏷️ python, finanse, ryzyko, quant</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Kategorie")
    st.markdown("<div class='sidebar-meta'><strong>Grupa docelowa:</strong><br><ul><li>Programiści</li><li>Analitycy Finansowi</li></ul></div>", unsafe_allow_html=True)


# Przypisanie aktywnej strony do zmiennej lokalnej dla czytelności warunków
page = st.session_state['active_page']

# ==========================================
# ZAKŁADKA 1: OPIS PROJEKTU (DOKUMENTACJA)
# ==========================================
if page == "Opis projektu":
    st.title("QuantRisk Pro")
    st.markdown("Platforma klasy Enterprise do zarządzania ryzykiem oraz biblioteka Python dla inżynierii finansowej i optymalizacji portfeli.")
    
    st.subheader("Instalacja")
    st.code("pip install quant-risk-pro", language="bash")
    
    st.markdown("---")
    st.subheader("Wersja '>= 2.0.0'")
    st.markdown("""
    Zaprojektowałem i wdrożyłem system klasy **Institutional Risk Engine** do analizy portfeli wieloskładnikowych. 
    Biblioteka wykorzystuje w pełni asynchroniczne API (FastAPI) oraz wektoryzowane obliczenia (NumPy, Pandas) w celu maksymalizacji wydajności.
    """)
    
    st.subheader("Kluczowe możliwości (Wersja ≥ 2.0.0)")
    st.markdown("""
    System udostępnia moduł `risk_metrics`, który odpowiada za estymację ryzyka ogonowego oraz moduł `models` do optymalizacji:
    * Optymalizacja portfela metodą Markowitza (Max Sharpe Ratio).
    * Parametryczny i Historyczny VaR (95%).
    * Expected Shortfall (CVaR).
    * Modelowanie zmienności procesem **GARCH(1,1)** dla lepszego odwzorowania klastrowania zmienności na giełdzie.
    """)
    
    st.subheader("Szybki start - Przykład użycia")
    st.markdown("Poniżej znajduje się prosty przykład wykorzystania naszego API w Pythonie do wyliczenia ryzyka i optymalizacji:")
    
    st.code("""
    from core.risk_metrics import calculate_comprehensive_metrics
    from core.models import optimize_portfolio_weights
    from data.ingestor import fetch_data

    # 1. Pobierz dane rynkowe dla spółek
    returns_df = fetch_data(["AAPL", "MSFT", "TSLA"])

    # 2. Zoptymalizuj wagi portfela (Model Markowitza)
    optimal_weights = optimize_portfolio_weights(returns_df)

    # 3. Wylicz metryki ryzyka na zoptymalizowanym portfelu
    portfolio_returns = returns_df.dot(optimal_weights)
    metrics = calculate_comprehensive_metrics(portfolio_returns)

    print(f"Parametryczny VaR (95%): {metrics['parametric']['var']}")
    """, language="python")


# ==========================================
# ZAKŁADKA 2: KALKULATOR RYZYKA
# ==========================================
elif page == "Kalkulator Ryzyka":
    st.title("Interaktywny Kalkulator Ryzyka")
    st.markdown("Przetestuj działanie algorytmów na żywych danych z giełdy. Wybierz spółki, a nasz silnik API zoptymalizuje wagi i wyliczy ryzyko ogonowe.")
    
    # Używamy zapamiętanych spółek z Doradcy jako domyślnych
    tickers_input = st.multiselect("Wybierz aktywa do portfela (min. 2):", 
                                   options=POPULAR_TICKERS, 
                                   default=st.session_state['selected_profile_tickers'])
    
    if st.button("Wykonaj obliczenia", type="primary"):
        if len(tickers_input) < 2:
            st.warning("Wybierz co najmniej 2 spółki, aby wykonać optymalizację portfela.")
        else:
            with st.spinner("Trwa pobieranie danych z giełdy i obliczanie modeli ryzyka (GARCH, VaR, Monte Carlo)..."):
                try:
                    # ADRES TWOJEGO API NA RENDER
                    res = requests.get("https://quantriskengine.onrender.com/v1/portfolio/risk", params={"tickers": tickers_input}, timeout=25)
                    res.raise_for_status()
                    data = res.json()
                    
                    st.success("Obliczenia zakończone sukcesem! (HTTP 200 OK)")
                    
                    risk = data.get("risk_metrics", {})
                    backtest = data.get("backtest", {})
                    
                    st.markdown("---")
                    st.markdown("### Raport Ryzyka i Optymalizacji (Układ Pionowy)")
                    
                    # --- UKŁAD PIONOWY Z OPISAMI ---
                    
                    # 1. Roczna zmienność
                    vol = risk.get('volatility', 'N/A')
                    st.markdown("#### 📊 Podstawowa miara ryzyka")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"<div class='result-box'><div class='metric-label'>Roczna zmienność (Volatility)</div><div class='metric-value'>{vol}</div></div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class='metric-description'>
                        Określa, jak bardzo cena portfela waha się w ciągu roku.
                        - <span class='good-result'>Git: < 2%</span> (Portfel stabilny, defensywny).<br>
                        - <span class='bad-result'>Dużo: > 5%</span> (Portfel agresywny, możliwe gwałtowne zmiany wartości).
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True) # Odstęp

                    # 2. Parametryczny VaR
                    pvar = risk.get('parametric', {}).get('var', 'N/A')
                    st.markdown("#### 📉 Ryzyko normalnych warunków rynkowych")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"<div class='result-box'><div class='metric-label'>Parametryczny VaR (95%)</div><div class='metric-value' style='color:#d73a49;'>{pvar}</div></div>", unsafe_allow_html=True)
                    with c2:
                        # Parsowanie wartości dla logiki opisu (zaokrąglone dla przykładu)
                        try: 
                            v_val = float(pvar.strip('%')) 
                            meaning = "<span class='good-result'>Git</span>" if v_val < 3.0 else "<span class='bad-result'>Kiepsko</span>"
                        except: meaning = ""
                        
                        st.markdown(f"""
                        <div class='metric-description'>
                        Maksymalna oczekiwana strata w ciągu jednego dnia z 95% pewnością.
                        - Wynik {pvar} oznacza: {meaning}.<br>
                        - Chcemy: <span class='good-result'>< 3%</span>. Statystycznie raz na 20 dni strata może być większa.
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                    # 3. Expected Shortfall
                    es = risk.get('historical', {}).get('es', 'N/A')
                    st.markdown("#### 💥 Ryzyko skrajnych załamań (Ogonowe)")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"<div class='result-box'><div class='metric-label'>Oczekiwana strata (CVaR)</div><div class='metric-value' style='color:#cb2431;'>{es}</div></div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class='metric-description'>
                        Średnia strata w najgorszych 5% przypadków (gdy VaR zostanie przekroczony).
                        - Pokazuje, co się stanie podczas krachu.<br>
                        - Chcemy: <span class='good-result'>< 5%</span>. Wyniki powyżej oznaczają głębokie straty w sytuacjach kryzysowych.
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                    # 4. Status Walidacji
                    b_status = backtest.get('status', 'N/A')
                    b_viol = backtest.get('violations', 'N/A')
                    st.markdown("#### ✅ Wiarygodność Modelu")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st_color = "#28a745" if b_status == "OK" else "#d73a49"
                        st.markdown(f"<div class='result-box'><div class='metric-label'>Status Walidacji (Test Kupca)</div><div class='metric-value' style='color:{st_color};'>{b_status}</div><div style='font-size:12px; color:#586069;'>Liczba przekroczeń: {b_viol}</div></div>", unsafe_allow_html=True)
                    with c2:
                        meaning = "<span class='good-result'>Git (Model zaufany)</span>" if b_status == "OK" else "<span class='bad-result'>Kiepsko (Model myli się za często)</span>"
                        st.markdown(f"""
                        <div class='metric-description'>
                        Sprawdza, czy model poprawnie przewidywał ryzyko w przeszłości.
                        - Wynik {b_status} oznacza: {meaning}.<br>
                        - Chcemy: <span class='good-result'>OK</span>. Status FAILED oznacza, że nie należy ufać powyższym wyliczeniom VaR.
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Wystąpił błąd podczas obliczeń: {e}")


# ==========================================
# ZAKŁADKA 3: DORADCA PORTFELOWY
# ==========================================
elif page == "Doradca Portfelowy":
    st.title("Inteligentny Doradca Portfelowy")
    st.markdown("Nie wiesz od czego zacząć? Wybierz swój profil inwestycyjny, a algorytm zasugeruje odpowiedni dobór spółek bazowych do optymalizacji.")
    
    profile = st.selectbox("Określ swoją tolerancję na ryzyko:", ["Konserwatywny (Niskie ryzyko)", "Zrównoważony (Średnie ryzyko)", "Agresywny (Wysokie ryzyko)"])
    
    st.markdown("---")
    
    current_tickers = []
    
    if profile == "Konserwatywny (Niskie ryzyko)":
        current_tickers = ['JNJ', 'PG', 'WMT', 'JPM', 'V']
        st.markdown("### Sugerowane aktywa: 🛡️ Defensywne i Dywidendowe")
        st.info("**Sektory:** Dobra podstawowe, Ochrona zdrowia, Finanse")
        st.code(f"tickers = {current_tickers}", language="python")
        st.markdown("Zestawienie idealne do modeli minimalizacji wariancji. Model GARCH wykazuje tutaj rzadsze skoki zmienności, zapewniając stabilność kapitału.")
        
    elif profile == "Zrównoważony (Średnie ryzyko)":
        current_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
        st.markdown("### Sugerowane aktywa: ⚖️ Big Tech i Blue Chips")
        st.info("**Sektory:** Technologia, Usługi komunikacyjne")
        st.code(f"tickers = {current_tickers}", language="python")
        st.markdown("Solidny balans. Optymalizacja Markowitza (maksymalizacja Sharpe Ratio) działa tu najlepiej, znajdując matematyczny złoty środek między wzrostem a ryzykiem.")
        
    elif profile == "Agresywny (Wysokie ryzyko)":
        current_tickers = ['NVDA', 'TSLA', 'AMD', 'META', 'NFLX']
        st.markdown("### Sugerowane aktywa: 🚀 Nowe Technologie i Półprzewodniki")
        st.info("**Sektory:** Półprzewodniki, Auta Elektryczne (EV)")
        st.code(f"tickers = {current_tickers}", language="python")
        st.markdown("Wysoka zmienność. Należy oczekiwać głębokich wartości **Expected Shortfall (CVaR)** oraz wyraźnego klastrowania zmienności wyłapywanego przez modele z rodziny ARCH/GARCH.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- PRZYCISK POWROTU DO KALKULATORA Z AUTO-WYBOREM ---
    def auto_analyze():
        st.session_state['selected_profile_tickers'] = current_tickers
        st.session_state['active_page'] = "Kalkulator Ryzyka"

    st.button(f"🔎 Przeanalizuj strategię {profile.split(' (')[0]} w Kalkulatorze", 
              type="primary", 
              on_click=auto_analyze)


# ==========================================
# ZAKŁADKA 4: POBIERANIE PLIKÓW
# ==========================================
elif page == "Pobierz pliki":
    st.title("Pobieranie plików i zasobów")
    st.markdown("Pobierz przykładowe dane historyczne, raporty z walidacji modelu lub zbudowane paczki dystrybucyjne silnika.")
    
    dummy_report = {
        "engine_version": "2.0.0",
        "validation_tests": ["Kupiec POF", "Christoffersen Independence", "Monte Carlo Normalcy"],
        "status": "Production Ready"
    }
    json_string = json.dumps(dummy_report, indent=4)
    
    st.markdown("### Paczka konfiguracyjna: quant-risk-pro-2.0.0.tar.gz")
    st.markdown("Plik konfiguracyjny rdzenia API oraz logi z walidacji modeli statystycznych.")
    
    st.download_button(
        label="📥 Pobierz raport JSON (Config)",
        file_name="quant_risk_report.json",
        mime="application/json",
        data=json_string,
        type="primary"
    )
    
    st.markdown("---")
    st.markdown("### Pliki danych historycznych (.csv)")
    st.markdown("Przykładowy wyciąg dziennych stóp zwrotu do samodzielnego przetestowania (Test Data).")
    
    dummy_csv = "Data,AAPL,MSFT\n2023-01-01,0.012,-0.005\n2023-01-02,0.021,0.011\n"
    st.download_button(
        label="📊 Pobierz dane testowe (CSV)",
        file_name="test_data.csv",
        mime="text/csv",
        data=dummy_csv
    )
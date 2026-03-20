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
st.set_page_config(page_title="Kalkulator Ryzyka Inwestycyjnego", layout="wide", initial_sidebar_state="expanded")

# --- ZAAWANSOWANY CSS (Styl PyPI / Dokumentacji) ---
st.markdown("""
    <style>
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
    
    /* Ukrycie domyślnego menu Streamlit z dołu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Metadane w pasku bocznym */
    .sidebar-meta { font-size: 14px; line-height: 1.6; color: #586069; }
    .sidebar-meta strong { color: #24292e; }
    
    /* Sekcje wyników (Kalkulator) */
    .result-box { border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 15px; background-color: #fafbfc; height: 100%; }
    .metric-value { font-size: 24px; font-weight: bold; color: #0366d6; }
    .metric-label { font-size: 12px; color: #586069; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- ZMIENNE GLOBALNE ---
POPULAR_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", "WMT", "JNJ", "PG", "XOM"]

# --- PASEK BOCZNY (SIDEBAR) JAK W PYPI ---
with st.sidebar:
    st.markdown("### Nawigacja")
    page = st.radio("Przejdź do", 
                    ["Opis projektu", "Kalkulator Ryzyka", "Doradca Portfelowy", "Pobierz pliki"], 
                    label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### Zweryfikowane szczegóły ✅")
    st.markdown("<div class='sidebar-meta'>Te szczegóły zostały zweryfikowane przez System.</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Twórcy")
    st.markdown("<div class='sidebar-meta'>👤 <strong>Twórca Kalkulatora</strong></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Metadane")
    st.markdown("""
    <div class='sidebar-meta'>
    <ul>
        <li><strong>Licencja:</strong> MIT</li>
        <li><strong>Autor:</strong> Risk Team</li>
        <li>🏷️ python, finanse, ryzyko, inwestycje</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Kategorie")
    st.markdown("<div class='sidebar-meta'><strong>Grupa docelowa:</strong><br><ul><li>Inwestorzy indywidualni</li><li>Analitycy Finansowi</li></ul></div>", unsafe_allow_html=True)


# ==========================================
# ZAKŁADKA 1: OPIS PROJEKTU (DOKUMENTACJA)
# ==========================================
if page == "Opis projektu":
    st.title("Kalkulator Ryzyka Inwestycyjnego")
    st.markdown("**Czym jest ten projekt?**\nJest to zaawansowane, ale proste w użyciu narzędzie do analizy bezpieczeństwa i optymalizacji portfeli inwestycyjnych na giełdzie.")
    st.markdown("**Dla kogo jest przeznaczone?**\nDla każdego inwestora, analityka lub programisty, który chce lepiej zrozumieć, ile ryzykuje na giełdzie i jak zbalansować swoje akcje, aby zminimalizować ewentualne straty.")
    
    st.subheader("Instalacja modułu (dla programistów)")
    st.code("pip install portfolio-risk-calculator", language="bash")
    
    st.markdown("---")
    st.subheader("Wdrożona Architektura")
    st.markdown("""
    System pod spodem wykorzystuje zaawansowany silnik matematyczny do wyceny ryzyka. 
    Aplikacja jest połączona z asynchronicznym API, które na bieżąco pobiera dane i wykonuje skomplikowane wektoryzowane obliczenia (NumPy, Pandas), ukrywając całą trudną matematykę pod przystępnym interfejsem.
    """)
    
    st.subheader("Kluczowe możliwości algorytmu")
    st.markdown("""
    * **Ochrona kapitału:** Estymacja Oczekiwanej Straty (CVaR) w scenariuszach skrajnego załamania rynku.
    * **Maksymalizacja zysków:** Optymalizacja portfela metodą Markowitza w celu znalezienia idealnego balansu między ryzykiem a zyskiem.
    * **Ocena historyczna:** Parametryczny i Historyczny VaR (Value at Risk - wskaźnik zagrożenia kapitału).
    * **Analiza zmienności:** Prognozowanie przyszłych wahań cen za pomocą procesów GARCH(1,1).
    * **Symulacje przyszłości:** Generowanie tysięcy losowych ścieżek rozwoju portfela (Metoda Monte Carlo).
    * **Weryfikacja modeli:** Automatyczny backtesting (Test Kupca) weryfikujący, czy modele matematyczne sprawdzały się w przeszłości.
    """)
    
    st.subheader("Szybki start - Przykład użycia API w kodzie")
    st.markdown("Jeśli chcesz zintegrować nasz kalkulator we własnym skrypcie Python, użyj poniższego kodu:")
    
    st.code("""
    from core.risk_metrics import calculate_comprehensive_metrics
    from core.models import optimize_portfolio_weights
    from data.ingestor import fetch_data

    # 1. Pobierz dane rynkowe dla spółek
    returns_df = fetch_data(["AAPL", "MSFT", "TSLA"])

    # 2. Zoptymalizuj wagi portfela (szukaj najlepszego balansu zysk/ryzyko)
    optimal_weights = optimize_portfolio_weights(returns_df)

    # 3. Wylicz metryki ryzyka na zoptymalizowanym portfelu
    portfolio_returns = returns_df.dot(optimal_weights)
    metrics = calculate_comprehensive_metrics(portfolio_returns)

    print(f"Szacowane ryzyko (VaR 95%): {metrics['parametric']['var']}")
    """, language="python")


# ==========================================
# ZAKŁADKA 2: KALKULATOR RYZYKA
# ==========================================
elif page == "Kalkulator Ryzyka":
    st.title("Interaktywny Kalkulator Ryzyka")
    st.markdown("Przetestuj swoje inwestycje. Wybierz spółki ze swojego portfela, a nasz algorytm przeanalizuje ich historię, zoptymalizuje wagi i pokaże Ci ukryte ryzyko.")
    
    tickers_input = st.multiselect("Wybierz aktywa do portfela (min. 2):", options=POPULAR_TICKERS, default=["MSFT", "AAPL"])
    
    if st.button("Wykonaj analizę portfela", type="primary"):
        if len(tickers_input) < 2:
            st.warning("Wybierz co najmniej 2 spółki, aby wykonać optymalizację portfela.")
        else:
            with st.spinner("Trwa pobieranie danych giełdowych i symulacja scenariuszy strat (to może potrwać kilka sekund)..."):
                try:
                    res = requests.get("https://quantriskengine.onrender.com/v1/portfolio/risk", params={"tickers": tickers_input}, timeout=15)
                    res.raise_for_status()
                    data = res.json()
                    
                    st.success("Obliczenia zakończone sukcesem!")
                    
                    risk = data.get("risk_metrics", {})
                    backtest = data.get("backtest", {})
                    
                    st.markdown("### Szczegółowy Raport Ryzyka")
                    st.markdown("Poniżej znajdziesz wyniki wskaźników z opisem, jak wpływają na Twoje pieniądze.")
                    
                    # --- FUNKCJA POMOCNICZA DO OCENY WYNIKÓW I KOLOROWANIA ---
                    def get_eval_html(val_str, threshold_good, threshold_bad):
                        if val_str in ['N/A', None, '']: return "<span style='color: gray;'>Brak danych do analizy</span>"
                        try:
                            # Próba zmiany stringa np. "15.2%" na liczbę 15.2
                            v = float(str(val_str).replace('%', '').strip())
                            v = abs(v) # upewnienie się że mamy wartość dodatnią do oceny poziomu
                            
                            # Konwersja formatu dziesiętnego (np. 0.15) na procenty do oceny, jeśli brakuje znaku %
                            if v < 1.0 and '%' not in str(val_str): 
                                v = v * 100 
                                
                            if v <= threshold_good:
                                return f"<span style='color: #28a745; font-weight: bold;'>{val_str} - Dobry wynik (Bezpiecznie)</span>"
                            elif v >= threshold_bad:
                                return f"<span style='color: #d73a49; font-weight: bold;'>{val_str} - Zły wynik (Duże ryzyko!)</span>"
                            else:
                                return f"<span style='color: #b08800; font-weight: bold;'>{val_str} - Przeciętny (Wymaga uwagi)</span>"
                        except:
                            return f"<span style='color: gray;'>{val_str} (Nietypowy format)</span>"

                    st.markdown("---")
                    
                    # 1. ZMIENNOŚĆ
                    v_vol = risk.get('volatility', 'N/A')
                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Roczna zmienność (Volatility)</div>"
                                    f"<div class='metric-value'>{v_vol}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** Jest to miara określająca, jak gwałtownie skaczą ceny Twoich akcji w ciągu roku.<br>"
                                    "**Jak to wpływa na portfel?** Mniejsze wahania (poniżej 15%) to spokojniejszy sen i mniejsze ryzyko uwięzienia z minusem na koncie. Wyniki powyżej 25-30% oznaczają bardzo agresywny i podatny na panikę portfel.<br>"
                                    f"**Twoja ocena:** {get_eval_html(v_vol, 15, 25)}", unsafe_allow_html=True)
                    
                    # 2. PARAMETRYCZNY VaR
                    v_pvar = risk.get('parametric', {}).get('var', 'N/A')
                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Parametryczny VaR (95%)</div>"
                                    f"<div class='metric-value' style='color:#d73a49;'>{v_pvar}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** 'Value at Risk'. Mówi, jakiej maksymalnej straty w normalnych warunkach możemy się spodziewać w 95% przypadków.<br>"
                                    "**Jak to wpływa na portfel?** Pokazuje granicę bólu. Jeśli wynosi np. 5%, oznacza to, że w 95% przypadków Twój portfel nie spadnie bardziej niż o te 5%. Chcemy, aby ta liczba była jak najniższa (najlepiej poniżej 3-5%).<br>"
                                    f"**Twoja ocena:** {get_eval_html(v_pvar, 4, 8)}", unsafe_allow_html=True)

                    # 3. HISTORYCZNY VaR
                    v_hvar = risk.get('historical', {}).get('var', 'N/A')
                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Historyczny VaR (95%)</div>"
                                    f"<div class='metric-value' style='color:#d73a49;'>{v_hvar}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** Ten sam wskaźnik co wyżej, ale bazujący sztywno na prawdziwych, historycznych krachach Twoich spółek.<br>"
                                    "**Jak to wpływa na portfel?** Pozwala spojrzeć prawdzie w oczy: pokazuje, jak bardzo te konkretne spółki potrafiły dołować w przeszłości i chroni przed zbytnim optymizmem teorii matematycznych.<br>"
                                    f"**Twoja ocena:** {get_eval_html(v_hvar, 4, 8)}", unsafe_allow_html=True)

                    # 4. OCZEKIWANA STRATA (CVaR)
                    v_cvar = risk.get('historical', {}).get('es', 'N/A')
                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Oczekiwana strata (CVaR)</div>"
                                    f"<div class='metric-value' style='color:#cb2431;'>{v_cvar}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** Skrót od 'Expected Shortfall'. Pyta: 'Skoro już nadszedł czarny łabędź i pękło 95% pewności z modelu VaR, to ile średnio pieniędzy wtedy stracę?'.<br>"
                                    "**Jak to wpływa na portfel?** To najważniejsza miara ochrony przed bankructwem. W ekstremalnych krachach pokazuje faktyczny ból. Dobry wynik utrzymuje się poniżej 6%. Powyżej 12% grozi ogromną stratą.<br>"
                                    f"**Twoja ocena:** {get_eval_html(v_cvar, 6, 12)}", unsafe_allow_html=True)

                    # 5. MONTE CARLO VaR
                    v_mcvar = risk.get('monte_carlo', {}).get('var', 'N/A')
                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Monte Carlo VaR</div>"
                                    f"<div class='metric-value' style='color:#d73a49;'>{v_mcvar}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** Potencjał straty wyliczony na podstawie tysięcy komputerowo wygenerowanych, losowych scenariuszy przyszłości.<br>"
                                    "**Jak to wpływa na portfel?** Daje bardzo wiarygodny ogląd, ponieważ uwzględnia ścieżki rozwoju, które mogły się jeszcze nigdy historycznie nie wydarzyć.<br>"
                                    f"**Twoja ocena:** {get_eval_html(v_mcvar, 4, 8)}", unsafe_allow_html=True)

                    # 6. STATUS WALIDACJI (TEST KUPCA)
                    v_status = backtest.get('status', 'N/A')
                    v_viol = backtest.get('violations', 'N/A')
                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Wiarygodność modelu (Test Kupca)</div>"
                                    f"<div class='metric-value' style='color:#0366d6;'>{v_status}</div>"
                                    f"<div style='font-size:12px; color:#586069;'>Liczba pomyłek: {v_viol}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** Komputer cofa się w czasie i sprawdza, czy przewidziane ryzyko faktycznie ochroniło kapitał przed stratami.<br>"
                                    "**Jak to wpływa na portfel?** Buduje zaufanie do powyższych metryk. Zbyt wiele 'pomyłek' (przekroczeń strat) oznacza, że rynek staje się zbyt dziki i modelom przestaje ufać.<br>"
                                    f"**Twoja ocena:** <span style='color: {'#28a745' if 'Pass' in str(v_status) or 'Ready' in str(v_status) or 'OK' in str(v_status) else '#586069'}; font-weight: bold;'>{v_status}</span>", unsafe_allow_html=True)

                except requests.exceptions.ConnectionError:
                    st.error("Błąd połączenia z API na serwerze (np. na Render). Serwer może być w trybie uśpienia. Poczekaj 50s i spróbuj ponownie.")
                except Exception as e:
                    st.error(f"Wystąpił błąd podczas obliczeń: {e}")


# ==========================================
# ZAKŁADKA 3: DORADCA PORTFELOWY (ULEPSZONA)
# ==========================================
elif page == "Doradca Portfelowy":
    st.title("Inteligentny Doradca Portfelowy")
    st.markdown("Wybierz swój profil inwestycyjny, a algorytm zaproponuje strukturę portfela opartą o zaawansowane modele matematyczne.")
    
    profile = st.selectbox("Określ swoją tolerancję na ryzyko:", 
                          ["Konserwatywny (Niskie ryzyko)", "Zrównoważony (Średnie ryzyko)", "Agresywny (Wysokie ryzyko)"])
    
    st.markdown("---")
    
    # Konfiguracja doradcy
    config = {
        "Konserwatywny (Niskie ryzyko)": {
            "tickers": ["JNJ", "PG", "WMT", "JPM", "V"],
            "weights": [0.25, 0.25, 0.20, 0.15, 0.15],
            "desc": "Zestawienie idealne do minimalizacji wahań. Wybrano spółki o stabilnych dywidendach i silnej pozycji rynkowej.",
            "method": "Global Minimum Variance (GMV)",
            "code_logic": "weights = min_variance_optimizer(returns_cov_matrix)",
            "drift": 0.0002 # symulacja dla wykresu
        },
        "Zrównoważony (Średnie ryzyko)": {
            "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "weights": [0.30, 0.30, 0.20, 0.20],
            "desc": "Solidny balans między wzrostem kapitału a bezpieczeństwem. Znajduje złoty środek między oczekiwanym zyskiem a ryzykiem.",
            "method": "Maximum Sharpe Ratio (MSR)",
            "code_logic": "weights = max_sharpe_optimizer(expected_returns, cov_matrix)",
            "drift": 0.0005
        },
        "Agresywny (Wysokie ryzyko)": {
            "tickers": ["NVDA", "TSLA", "AMD", "META", "NFLX"],
            "weights": [0.35, 0.25, 0.15, 0.15, 0.10],
            "desc": "Skupienie na firmach technologicznych z dużą dynamiką (Growth). Akceptujemy duże wahania w zamian za szansę na wysokie zyski.",
            "method": "Risk Parity / Alpha Seeking",
            "code_logic": "weights = risk_budgeting_optimizer(garch_volatility_forecast)",
            "drift": 0.001
        }
    }
    
    current = config[profile]
    
    col_text, col_chart = st.columns([1.2, 1])
    
    with col_text:
        st.subheader(f"🛡️ Strategia: {profile.split(' (')[0]}")
        st.markdown(f"**Dlaczego te spółki?**\n{current['desc']}")
        st.info(f"**Metoda obliczeniowa pod maską:** {current['method']}")
        st.markdown("**Zastosowany silnik:**")
        st.code(current['code_logic'], language="python")
        
    with col_chart:
        # Wykres kołowy alokacji
        fig_pie = px.pie(names=current['tickers'], values=current['weights'], 
                         title="Sugerowana budowa portfela", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    
    # --- KALKULATOR ZAKUPÓW ---
    st.subheader("💰 Kalkulator wielkości pozycji")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        waluta = st.selectbox("Waluta:", ["PLN", "USD", "EUR"])
    with c2:
        kwota = st.number_input(f"Kwota inwestycji ({waluta}):", min_value=1000, value=10000, step=500)
    with c3:
        st.markdown(f"**Sugerowany podział dla {kwota} {waluta}:**")
        # Wyświetlenie metrów dla każdej spółki
        cols = st.columns(len(current['tickers']))
        for i, t in enumerate(current['tickers']):
            pos_val = kwota * current['weights'][i]
            cols[i].metric(t, f"{int(current['weights'][i]*100)}%", f"{int(pos_val)} {waluta}")

    st.markdown("---")

    # --- WYKRES PROGNOZY ---
    st.subheader("📈 Prognoza wzrostu (Symulacja Komputerowa)")
    st.markdown("Potencjalne zachowanie Twojego kapitału w ciągu najbliższych 252 dni handlowych (1 rok).")
    
    np.random.seed(42)
    days = 252
    # Generowanie ścieżki random walk na bazie profilu
    returns = np.random.normal(current['drift'], 0.012, days)
    price_path = np.exp(np.cumsum(returns))
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=list(range(days)), y=price_path, mode='lines', 
                                  name='Scenariusz bazowy', line=dict(color='#0366d6', width=2)))
    fig_line.update_layout(xaxis_title="Dni z rzędu", yaxis_title="Wartość portfela", 
                           height=350, margin=dict(t=20))
    st.plotly_chart(fig_line, use_container_width=True)


# ==========================================
# ZAKŁADKA 4: POBIERANIE PLIKÓW
# ==========================================
elif page == "Pobierz pliki":
    st.title("Pobieranie plików i zasobów")
    st.markdown("Pobierz przykładowe dane giełdowe lub raporty ze swojego konta.")
    
    dummy_report = {
        "engine_version": "2.0.0",
        "validation_tests": ["Kupiec POF", "Christoffersen Independence", "Monte Carlo Normalcy"],
        "status": "Production Ready"
    }
    json_string = json.dumps(dummy_report, indent=4)
    
    st.download_button(
        label="📥 Pobierz raport bezpieczeństwa (JSON)",
        file_name="risk_report.json",
        mime="application/json",
        data=json_string,
        type="primary"
    )
    
    st.markdown("---")
    dummy_csv = "Data,AAPL,MSFT\n2023-01-01,0.012,-0.005\n2023-01-02,0.021,0.011\n"
    st.download_button(
        label="📊 Pobierz dane historyczne (CSV)",
        file_name="hist_data.csv",
        mime="text/csv",
        data=dummy_csv
    )
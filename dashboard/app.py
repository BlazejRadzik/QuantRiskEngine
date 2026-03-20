import os
import sys
import streamlit as st

# PANCERNA POPRAWKA ŚCIEŻKI:
# Pobieramy ścieżkę do folderu głównego (tam gdzie jest core i dashboard)
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Dopiero TERAZ importujemy Twoje moduły
try:
    from core.models import get_optimal_weights, simulate_monte_carlo
    from core.risk_metrics import calculate_portfolio_metrics
except ModuleNotFoundError:
    st.error(f"Nie znaleziono modułów w: {root_path}. Sprawdź strukturę plików na GitHub.")
import streamlit as st
import requests
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yfinance as yf

@st.cache_data(ttl=3600)
def load_data(tickers):
    data = yf.download(tickers, period="1y", progress=False)
    return data

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

# --- ZARZĄDZANIE STANEM (Pamięta wybrane spółki) ---
if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = ["MSFT", "AAPL"]

# --- BAZA ETF I SPÓŁEK ---
ETF_CONSTITUENTS = {
    "Wybierz ETF...": [],
    "SPY (S&P 500 Top)": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "TSLA", "UNH", "JNJ"],
    "QQQ (Nasdaq 100)": ["MSFT", "AAPL", "NVDA", "AMZN", "META", "AVGO", "TSLA", "GOOGL", "GOOG", "COST", "PEP"],
    "XLF (Sektor Finansowy)": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "SPGI", "GS", "MS", "AXP"]
}

# Połączona duża lista tickerów
ALL_TICKERS = list(set(["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "JPM", "V", "WMT", "JNJ", "PG", "XOM", "BAC", "MA", "HD", "CVX", "MRK", "KO", "PEP", "AVGO", "COST", "MCD", "CSCO", "INTC", "AMD", "DIS", "ADBE", "CRM"] + [ticker for sublist in ETF_CONSTITUENTS.values() for ticker in sublist]))
ALL_TICKERS.sort()

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
    st.markdown("<div class='sidebar-meta'>👤 <strong>BR</strong></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Metadane")
    st.markdown("""
    <div class='sidebar-meta'>
    <ul>
        <li><strong>Licencja:</strong> MIT</li>
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
    st.markdown("**Czym jest ten projekt?**\nJest to proste w użyciu narzędzie do analizy bezpieczeństwa i optymalizacji portfeli inwestycyjnych na giełdzie.")
    st.markdown("**Dla kogo jest przeznaczone?**\nDla każdego inwestora, analityka lub programisty, który chce lepiej zrozumieć, ile ryzykuje na giełdzie i jak zbalansować swoje akcje, aby zminimalizować ewentualne straty.")
    
    st.subheader("Instalacja modułu (dla programistów)")
    st.code("pip install portfolio-risk-calculator", language="bash")
    
    st.markdown("---")
    st.subheader("Wdrożona Architektura")
    st.markdown("""
    System pod spodem wykorzystuje silnik matematyczny do wyceny ryzyka. 
    Aplikacja jest połączona z asynchronicznym API, które na bieżąco pobiera dane i wykonuje wektoryzowane obliczenia (NumPy, Pandas), ukrywając całą matematykę pod interfejsem.
    """)
    
    st.subheader("Kluczowe możliwości algorytmu")
    st.markdown("""
    * **Ochrona kapitału:** Estymacja Oczekiwanej Straty (CVaR) w scenariuszach skrajnego załamania rynku.
    * **Maksymalizacja zysków:** Optymalizacja portfela metodą Markowitza w celu znalezienia idealnego balansu między ryzykiem a zyskiem.
    * **Ocena historyczna:** Parametryczny i Historyczny VaR (Value at Risk - wskaźnik zagrożenia kapitału).
    * **Analiza zmienności:** Prognozowanie przyszłych wahań cen za pomocą procesów GARCH(1,1).
    * **Symulacje przyszłości:** Generowanie losowych ścieżek rozwoju portfela (Metoda Monte Carlo).
    * **Weryfikacja modeli:** Automatyczny backtesting (Test Kupca) weryfikujący, czy modele matematyczne sprawdzały się w przeszłości.
    """)
    
    st.subheader("Szybki start - Przykład użycia API w kodzie")
    st.markdown("Jeśli chcesz zintegrować kalkulator we własnym skrypcie Python, użyj poniższego kodu:")
    
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
    st.markdown("Przetestuj swoje inwestycje. Wybierz spółki ze swojego portfela (lub całe ETF-y), a algorytm przeanalizuje ich historię, zoptymalizuje wagi i pokaże Ci ukryte ryzyko.")
    
    st.markdown("---")
    
    # NOWY UKŁAD: Lewa strona (Wyszukiwarka), Prawa strona (ETF)
    col_search, col_etf = st.columns([1.5, 1])
    
    with col_etf:
        st.markdown("### 🏦 Wybierz z ETF")
        selected_etf = st.selectbox("Wybierz fundusz, aby zobaczyć jego składniki:", list(ETF_CONSTITUENTS.keys()))
        
        if selected_etf != "Wybierz ETF...":
            etf_tickers = ETF_CONSTITUENTS[selected_etf]
            st.info(f"**Skład {selected_etf}:** {', '.join(etf_tickers)}")
            
            # Przycisk dodający spółki
            if st.button(f"➕ Dodaj akcje z {selected_etf.split(' ')[0]}"):
                current_list = st.session_state.get("ms_tickers", st.session_state.selected_tickers)
                new_list = list(current_list)
                
                for t in etf_tickers:
                    if t not in new_list and len(new_list) < 12:
                        new_list.append(t)
                        
                st.session_state.selected_tickers = new_list
                st.session_state.ms_tickers = new_list
                st.rerun()
    
    with col_search:
        st.markdown("### 🔍 Wyszukiwarka spółek")
        
        def update_tickers():
            st.session_state.selected_tickers = st.session_state.ms_tickers
            
        st.multiselect(
            "Wpisz ticker (np. AAPL) lub wybierz z listy (Limit: max 12 spółek dla stabilności serwera):", 
            options=ALL_TICKERS, 
            default=st.session_state.selected_tickers,
            key="ms_tickers",
            on_change=update_tickers,
            max_selections=12
        )
        st.caption(f"Wybrano: {len(st.session_state.selected_tickers)} aktywów")

    st.markdown("---")
    
    if st.button("Wykonaj analizę portfela", type="primary"):
        if len(st.session_state.selected_tickers) < 2:
            st.warning("Wybierz co najmniej 2 spółki, aby wykonać optymalizację portfela.")
        else:
            with st.spinner("Trwa pobieranie danych giełdowych i symulacja scenariuszy strat (to może potrwać do półtorej minuty, w przypadku błędu spróbuj ponownie)..."):
                try:
                    res = requests.get("https://quantriskengine.onrender.com/v1/portfolio/risk", params={"tickers": st.session_state.selected_tickers}, timeout=90)
                    res.raise_for_status()
                    data = res.json()
                    
                    st.success("Obliczenia zakończone sukcesem!")
                    
                    risk = data.get("risk_metrics", {})
                    backtest = data.get("backtest", {})
                    
                    st.markdown("### Szczegółowy Raport Ryzyka")
                    st.markdown("Poniżej znajdziesz wyniki wskaźników z opisem, jak wpływają na Twoje pieniądze.")
                    
                    # Zmień progi w get_eval_html na bardziej "rynkowe" dla akcji (Equity)
                    def get_eval_html(val_str, threshold_good, threshold_bad):
                        try:
                            v = float(str(val_str).replace('%', '').strip())
                            v = abs(v)
                            # Volatility: <15% (Low), 15-30% (Moderate), >30% (High) - standard dla S&P500 vs Tech
                            if v <= threshold_good:
                                return f"<span style='color: #28a745; font-weight: bold;'>{val_str} - Konserwatywny</span>"
                            elif v >= threshold_bad:
                                return f"<span style='color: #d73a49; font-weight: bold;'>{val_str} - Agresywny</span>"
                            else:
                                return f"<span style='color: #b08800; font-weight: bold;'>{val_str} - Zrównoważony</span>"
                        except:
                            return f"<span style='color: gray;'>{val_str}</span>"

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

                    # 6. STATUS WALIDACJI (TEST KUPCA) - Z filtrem logicznym
                    v_status = backtest.get('status', 'N/A')
                    v_viol = backtest.get('violations', 0)
                    
                    # Logika oceniająca - nie ufamy ślepo API!
                    try:
                        viol_count = int(v_viol)
                        if viol_count > 16:
                            v_status = "Odrzucony (Model nie trzyma ryzyka)"
                            status_color = "#d73a49" # Czerwony
                        else:
                            status_color = "#28a745" if "Pass" in str(v_status) else "#b08800"
                    except:
                        status_color = "#586069" # Szary błąd

                    c_box, c_desc = st.columns([1, 2.5])
                    with c_box:
                        st.markdown("<div class='result-box'><div class='metric-label'>Wiarygodność modelu (Test Kupca)</div>"
                                    f"<div class='metric-value' style='color:{status_color}; font-size:18px;'>{v_status}</div>"
                                    f"<div style='font-size:12px; color:#586069; margin-top:5px;'>Przekroczenia straty (Pomyłki): {v_viol}</div></div>", unsafe_allow_html=True)
                    with c_desc:
                        st.markdown("**Co to znaczy?** Komputer cofa się w czasie i sprawdza, czy przewidziane ryzyko faktycznie ochroniło kapitał.<br>"
                                    "**Jak to wpływa na portfel?** Limit pomyłek dla 1 roku wynosi około 12-16. Jeśli liczba 'pomyłek' jest wyższa, model zawiódł w przeszłości i nie wolno mu ufać.<br>", unsafe_allow_html=True)

                except requests.exceptions.ReadTimeout:
                    st.error("Błąd: Serwer potrzebował zbyt dużo czasu na przeliczenie tak dużej ilości danych. Zmniejsz liczbę aktywów i spróbuj ponownie.")
                except requests.exceptions.ConnectionError:
                    st.error("Błąd połączenia z API na serwerze (np. na Render). Serwer może być w trybie uśpienia. Poczekaj 50s i spróbuj ponownie.")
                except Exception as e:
                    st.error(f"Wystąpił błąd podczas obliczeń: {e}")


# ==========================================
# ZAKŁADKA 3: DORADCA PORTFELOWY (OBLICZENIA NA ŻYWO)
# ==========================================
elif page == "Doradca Portfelowy":
    st.title("Inteligentny Doradca Portfelowy")
    st.markdown("Wybierz swój profil inwestycyjny. Algorytm na żywo pobierze dane z giełdy i zoptymalizuje wagi dla wybranej grupy aktywów.")
    
    profile = st.selectbox("Określ swoją tolerancję na ryzyko:", 
                          ["Konserwatywny (Niskie ryzyko)", "Zrównoważony (Średnie ryzyko)", "Agresywny (Wysokie ryzyko)"])
    
    st.markdown("---")
    
    # 1. Konfiguracja puli spółek pod profil
    base_config = {
        "Konserwatywny (Niskie ryzyko)": {
            "tickers": ["JNJ", "PG", "WMT", "JPM", "V"],
            "desc": "Zestawienie idealne do minimalizacji wahań. Szukamy portfela o najmniejszym możliwym ryzyku.",
            "method": "Global Minimum Variance (GMV) - Optymalizacja matematyczna Scipy",
            "code_logic": "weights = get_optimal_weights(returns, 'min_vol')",
            "strategy_type": "min_vol"
        },
        "Zrównoważony (Średnie ryzyko)": {
            "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "desc": "Solidny balans. Algorytm szuka tzw. Złotego Środka na podstawie wskaźnika Sharpe'a.",
            "method": "Maximum Sharpe Ratio (MSR) - Optymalizacja matematyczna Scipy",
            "code_logic": "weights = get_optimal_weights(returns, 'max_sharpe')",
            "strategy_type": "max_sharpe"
        },
        "Agresywny (Wysokie ryzyko)": {
            "tickers": ["NVDA", "TSLA", "AMD", "META", "NFLX"],
            "desc": "Skupienie na wysokiej dynamice. Algorytm faworyzuje spółki z najwyższym potencjałem wzrostu.",
            "method": "Maximum Return Seeking - Optymalizacja matematyczna Scipy",
            "code_logic": "weights = get_optimal_weights(returns, 'max_return')",
            "strategy_type": "max_return"
        }
    }
    
    current_setup = base_config[profile]
    tickers = current_setup["tickers"]
    strategy = current_setup["strategy_type"]
    
    # Zmienne na wyniki
    current_weights = []
    
    # 2. Silnik Optymalizacji (Obliczenia na żywo - NAPRAWIONE)
    with st.spinner(f"Pobieram dane dla {', '.join(tickers)} i obliczam optymalne wagi..."):
        try:
            # Pobieranie świeżych danych (1 rok)
            data = load_data(tickers)
            if 'Adj Close' in data: prices = data['Adj Close']
            else: prices = data['Close']
            
            # PANCERNA NAPRAWA: YFinance sortuje tabele alfabetycznie! 
            # Wymuszamy naszą kolejność zdefiniowaną w profilu ryzyka
            if isinstance(prices, pd.Series):
                prices = prices.to_frame(name=tickers[0])
            else:
                prices = prices[tickers] 
            
            # Przygotowanie danych
            returns = prices.pct_change().dropna()
            
            # --- PRAWDZIWA OPTYMALIZACJA Z CORE ---
            current_weights = get_optimal_weights(returns, strategy)
            metrics = calculate_portfolio_metrics(current_weights, returns)
            
            # Zapisanie wyników do sesji na potrzeby raportu JSON z Zakładki 4
            st.session_state.last_opt_weights = dict(zip(tickers, current_weights))
            st.session_state.last_opt_metrics = metrics
            
            # Wyciągnięcie zmiennych do wykresów poniżej
            port_returns = metrics["portfolio_returns_series"]
            sortino_ratio = metrics["sortino_ratio"]
            skewness_val = metrics["skewness"]
            kurt_val = metrics["kurtosis"]

        except Exception as e:
            st.error(f"Błąd podczas obliczeń giełdowych: {e}. Przechodzę na równe wagi awaryjne.")
            current_weights = [1/len(tickers)] * len(tickers)
            returns = pd.DataFrame() # Puste dla uniknięcia błędów dalej
            port_returns = pd.Series([0])
            sortino_ratio, skewness_val, kurt_val = 0.0, 0.0, 0.0

    col_text, col_chart = st.columns([1.2, 1])
    
    with col_text:
        st.subheader(f"🛡️ Strategia: {profile.split(' (')[0]}")
        st.markdown(f"**Dlaczego te spółki?**\n{current_setup['desc']}")
        st.info(f"**Metoda obliczeniowa pod maską:** {current_setup['method']}")
        st.markdown("**Zastosowany silnik:**")
        st.code(current_setup['code_logic'], language="python")
        
    with col_chart:
        fig_pie = px.pie(names=tickers, values=current_weights, 
                         title="Wyliczona na żywo struktura portfela", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    
    st.subheader("💰 Kalkulator wielkości pozycji")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        waluta = st.selectbox("Waluta:", ["PLN", "USD", "EUR"])
    with c2:
        kwota = st.number_input(f"Kwota inwestycji ({waluta}):", min_value=1000, value=10000, step=500)
    with c3:
        st.markdown(f"**Wyliczony podział kapitału dla {kwota} {waluta}:**")
        cols = st.columns(len(tickers))
        for i, t in enumerate(tickers):
            pos_val = kwota * current_weights[i]
            # Używamy formatowania do 1 miejsca po przecinku, by zgadzało się ze sztywnymi ramami modelu
            cols[i].metric(t, f"{current_weights[i]*100:.1f}%", f"{round(pos_val, 2)} {waluta}")

    st.markdown("---")

    st.subheader("📈 Prognoza wzrostu (Symulacja Komputerowa)")
    st.markdown("Potencjalne zachowanie zoptymalizowanego portfela w ciągu najbliższych 252 dni handlowych (1 rok).")
    
    # NAPRAWIONE: Wielościeżkowa symulacja z backendu
    mean_path, worst_path, best_path = simulate_monte_carlo(port_returns)
    
    # PRAWIDŁOWY DRAWDOWN: Liczony z pesymistycznej ścieżki (najgorszy przypadek), a nie z rosnącej średniej!
    cum_max = np.maximum.accumulate(worst_path)
    drawdown = (worst_path - cum_max) / cum_max
    max_drawdown = drawdown.min()
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(y=mean_path, mode='lines', name='Scenariusz bazowy', line=dict(color='#0366d6', width=2)))
    fig_line.add_trace(go.Scatter(y=best_path, mode='lines', name='Optymistycznie (95%)', line=dict(color='#28a745', dash='dot')))
    fig_line.add_trace(go.Scatter(y=worst_path, mode='lines', name='Pesymistycznie (5%)', line=dict(color='#d73a49', dash='dot')))
    
    fig_line.update_layout(xaxis_title="Dni z rzędu", yaxis_title="Wartość portfela", height=350, margin=dict(t=20))
    st.plotly_chart(fig_line, use_container_width=True)
    
    col_m1, col_m2, col_m3 = st.columns(3)

    col_m1.metric("Max Drawdown", f"{round(max_drawdown*100, 2)}%")
    col_m2.metric("Sortino Ratio", f"{round(sortino_ratio, 2)}")
    col_m3.metric("Skewness", f"{round(skewness_val, 2)}")

    st.metric("Kurtosis", f"{round(kurt_val, 2)}")
    
    # PRZYWRÓCONE WYKRESY Z ORYGINAŁU
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


# ==========================================
# ZAKŁADKA 4: POBIERANIE PLIKÓW 
# ==========================================
elif page == "Pobierz pliki":
    st.title("Pobieranie plików i zasobów")
    st.markdown("Wygeneruj raport i **prawdziwe dane historyczne** dla spółek wybranych w Kalkulatorze.")
    
    if len(st.session_state.selected_tickers) > 0:
        st.info(f"Aktualnie do portfela wybrano: **{', '.join(st.session_state.selected_tickers)}**")
    else:
        st.info("Brak wybranych spółek.")
    
    # PRZYWRÓCONY CAŁY BLOK POBIERANIA CSV
    st.markdown("### Krok 1: Pobierz surowe dane z giełdy")
    st.markdown("Kliknij poniżej, aby pobrać faktyczne, codzienne stopy zwrotu z ostatniego roku dla wybranych spółek.")
    
    if st.button("Pobierz i przygotuj dane z Giełdy", type="primary"):
        if len(st.session_state.selected_tickers) > 0:
            with st.spinner("Łączenie z rynkiem finansowym i generowanie arkusza..."):
                try:
                    data = yf.download(st.session_state.selected_tickers, period="1y", progress=False)
                    
                    if 'Adj Close' in data:
                        prices = data['Adj Close']
                    elif 'Close' in data:
                        prices = data['Close']
                    else:
                        raise ValueError("Brak odpowiednich danych cenowych w odpowiedzi z giełdy.")

                    if isinstance(prices, pd.Series):
                        prices = prices.to_frame(name=st.session_state.selected_tickers[0])
                        
                    returns_df = prices.pct_change().dropna()
                    
                    if returns_df.empty:
                        raise ValueError("Zwrócono puste dane. Sprawdź poprawność tickerów.")
                    
                    csv = returns_df.to_csv(index=True).encode('utf-8')
                    
                    st.success("Dane pobrane poprawnie! Arkusz jest gotowy do zapisu.")
                    st.download_button(
                        label="📥 Zapisz plik CSV z historią stóp zwrotu",
                        file_name="prawdziwa_historia_zwrotow.csv",
                        mime="text/csv",
                        data=csv
                    )
                except Exception as e:
                    st.error(f"Nie udało się wygenerować danych: {e}. Spróbuj wybrać inne aktywa.")
        else:
            st.warning("Najpierw musisz dodać jakieś akcje w zakładce Kalkulator Ryzyka!")
    
    st.markdown("---")
    st.markdown("### Krok 2: Konfiguracja silnika (JSON)")
    
    # NAPRAWIONE: Zamiast "makiety" generujemy raport z faktycznych wyliczeń usera
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
            label="📥 Pobierz raport bezpieczeństwa (JSON)",
            file_name="risk_report.json",
            mime="application/json",
            data=json_string
        )
    else:
        st.info("Przejdź najpierw do zakładki 'Doradca Portfelowy' i pozwól systemowi przeliczyć wagi, aby wygenerować Twój unikalny raport w formacie JSON.")
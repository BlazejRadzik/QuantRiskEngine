# data/ingestor.py
import yfinance as yf
import pandas as pd
import requests
from data.db_manager import DBManager
from datetime import datetime, timedelta

class DataIngestor:
    def __init__(self, tickers: list):
        self.tickers = [t.strip().upper() for t in tickers]
        self.db = DBManager()
        # Tutaj docelowo wstawisz klucz do profesjonalnego API z .env
        self.tiingo_api_key = "TWOJ_KLUCZ_TIINGO_LUB_NONE" 

    def _fetch_from_tiingo(self, ticker, start_date):
        """Metoda pobierania z profesjonalnego API (Przykładowa struktura)."""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Token {self.tiingo_api_key}'}
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={start_date}"
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.normalize()
        df.set_index('date', inplace=True)
        return df['adjClose']

    def _fetch_from_yfinance(self, ticker, period="2y"):
        """Fallback do starego dobrego yfinance."""
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError("Empty data from yfinance")
            
        if isinstance(df.columns, pd.MultiIndex):
            col = ('Close', ticker) if ('Close', ticker) in df.columns else df.columns[0]
            s = df[col].copy()
        else:
            s = df['Close'].copy()
            
        s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
        return s

    def fetch_historical_data(self, period="2y") -> pd.DataFrame:
        all_series = {}
        
        # Uproszczone wyliczenie daty początkowej dla Cache
        days = 365 * int(period.replace('y', ''))
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        print(f"\n[DATA LAYER] Starting retrieval for: {self.tickers}")
        
        for t in self.tickers:
            # 1. Próba odczytu z lokalnej bazy danych (Cache hit)
            s = self.db.load_data(t, start_date)
            
            # Sprawdzamy, czy mamy wystarczającą ilość danych w bazie (np. minimum 250 dni handlowych na rok)
            if not s.empty and len(s) > (days * 0.65): 
                all_series[t] = s
                print(f"  ⚡ {t}: Loaded from LOCAL CACHE ({len(s)} rows)")
                continue
                
            # 2. Cache Miss - pobieramy z sieci (Fallback Pattern)
            print(f"  🌐 {t}: Cache miss. Fetching from external APIs...")
            try:
                # W produkcji tu odkomentujesz Tiingo/Alpha Vantage
                # s = self._fetch_from_tiingo(t, start_date)
                
                # Zostawiamy yfinance jako testowy mechanizm
                s = self._fetch_from_yfinance(t, period)
                
                all_series[t] = s
                # 3. Zapis do bazy (zapamiętanie na przyszłość)
                self.db.save_data(t, s)
                print(f"  ✅ {t}: Downloaded & Cached successfully.")
                
            except Exception as e:
                print(f"  ❌ {t}: ALL APIs FAILED -> {str(e)}")

        if not all_series:
            return None

        # Łączenie w DataFrame i czyszczenie braków tak jak miałeś w oryginale
        final_df = pd.DataFrame(all_series).dropna()
        print(f"[DATA LAYER] Final Overlap: {len(final_df)} overlapping trading days.")
        
        return final_df
import yfinance as yf
import pandas as pd
import numpy as np

class DataIngestor:
    def __init__(self, tickers: list):
        self.tickers = [t.strip().upper() for t in tickers]

    def fetch_historical_data(self, period="2y"):
        all_series = {}
        print(f"\n[DEBUG] Starting download for: {self.tickers}")
        
        for t in self.tickers:
            try:
                # Pobieramy dane z wymuszonym auto_adjust
                df = yf.download(t, period=period, interval="1d", progress=False, auto_adjust=True)
                
                if not df.empty:
                    # Szukamy kolumny 'Close' (po auto_adjust to jest nasze Adj Close)
                    # Sprawdzamy czy to nie MultiIndex
                    if isinstance(df.columns, pd.MultiIndex):
                        # Jeśli yfinance zwrócił poziomy, bierzemy Close dla konkretnego tickera
                        col = ('Close', t) if ('Close', t) in df.columns else df.columns[0]
                        s = df[col].copy()
                    else:
                        s = df['Close'].copy()
                    
                    # TOTALNA NORMALIZACJA INDEKSU
                    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
                    
                    all_series[t] = s
                    print(f"  ✅ {t}: Success ({len(s)} rows)")
                else:
                    print(f"  ⚠️ {t}: Empty DataFrame from API")
            except Exception as e:
                print(f"  ❌ {t}: Error -> {str(e)}")

        if not all_series:
            return None

        # Łączymy w DataFrame
        final_df = pd.DataFrame(all_series)
        
        # Usuwamy braki - jeśli nadal będzie 0, to znaczy że daty się kompletnie nie pokrywają
        final_df = final_df.dropna()
        
        print(f"[DEBUG] Final Overlap: {len(final_df)} days.")
        return final_df 
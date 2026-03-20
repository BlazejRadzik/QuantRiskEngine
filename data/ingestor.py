import yfinance as yf
import pandas as pd
from typing import List

def fetch_data(tickers: List[str], period: str = "2y") -> pd.DataFrame:
    """
    Pobiera historyczne ceny zamknięcia z Yahoo Finance i oblicza dzienne stopy zwrotu.
    """
    if not tickers:
        return pd.DataFrame()
        
    # Pobieranie danych (Close prices)
    data = yf.download(tickers, period=period, progress=False)['Close']
    
    # Obsługa przypadku, gdy przekazano tylko jeden ticker (yfinance zwraca wtedy Series)
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
        
    # Obliczenie dziennych, logarytmicznych stóp zwrotu (lepsze do modeli ryzyka)
    import numpy as np
    returns = np.log(data / data.shift(1)).dropna()
    
    return returns
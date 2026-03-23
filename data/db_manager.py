import sqlite3
import pandas as pd
import os
from datetime import datetime

class DBManager:
    def __init__(self, db_name="market_data.db"):
        self.db_path = os.path.join(os.path.dirname(__file__), db_name)
        self.init_db()

    def init_db(self):
        """Tworzy tabelę, jeśli jeszcze nie istnieje. Klucz główny zapobiega duplikatom."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_prices (
                    ticker TEXT,
                    date TIMESTAMP,
                    close REAL,
                    PRIMARY KEY (ticker, date)
                )
            ''')
            conn.commit()

    def save_data(self, ticker: str, df: pd.DataFrame):
        """Zapisuje nowy DataFrame do bazy SQL używając upsert (INSERT OR IGNORE)."""
        if df.empty: return

        records = [(ticker, str(index.date()), float(row)) for index, row in df.items()]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT OR IGNORE INTO daily_prices (ticker, date, close)
                VALUES (?, ?, ?)
            ''', records)
            conn.commit()

    def load_data(self, ticker: str, start_date: str) -> pd.Series:
        """Ładuje dane z lokalnej bazy SQL i zwraca jako Pandas Series."""
        with sqlite3.connect(self.db_path) as conn:
            query = f"SELECT date, close FROM daily_prices WHERE ticker = '{ticker}' AND date >= '{start_date}' ORDER BY date ASC"
            df = pd.read_sql_query(query, conn, index_col="date", parse_dates=["date"])

        if not df.empty:
            return df['close']
        return pd.Series(dtype=float)

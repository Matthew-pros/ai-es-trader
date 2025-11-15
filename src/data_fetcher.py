import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
from .utils import iso_to_timestamp, utc_to_est

# Massive poskytuje data pod symbolem "ES" (continuous future)
MASSIVE_SYMBOL = "ES"
EST = pytz.timezone('America/New_York')

@st.cache_data(ttl=60)  # cache na 1 minutu – zabraňuje opakovanému volání během reloadu
def fetch_es_data(days: int = 7) -> pd.DataFrame:
    """
    Stáhne minutová OHLCV data z Massive REST API.
    Dokumentace: https://massive.com/docs/rest/quickstart#understanding-the-api-response
    """
    api_key = st.secrets.get("MASSIVE_API_KEY")
    if not api_key or api_key == "VLOŽTE_TADY_SVŮJ_MASSIVE_KEY":
        st.error("❌ Massive API key není nastaven. Zkontrolujte soubor `.streamlit/secrets.toml`.")
        return pd.DataFrame()

    # Výpočet časového intervalu v UTC (Massive očekává ISO8601 v UTC)
    end_utc = datetime.utcnow()
    start_utc = end_utc - timedelta(days=days)

    url = f"https://api.massive.io/v1/quotes/{MASSIVE_SYMBOL}/bars"

    params = {
        "apikey": api_key,
        "start": start_utc.isoformat() + "Z",
        "end":   end_utc.isoformat()   + "Z",
        "granularity": "minute",               # 1‑minuty
        "adjusted": "false"
    }

    try:
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()

        if "bars" not in payload or not payload["bars"]:
            st.warning("⚠️ Massive API nevrátila žádná data pro požadované období.")
            return pd.DataFrame()

        # Převod na DataFrame – pole `bars` má strukturu dle dokumentace
        df = pd.DataFrame(payload["bars"])

        # Příklad položek v `bars` (z dokumentace):
        # {
        #   "t": "2025-04-27T13:45:00Z",   # timestamp (ISO‑8601)
        #   "o": 6725.0, "h": 6728.5, "l": 6722.0, "c": 6727.0,
        #   "v": 1245.0, "n": 15               # n = počet obchodů v tomto intervalu
        # }

        # Převod timestampu
        df["timestamp_utc"] = df["t"].apply(iso_to_timestamp)
        df["timestamp_est"] = df["timestamp_utc"].apply(utc_to_est)

        # Přejmenování sloupců na jednotný název, který používá zbytek kódu
        df.rename(columns={
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume"
        }, inplace=True)

        # Dodatečné sloupce pro filtrování
        df["date"] = df["timestamp_est"].dt.date
        df["time_est"] = df["timestamp_est"].dt.time

        # Výběr jen potřebných sloupců a uspořádání
        df = df[[
            "timestamp_utc", "timestamp_est", "date", "time_est",
            "open", "high", "low", "close", "volume"
        ]]

        return df.sort_values("timestamp_utc").reset_index(drop=True)

    except requests.exceptions.HTTPError as http_err:
        st.error(f"❌ HTTP error při volání Massive API: {http_err}")
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        st.error("❌ Časový limit při komunikaci s Massive API – zkuste to později.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Neočekávaná chyba při zpracování Massive dat: {e}")
        return pd.DataFrame()

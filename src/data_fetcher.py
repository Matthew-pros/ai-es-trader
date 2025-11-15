import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import pytz
from .utils import convert_ms_to_datetime

# Používáme 'X:ES' pro neustále se obnovující futures kontrakt ES
POLYGON_SYMBOL = "X:ES" 
EST_TIMEZONE = pytz.timezone('America/New_York')

@st.cache_data(ttl=60) # Cache na 1 minutu, aby se data neaktualizovala příliš často
def fetch_realtime_es_data(days=6):
    """
    Stáhne reálná minutová data pro ES z Polygon API.
    ROBUSTNÍ VERZE: s kontrolou chyb a jasným hlášením.
    """
    api_key = st.secrets["POLYGON_API_KEY"]
    if not api_key or api_key == "VÁŠ_KLÍČ_ZDE":
        st.error("❌ Chyba: Polygon API klíč není nastaven. Zkontrolujte soubor `.streamlit/secrets.toml`.")
        return pd.DataFrame()

    # Cílové časové období
    end_date_utc = datetime.now(timezone.utc)
    start_date_utc = end_date_utc - timedelta(days=days)
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{POLYGON_SYMBOL}/range/1/minute/{start_date_utc.strftime('%Y-%m-%d')}/{end_date_utc.strftime('%Y-%m-%d')}"

    params = {
        "apikey": api_key,
        "adjusted": "false",
        "sort": "asc"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Vyvolá výjimku pro HTTP chyby (4xx nebo 5xx)

        data = response.json()
        
        if 'results' not in data or not data['results']:
            st.warning("⚠️ Polygon API vrátilo prázdná data. Možná je mimo burzovní hodiny.")
            return pd.DataFrame()

        df = pd.DataFrame(data['results'])
        
        # Převedení časových razítek a sloupců
        df['timestamp_utc'] = convert_ms_to_datetime(df['t'])
        df['timestamp_est'] = df['timestamp_utc'].dt.tz_convert(EST_TIMEZONE)
        
        df.rename(columns={
            'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'
        }, inplace=True)
        
        # Přidání sloupců pro snadnější filtrování
        df['date'] = df['timestamp_est'].dt.date
        df['time_est'] = df['timestamp_est'].dt.time
        
        return df[['timestamp_utc', 'timestamp_est', 'date', 'time_est', 'open', 'high', 'low', 'close', 'volume']]

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Chyba při komunikaci s Polygon API: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Neočekávaná chyba při zpracování dat: {e}")
        return pd.DataFrame()

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def get_trading_day(date_str: str) -> bool:
    """Zkontroluje, zda je daný den pracovní den."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        # Zjednodušení: víkendy jsou neobchodní dny
        return date_obj.weekday() < 5
    except ValueError:
        return False

@st.cache_data(ttl=3600)
def convert_ms_to_datetime(ms):
    """Převede milisekundy na datetime objekt s časovou zónou UTC."""
    return pd.to_datetime(ms, unit='ms', utc=True)

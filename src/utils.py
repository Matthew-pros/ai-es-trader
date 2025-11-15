import pandas as pd
from datetime import datetime
import pytz

EST = pytz.timezone('America/New_York')
UTC = pytz.utc

def utc_to_est(ts: pd.Timestamp) -> pd.Timestamp:
    """Převede UTC timestamp na US/Eastern (EST/EDT) a vrátí časově‑značený objekt."""
    return ts.tz_convert(EST)

def iso_to_timestamp(iso_str: str) -> pd.Timestamp:
    """Převede ISO‑8601 řetězec (např. '2025-04-27T13:45:00Z') na tz‑aware Timestamp v UTC."""
    return pd.to_datetime(iso_str).tz_localize('UTC')

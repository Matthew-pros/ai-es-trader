import pandas as pd
import pytz

EST_TIMEZONE = pytz.timezone('America/New_York')

def calculate_ib_for_day(data: pd.DataFrame, target_date: pd.Timestamp) -> dict:
    """
    Spočítá Initial Balance (IB) pro daný den.
    Vrací slovník s detaily nebo None, pokud data nejsou k dispozici.
    """
    if data.empty:
        return None

    day_data = data[data['date'] == target_date.date()].copy()
    if day_data.empty:
        return None

    # Filtrování na časové okno 8:00 - 8:15 EST včetně
    ib_window_start = pd.Timestamp(year=target_date.year, month=target_date.month, day=target_date.day, hour=8, minute=0, tzinfo=EST_TIMEZONE)
    ib_window_end = pd.Timestamp(year=target_date.year, month=target_date.month, day=target_date.day, hour=8, minute=15, second=59, tzinfo=EST_TIMEZONE)

    ib_data = day_data[
        (day_data['timestamp_est'] >= ib_window_start) &
        (day_data['timestamp_est'] <= ib_window_end)
    ]
    
    if ib_data.empty:
        # Někdy nemusí být data přesně v tomto okně, zkusíme lenientnější přístup
        morning_data = day_data[day_data['timestamp_est'].dt.hour == 8]
        if morning_data.empty:
            return None
        ib_data = morning_data

    ib_high = round(ib_data['high'].max(), 2)
    ib_low = round(ib_data['low'].min(), 2)
    ib_range = round(ib_high - ib_low, 2)
    ib_mid = round((ib_high + ib_low) / 2, 2)

    return {
        "high": ib_high,
        "low": ib_low,
        "range": ib_range,
        "mid": ib_mid,
        "valid": True
    }

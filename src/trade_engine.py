import pandas as pd
import numpy as np
from .ib_calculator import calculate_ib_for_day

def get_magnet_levels(price: float) -> list[float]:
    """Generuje magnetické úrovně (násobky 50) kolem aktuální ceny."""
    base = round(price / 50) * 50
    return sorted([base - 100, base - 50, base, base + 50, base + 100])

def calculate_daily_bias(data_for_day: pd.DataFrame) -> int:
    """
    Vypočítá jednoduchý bias skóre na základě předešlého dne a volume.
    -100 (silný short) až +100 (silný long)
    """
    if len(data_for_day) < 390: # Méně než 1 hodina dat, nespolehlivé
        return 0
        
    open_price = data_for_day.iloc[0]['open']
    close_price = data_for_day.iloc[-1]['close']
    
    # Bias na základě denní změny
    daily_change_pct = (close_price - open_price) / open_price * 100
    
    # Bias na základě objemu (jednoduché přiblížení)
    avg_vol = data_for_day['volume'].mean()
    last_hour_vol = data_for_day.tail(60)['volume'].mean()
    volume_bias = 10 if last_hour_vol > avg_vol * 1.2 else -10 if last_hour_vol < avg_vol * 0.8 else 0
    
    total_bias = (daily_change_pct * 2) + volume_bias
    return np.clip(total_bias, -100, 100)

def generate_recommendations(data: pd.DataFrame) -> pd.DataFrame:
    """
    Generuje zpětnou analýzu a doporučení pro posledních 5 obchodních dní.
    """
    recommendations = []
    
    # Získání posledních 5 jedinečných obchodních dní
    trading_days = sorted(data['date'].unique(), reverse=True)[:5]

    for day in trading_days:
        day_data = data[data['date'] == day]
        
        # Výpočet IB
        ib_info = calculate_ib_for_day(data, pd.Timestamp(day))
        if not ib_info or not ib_info['valid']:
            continue
            
        # Rozhodovací logika
        bias = calculate_daily_bias(day_data)
        action = "BUY" if bias > 0 else "SELL"
        
        close_price = day_data['close'].iloc[-1]
        entry_price = ib_info['high'] + 0.25 if action == "BUY" else ib_info['low'] - 0.25
        
        # Target: nejbližší magnet ve směru obchodu
        magnets = get_magnet_levels(close_price)
        if action == "BUY":
            tp = next(m for m in sorted(magnets) if m > entry_price)
            sl = ib_info['low'] - 5
        else: # SELL
            tp = next(m for m in sorted(magnets, reverse=True) if m < entry_price)
            sl = ib_info['high'] + 5

        # Vyhodnocení výsledku (zjednodušené: zda cena dosáhla TP dříve než SL)
        # Pro přehlednost bereme v úvahu pouze konečnou cenu dne
        result = "WIN" if (action == "BUY" and close_price >= tp - 5) or (action == "SELL" and close_price <= tp + 5) else "LOSS"
        
        rrr = round(abs(tp - entry_price) / abs(entry_price - sl), 2) if (entry_price - sl) != 0 else 0

        recommendations.append({
            "Date": day.strftime("%Y-%m-%d"),
            "Action": action,
            "Bias": bias,
            "IB_High": ib_info['high'],
            "IB_Low": ib_info['low'],
            "Entry": entry_price,
            "Target (TP)": tp,
            "Stop Loss (SL)": sl,
            "Close": close_price,
            "RRR": rrr,
            "Result": result
        })

    return pd.DataFrame(recommendations)

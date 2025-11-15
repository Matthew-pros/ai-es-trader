import streamlit as st
import pandas as pd
from datetime import datetime
from src.data_fetcher import fetch_realtime_es_data
from src.trade_engine import generate_recommendations, get_magnet_levels

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(
    page_title="AI ES Trader",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 AI-Powered S&P 500 (ES) Trading Engine")
st.markdown("**Reálná data | Přesný Initial Balance | Produkční systém**")

# --- POBOČNÍ PANEL ---
with st.sidebar:
    st.header("⚙️ Nastavení")
    
    # Tlačítko pro načtení dat
    if st.button("🔄 Načíst nejnovější data", type="primary"):
        if 'data' in st.session_state:
            del st.session_state['data']
        st.rerun()

    st.markdown("---")
    st.markdown("**Tento systém obchoduje:**")
    st.info("""
    - Breakout z **Initial Balance (8:00-8:15 EST)**
    - Cílí na nejbližší **magnetickou úroveň** (násobky 50)
    - Používá denní **bias analýzu** pro směr obchodu
    - Maximální **riziko = 1-2%** z kapitálu
    """)

# --- HLAVNÍ TĚLO APLIKACE ---
# Načtení dat (s použitím cache)
if 'data' not in st.session_state:
    with st.spinner("📡 Stahuji reálná data z Polygon.io..."):
        es_data = fetch_realtime_es_data(days=8)
        if not es_data.empty:
            st.session_state.data = es_data
            st.success(f"✅ Data úspěšně načtena ({len(es_data)} záznamů)")
        else:
            st.error("❌ Nepodařilo se načíst data. Zkontrolujte API klíč a síťové připojení.")
            st.stop()
else:
    es_data = st.session_state.data

if es_data.empty:
    st.stop()

# Zobrazení klíčových metrik
latest_bar = es_data.iloc[-1]
prev_bar = es_data.iloc[-2]
current_price = latest_bar['close']
price_change = current_price - prev_bar['close']

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Aktuální cena ES", f"{current_price:.2f}", f"{price_change:+.2f}")
with col2:
    st.metric("🕐 Poslední update", latest_bar['timestamp_est'].strftime("%H:%M:%S EST"))
with col3:
    st.metric("💎 Objem", f"{latest_bar['volume']:,}")

st.markdown("---")

# Generování a zobrazení doporučení
with st.spinner("🧠 Analyzuji trh a generuji signály..."):
    recommendations_df = generate_recommendations(es_data)

if not recommendations_df.empty:
    st.subheader("📈 Zpětná analýza a doporučení (posledních 5 dní)")
    
    # Zvýraznění WIN/LOSS
    styled_df = recommendations_df.style.applymap(
        lambda x: 'color: green; font-weight: bold' if x == 'WIN' else 'color: red; font-weight: bold',
        subset=['Result']
    )
    st.dataframe(styled_df, use_container_width=True)

    # Statistiky
    win_rate = (recommendations_df['Result'] == 'WIN').mean()
    avg_rrr = recommendations_df['RRR'].mean()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🎯 Win Rate", f"{win_rate:.1%}")
    with col2:
        st.metric("📊 Průměrné R:R", f"{avg_rrr:.2f}:1")

    # Dnešní doporučení
    today_rec = recommendations_df.iloc[0]
    with st.expander("🎯 Dnešní doporučení (detail)", expanded=True):
        st.write(f"""
        **Datum:** {today_rec['Date']}  
        **Denní Bias:** `{today_rec['Bias']}` (silnější {'🟢 LONG' if today_rec['Bias'] > 0 else '🔴 SHORT'})
        ---
        **Doporučená akce:** `{today_rec['Action']}`
        - **Vstup:** nad `{today_rec['Entry']}` (pokud BUY) / pod `{today_rec['Entry']}` (pokud SELL)
        - **Cíl (TP):** `{today_rec['Target (TP)']}`
        - **Stop Loss (SL):** `{today_rec['Stop Loss (SL)']}`
        - **Riziko/Výnos (R:R):** `{today_rec['RRR']}:1`
        """)

# Zobrazení magnetických úrovní
st.subheader("🧲 Magnetické úrovně (násobky 50)")
magnets = get_magnet_levels(current_price)
magnet_labels = [f"**{m}**" if abs(m - current_price) < 25 else str(m) for m in magnets]
st.write(" | ".join(magnet_labels))
st.caption("Cena má tendenci se zastavovat a otáčet kolem těchto hladin.")

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands, KeltnerChannel

# إعدادات الواجهة
st.set_page_config(page_title="مساعد المضاربة الآلي", page_icon="🤖", layout="wide")
st.title("🤖 مساعد المضاربة الآلي (V4.0 - تتبع الأداء والنتائج)")

# إعدادات التيليجرام
st.sidebar.header("⚙️ إعدادات التيليجرام")
tele_token = st.sidebar.text_input("Bot Token", type="password")
tele_chat = st.sidebar.text_input("Chat ID")

# ملفات الحفظ
TRADES_FILE = "active_trades.csv"
HISTORY_FILE = "trade_history.csv"
tickers = ['2222.SR', '1180.SR', '1211.SR', '7204.SR', '1120.SR', '1010.SR', '2010.SR', '4001.SR']

def send_telegram(msg):
    if tele_token and tele_chat:
        url = f"https://api.telegram.org/bot{tele_token}/sendMessage"
        requests.post(url, json={"chat_id": tele_chat, "text": msg, "parse_mode": "Markdown"})

def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file)
    if file == TRADES_FILE:
        return pd.DataFrame(columns=['Ticker', 'Entry', 'SL', 'TP', 'Date'])
    return pd.DataFrame(columns=['Ticker', 'Entry', 'Exit_Price', 'Result', 'Return_%', 'Date'])

def save_data(df, file):
    df.to_csv(file, index=False)

def show_dashboard():
    st.subheader("📊 لوحة أداء الاستراتيجية")
    history = load_data(HISTORY_FILE)
    if history.empty:
        st.info("لا يوجد سجل للصفقات السابقة بعد. ابدأ بالتداول لإنشاء الإحصائيات.")
        return
    wins = len(history[history['Result'] == 'Win'])
    losses = len(history[history['Result'] == 'Loss'])
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    total_return = history['Return_%'].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 صفقات ناجحة", wins)
    col2.metric("🔴 صفقات خاسرة", losses)
    col3.metric("📈 نسبة النجاح", f"{win_rate:.1f}%")
    col4.metric("💰 صافي العائد الإجمالي", f"{total_return:.2f}%", delta=f"{total_return:.2f}%", delta_color="inverse" if total_return < 0 else "normal")

def scan_market():
    st.subheader("1. مسح السوق للبحث عن فرص جديدة")
    trades = load_data(TRADES_FILE)
    if st.button("🔍 ابدأ المسح الآن", use_container_width=True):
        with st.spinner("جاري البحث عن الانفجارات السعربية..."):
            for ticker in tickers:
                try:
                    data = yf.download(ticker, period="1y", interval="1d", progress=False)
                    if data.empty: continue
                    
                    data['EMA10'] = EMAIndicator(data['Close'], window=10).ema_indicator()
                    data['EMA20'] = EMAIndicator(data['Close'], window=20).ema_indicator()
                    data['RSI14'] = RSIIndicator(data['Close'], window=14).rsi()
                    data['ATR14'] = AverageTrueRange(data['High'], data['Low'], data['Close'], window=14).average_true_range()
                    
                    bb = BollingerBands(data['Close'], window=20, window_dev=2)
                    data['BBL'] = bb.bollinger_lband()
                    data['BBU'] = bb.bollinger_hband()
                    
                    kc = KeltnerChannel(data['High'], data['Low'], data['Close'], window=20, window_atr=2)
                    data['KCL'] = kc.keltner_channel_lband()
                    data['KCU'] = kc.keltner_channel_hband()
                    
                    data.dropna(inplace=True)
                    data['Res20'] = data['High'].rolling(window=20).max().shift(1)
                    data['Avg_Vol'] = data['Volume'].rolling(window=20).mean().shift(1)
                    
                    last = data.iloc[-1]
                    squeeze = (last['BBL'] > last['KCL']) and (last['BBU'] < last['KCU'])
                    breakout = last['Close'] > last['Res20']
                    rvol = last['Volume'] / last['Avg_Vol'] if last['Avg_Vol'] > 0 else 0
                    
                    if last['EMA10'] > last['EMA20'] and last['RSI14'] > 50 and squeeze and breakout and rvol >= 1.5:
                        if ticker not in trades['Ticker'].values:
                            entry = last['Close']
                            sl = entry - (2 * last['ATR14'])
                            tp = entry + (4 * last['ATR14'])
                            date = datetime.now().strftime('%Y/%m/%d')
                            
                            new_trade = pd.DataFrame([[ticker, entry, sl, tp, date]], columns=['Ticker', 'Entry', 'SL', 'TP', 'Date'])
                            trades = pd.concat([trades, new_trade], ignore_index=True)
                            save_data(trades, TRADES_FILE)
                            
                            msg = f"🚀 *إشارة دخول (شراء)*\n🏢 السهم: {ticker.replace('.SR','')}\n💰 الدخول: {entry:.2f}\n🛑 الوقف: {sl:.2f}\n🎯 الهدف: {tp:.2f}"
                            send_telegram(msg)
                            st.success(f"تم العثور على فرصة لـ {ticker} وتم الدخول!")
                except Exception as e:
                    pass

def monitor_trades():
    st.subheader("2. مراقبة الصفقات المفتوحة")
    trades = load_data(TRADES_FILE)
    history = load_data(HISTORY_FILE)
    if trades.empty:
        st.info("لا توجد صفقات مفتوحة حالياً.")
        return
    st.dataframe(trades, use_container_width=True)
    if st.button("📡 فحص الصفقات المفتوحة الآن", use_container_width=True):
        with st.spinner("جاري فحص أسعار الصفقات المفتوحة..."):
            for i, trade in trades.iterrows():
                ticker = trade['Ticker']
                try:
                    live_data = yf.download(ticker, period="1d", interval="1m", progress=False)
                    if live_data.empty: continue
                    current_price = live_data['Close'].iloc[-1]
                    entry_date = datetime.strptime(trade['Date'], '%Y/%m/%d')
                    days_passed = (datetime.now() - entry_date).days
                    hit_tp = current_price >= trade['TP']
                    hit_sl = current_price <= trade['SL']
                    time_out = days_passed >= 7 
                    exit_price = 0
                    result = ""
                    return_pct = 0
                    if hit_tp:
                        exit_price = trade['TP']
                        result = "Win"
                        return_pct = ((exit_price - trade['Entry']) / trade['Entry']) * 100
                        msg = f"🎯 *هدف تحقق (بيع)*\n🏢 السهم: {ticker.replace('.SR','')}\n💰 الربح: +{return_pct:.2f}%"
                        send_telegram(msg)
                        st.success(f"تم تحقيق الهدف لـ {ticker}!")
                    elif hit_sl:
                        exit_price = trade['SL']
                        result = "Loss"
                        return_pct = ((exit_price - trade['Entry']) / trade['Entry']) * 100
                        msg = f"🛑 *ضرب وقف الخسارة (بيع)*\n🏢 السهم: {ticker.replace('.SR','')}\n💰 الخسارة: {return_pct:.2f}%"
                        send_telegram(msg)
                        st.warning(f"تم ضرب وقف الخسارة لـ {ticker}.")
                    elif time_out:
                        exit_price = current_price
                        result = "Win" if current_price >= trade['Entry'] else "Loss"
                        return_pct = ((exit_price - trade['Entry']) / trade['Entry']) * 100
                        msg = f"⏳ *انتهاء الوقت (بيع)*\n🏢 السهم: {ticker.replace('.SR','')}\n💰 العائد: {return_pct:.2f}%"
                        send_telegram(msg)
                        st.info(f"تم إغلاق {ticker} لانتهاء المدة الزمنية.")
                    if hit_tp or hit_sl or time_out:
                        new_hist = pd.DataFrame([[ticker, trade['Entry'], exit_price, result, return_pct, trade['Date']]], columns=['Ticker', 'Entry', 'Exit_Price', 'Result', 'Return_%', 'Date'])
                        history = pd.concat([history, new_hist], ignore_index=True)
                        save_data(history, HISTORY_FILE)
                        trades = trades.drop(i)
                        save_data(trades, TRADES_FILE)
                except:
                    pass

show_dashboard()
st.markdown("---")
scan_market()
st.markdown("---")
monitor_trades()

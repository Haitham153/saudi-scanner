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
st.title("🤖 رادار السوق السعودي الشامل (V8.0 - القائمة الكاملة)")

# إعدادات التيليجرام
st.sidebar.header("⚙️ إعدادات التيليجرام")
tele_token = st.sidebar.text_input("Bot Token", type="password")
tele_chat = st.sidebar.text_input("Chat ID")

# ملفات الحفظ
TRADES_FILE = "active_trades.csv"
HISTORY_FILE = "trade_history.csv"

# القائمة الكاملة لأسهم السوق السعودي (مقدمة من المستخدم)
tickers = [
    '1010.SR', '1020.SR', '1030.SR', '1050.SR', '1060.SR', '1080.SR', '1111.SR', '1120.SR', '1140.SR', '1150.SR', '1180.SR', '1182.SR', '1183.SR',
    '1201.SR', '1202.SR', '1210.SR', '1211.SR', '1212.SR', '1213.SR', '1214.SR',
    '1301.SR', '1302.SR', '1303.SR', '1304.SR', '1320.SR',
    '1810.SR', '1820.SR', '1830.SR', '1831.SR', '1832.SR', '1833.SR', '1834.SR',
    '2001.SR', '2002.SR', '2010.SR', '2020.SR', '2030.SR', '2040.SR', '2050.SR', '2060.SR', '2070.SR', '2080.SR', '2081.SR', '2082.SR', '2083.SR', '2090.SR',
    '2100.SR', '2110.SR', '2120.SR', '2130.SR', '2140.SR', '2150.SR', '2160.SR', '2170.SR', '2180.SR', '2190.SR', '2200.SR', '2210.SR', '2220.SR', '2222.SR', '2223.SR', '2230.SR', '2240.SR', '2250.SR', '2270.SR', '2280.SR', '2281.SR', '2282.SR', '2283.SR', '2284.SR', '2285.SR', '2290.SR',
    '2300.SR', '2310.SR', '2320.SR', '2330.SR', '2340.SR', '2350.SR', '2360.SR', '2370.SR', '2380.SR', '2381.SR', '2382.SR',
    '3001.SR', '3002.SR', '3003.SR', '3004.SR', '3005.SR', '3010.SR', '3020.SR', '3030.SR', '3040.SR', '3050.SR', '3060.SR', '3080.SR', '3090.SR',
    '4001.SR', '4002.SR', '4003.SR', '4004.SR', '4005.SR', '4006.SR', '4007.SR', '4009.SR', '4010.SR', '4011.SR', '4012.SR', '4013.SR', '4014.SR', '4015.SR',
    '4020.SR', '4030.SR', '4031.SR', '4040.SR', '4050.SR', '4061.SR', '4070.SR', '4080.SR', '4090.SR',
    '4100.SR', '4110.SR', '4130.SR', '4140.SR', '4150.SR', '4160.SR', '4161.SR', '4162.SR', '4163.SR', '4164.SR', '4170.SR', '4180.SR', '4190.SR', '4191.SR', '4192.SR',
    '4200.SR', '4210.SR', '4220.SR', '4230.SR', '4240.SR', '4250.SR', '4260.SR', '4270.SR', '4280.SR', '4290.SR', '4291.SR', '4292.SR',
    '4300.SR', '4310.SR', '4320.SR', '4321.SR', '4322.SR', '4323.SR',
    '5110.SR',
    '6001.SR', '6002.SR', '6004.SR', '6010.SR', '6012.SR', '6013.SR', '6014.SR', '6015.SR',
    '7010.SR', '7200.SR', '7201.SR', '7202.SR', '7203.SR', '7210.SR', '7220.SR', '7221.SR', '7230.SR', '7231.SR', '7232.SR',
    '8010.SR', '8020.SR', '8030.SR', '8040.SR', '8050.SR', '8060.SR', '8070.SR', '8100.SR', '8120.SR', '8150.SR', '8160.SR', '8170.SR', '8180.SR', '8190.SR', '8200.SR', '8210.SR', '8230.SR', '8240.SR', '8250.SR', '8260.SR', '8270.SR', '8280.SR', '8300.SR', '8310.SR', '8311.SR', '8312.SR'
]

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
    st.subheader(f"1. مسح السوق ({len(tickers)} سهم)")
    trades = load_data(TRADES_FILE)
    if st.button("🔍 ابدأ المسح الشامل للسوق الآن", use_container_width=True, type="primary"):
        with st.spinner(f"جاري فحص {len(tickers)} سهم... قد يستغرق هذا 3 إلى 5 دقائق. يرجى عدم إغلاق الصفحة."):
            for ticker in tickers:
                try:
                    data = yf.download(ticker, period="1y", interval="1d", progress=False, threads=False)
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
                            st.success(f"🎯 تم العثور على فرقة لـ {ticker.replace('.SR','')} وتم الدخول!")
                except Exception as e:
                    pass
        st.success("✅ اكتمل المسح الشامل لجميع أسهم السوق السعودي.")

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
                    live_data = yf.download(ticker, period="1d", interval="1m", progress=False, threads=False)
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

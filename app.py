import streamlit as st
import pandas as pd
import yfinance as yf
import ta

st.set_page_config(page_title="Seif Trading Bot", layout="centered")

st.title("🤖 Seif Bot - إشارات التداول")
st.markdown("هذا البوت يعرض لك إشارات الشراء والبيع حسب المؤشرات الفنية.")

# 📥 الإعدادات
symbol = st.selectbox("اختر الزوج", ["BTC-USD", "ETH-USD", "SOL-USD"])
interval = st.selectbox("اختر الفريم الزمني", ["1h", "4h", "1d"])
period = st.selectbox("اختر مدة التحليل", ["7d", "14d", "30d"])

# 📊 تحميل البيانات
df = yf.download(tickers=symbol, interval=interval, period=period)
df.reset_index(inplace=True)

# ✅ عرض الأعمدة المتاحة
st.subheader("🧾 الأعمدة الموجودة:")
st.write(df.columns.tolist())

# ✅ التحقق من الأعمدة المناسبة
try:
    price_col = symbol  # العمود باسم رمز الزوج مثلاً "BTC-USD"
    volume_col = [col for col in df.columns if "Volume" in col][0]
except IndexError:
    st.error("❌ لم يتم العثور على الأعمدة المطلوبة.")
    st.stop()

# ✅ إنشاء مؤشرات فنية
df['rsi'] = ta.momentum.RSIIndicator(close=df[price_col], window=14).rsi()
df['ma50'] = df[price_col].rolling(window=50).mean()
df['ma200'] = df[price_col].rolling(window=200).mean()
macd = ta.trend.MACD(close=df[price_col])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()

# ✅ تعريف الشموع
def is_bullish_engulfing(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    return (prev[price_col] < prev[price_col]) and (last[price_col] > last[price_col]) and (last[price_col] > prev[price_col])

def is_bearish_engulfing(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    return (prev[price_col] > prev[price_col]) and (last[price_col] < last[price_col]) and (last[price_col] < prev[price_col])

def is_high_volume(df):
    avg = df[volume_col].iloc[-10:].mean()
    return df[volume_col].iloc[-1] > avg

# ✅ إشارات الشراء والبيع
def is_buy_signal(df):
    last = df.iloc[-1]
    return (
        last['rsi'] < 30 and
        last['ma50'] > last['ma200'] and
        last['macd'] > last['macd_signal'] and
        is_high_volume(df)
    )

def is_sell_signal(df):
    last = df.iloc[-1]
    return (
        last['rsi'] > 70 and
        last['ma50'] < last['ma200'] and
        last['macd'] < last['macd_signal'] and
        is_high_volume(df)
    )

# ✅ عرض النتيجة
st.subheader("📈 النتيجة:")

if is_buy_signal(df):
    st.success("🟢 إشارة شراء قوية ✅")
elif is_sell_signal(df):
    st.error("🔴 إشارة بيع قوية ✅")
else:
    st.warning("⏸️ لا توجد إشارة مؤكدة حالياً.")

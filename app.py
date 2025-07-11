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

# تأكد من وجود بيانات كافية
if df.empty or len(df) < 50:
    st.error("❌ لا توجد بيانات كافية للتحليل. حاول تغيير الإعدادات.")
    st.stop()

# ✅ إصلاح الأعمدة لو فيها MultiIndex
df.columns = [col if isinstance(col, str) else col[1] for col in df.columns]

# ✅ أعمدة الأسعار
close_col = next((col for col in df.columns if "Close" in col), None)
volume_col = next((col for col in df.columns if "Volume" in col), None)

if not close_col or not volume_col:
    st.error("❌ لم يتم العثور على أعمدة الأسعار اللازمة.")
    st.stop()

# ✅ المؤشرات
df['rsi'] = ta.momentum.RSIIndicator(close=df[close_col], window=14).rsi()
df['ma50'] = df[close_col].rolling(window=50).mean()
df['ma200'] = df[close_col].rolling(window=200).mean()
macd = ta.trend.MACD(close=df[close_col])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()

# ✅ الشموع
def is_bullish_engulfing(df):
    if len(df) < 2:
        return False
    last = df.iloc[-1]
    prev = df.iloc[-2]
    return (prev[close_col] < prev['Open']) and (last[close_col] > last['Open']) and (last[close_col] > prev['Open'])

def is_bearish_engulfing(df):
    if len(df) < 2:
        return False
    last = df.iloc[-1]
    prev = df.iloc[-2]
    return (prev[close_col] > prev['Open']) and (last[close_col] < last['Open']) and (last[close_col] < prev['Open'])

def is_high_volume(df):
    if len(df) < 10:
        return False
    avg = df[volume_col].iloc[-10:].mean()
    return df[volume_col].iloc[-1] > avg

# ✅ إشارات
def is_buy_signal(df):
    last = df.iloc[-1]
    return (
        last['rsi'] < 30 and
        last['ma50'] > last['ma200'] and
        last['macd'] > last['macd_signal'] and
        is_bullish_engulfing(df) and
        is_high_volume(df)
    )

def is_sell_signal(df):
    last = df.iloc[-1]
    return (
        last['rsi'] > 70 and
        last['ma50'] < last['ma200'] and
        last['macd'] < last['macd_signal'] and
        is_bearish_engulfing(df) and
        is_high_volume(df)
    )

# ✅ عرض النتيجة
st.subheader("📈 النتيجة:")

try:
    if is_buy_signal(df):
        st.success("🟢 إشارة شراء قوية ✅")
    elif is_sell_signal(df):
        st.error("🔴 إشارة بيع قوية ✅")
    else:
        st.warning("⏸️ لا توجد إشارة مؤكدة حالياً.")
except Exception as e:
    st.error(f"حدث خطأ أثناء التحليل: {e}")

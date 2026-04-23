import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os
import time

st.set_page_config(layout="wide")
st.title("📊 StockMantra - Fundamental Analyzer")

# ----------------------------
# 📂 LOAD COMPANIES
# ----------------------------
@st.cache_data
def load_companies():
    if os.path.exists("companies.csv"):
        return pd.read_csv("companies.csv")
    return pd.DataFrame({
        "Symbol": ["RELIANCE.NS", "TCS.NS"],
        "Name": ["Reliance Industries", "TCS"],
        "ListingDate": ["1977-11-08", "2004-08-25"]
    })

df = load_companies()

# ----------------------------
# 🔍 SIDEBAR
# ----------------------------
company = st.sidebar.selectbox("Select Company", df["Name"])
symbol = df[df["Name"] == company]["Symbol"].values[0]
listing_date = df[df["Name"] == company]["ListingDate"].values[0]

# ----------------------------
# 📡 PRICE
# ----------------------------
@st.cache_data(ttl=600)
def get_price(symbol):
    try:
        time.sleep(1)
        return yf.Ticker(symbol).history(period="1y")
    except:
        return pd.DataFrame()

price = get_price(symbol)

# ----------------------------
# 📡 FUNDAMENTAL DATA (SAFE)
# ----------------------------
def get_ratios(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        return {
            "PE": info.get("trailingPE"),
            "ROE": info.get("returnOnEquity"),
            "ROCE": info.get("returnOnAssets"),  # closest proxy
        }
    except:
        return {"PE": None, "ROE": None, "ROCE": None}

rat = get_ratios(symbol)

# ----------------------------
# 🧠 FALLBACK (IF DATA MISSING)
# ----------------------------
def fallback():
    return {
        "PE": 20,
        "ROE": 15,
        "ROCE": 18
    }

if rat["PE"] is None:
    rat = fallback()

# ----------------------------
# 🏢 BASIC INFO
# ----------------------------
st.header(company)

latest_price = price["Close"].iloc[-1] if not price.empty else 0
latest_price = round(latest_price)  # ✅ absolute (no fraction)

col1, col2 = st.columns(2)
col1.metric("Price", latest_price)
col2.metric("Listing Date", listing_date)

# ----------------------------
# 📈 CHART
# ----------------------------
st.subheader("📈 Price Chart")

if not price.empty:
    fig = px.line(price, x=price.index, y="Close")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# 📊 RATIOS
# ----------------------------
st.subheader("📊 Fundamental Ratios")

ratios = {
    "PE Ratio": round(rat["PE"], 2) if rat["PE"] else rat["PE"],
    "ROE (%)": round(rat["ROE"] * 100, 2) if rat["ROE"] else rat["ROE"],
    "ROCE (%)": round(rat["ROCE"] * 100, 2) if rat["ROCE"] else rat["ROCE"]
}

st.table(pd.DataFrame(ratios.items(), columns=["Metric", "Value"]))

# ----------------------------
# ⚔️ COMPARISON
# ----------------------------
st.sidebar.subheader("Compare")

comp = st.sidebar.selectbox("Second Company", df["Name"])
comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]

price2 = get_price(comp_symbol)
price2_val = round(price2["Close"].iloc[-1]) if not price2.empty else 0

rat2 = get_ratios(comp_symbol)
if rat2["PE"] is None:
    rat2 = fallback()

comp_df = pd.DataFrame({
    "Metric": ["Price", "PE", "ROE (%)", "ROCE (%)"],
    company: [
        latest_price,
        round(rat["PE"], 2),
        round(rat["ROE"] * 100, 2),
        round(rat["ROCE"] * 100, 2)
    ],
    comp: [
        price2_val,
        round(rat2["PE"], 2),
        round(rat2["ROE"] * 100, 2),
        round(rat2["ROCE"] * 100, 2)
    ]
})

st.subheader("⚔️ Comparison")
st.dataframe(comp_df)
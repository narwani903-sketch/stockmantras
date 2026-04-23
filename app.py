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
# 📡 PRICE (CACHED)
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
# 📡 RATIOS (FROM YFINANCE)
# ----------------------------
def get_ratios(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            "PE": info.get("trailingPE"),
            "ROE": info.get("returnOnEquity"),
            "ROCE": info.get("returnOnAssets")  # proxy
        }
    except:
        return {"PE": None, "ROE": None, "ROCE": None}

rat = get_ratios(symbol)

# ----------------------------
# 🧠 FALLBACK VALUES
# ----------------------------
def fallback():
    return {"PE": 20, "ROE": 0.15, "ROCE": 0.18}

if rat["PE"] is None:
    rat = fallback()

# ----------------------------
# 🧠 SAFE FORMAT FUNCTIONS
# ----------------------------
def safe_percent(val):
    try:
        if val is None:
            return "N/A"
        return round(val * 100, 2)
    except:
        return "N/A"

def safe_number(val):
    try:
        if val is None:
            return "N/A"
        return round(val, 2)
    except:
        return "N/A"

# ----------------------------
# 🏢 BASIC INFO
# ----------------------------
st.header(company)

latest_price = price["Close"].iloc[-1] if not price.empty else 0
latest_price = round(latest_price)  # absolute value

col1, col2 = st.columns(2)
col1.metric("Price", latest_price)
col2.metric("Listing Date", listing_date)

# ----------------------------
# 📈 PRICE CHART
# ----------------------------
st.subheader("📈 Price Chart")

if not price.empty:
    fig = px.line(price, x=price.index, y="Close")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No price data available")

# ----------------------------
# 📊 RATIOS DISPLAY
# ----------------------------
st.subheader("📊 Fundamental Ratios")

ratios = {
    "PE Ratio": safe_number(rat.get("PE")),
    "ROE (%)": safe_percent(rat.get("ROE")),
    "ROCE (%)": safe_percent(rat.get("ROCE"))
}

st.table(pd.DataFrame(ratios.items(), columns=["Metric", "Value"]))

# ----------------------------
# ⚔️ COMPARISON
# ----------------------------
st.sidebar.subheader("Compare")

comp = st.sidebar.selectbox("Second Company", df["Name"])
comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]

price2 = get_price(comp_symbol)
price2_val = price2["Close"].iloc[-1] if not price2.empty else 0
price2_val = round(price2_val)

rat2 = get_ratios(comp_symbol)
if rat2["PE"] is None:
    rat2 = fallback()

comp_df = pd.DataFrame({
    "Metric": ["Price", "PE Ratio", "ROE (%)", "ROCE (%)"],
    company: [
        latest_price,
        safe_number(rat.get("PE")),
        safe_percent(rat.get("ROE")),
        safe_percent(rat.get("ROCE"))
    ],
    comp: [
        price2_val,
        safe_number(rat2.get("PE")),
        safe_percent(rat2.get("ROE")),
        safe_percent(rat2.get("ROCE"))
    ]
})

st.subheader("⚔️ Comparison")
st.dataframe(comp_df)
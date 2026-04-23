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
# 📡 SAFE PRICE (CACHED)
# ----------------------------
@st.cache_data(ttl=600)
def get_price(symbol):
    try:
        time.sleep(1)
        return yf.Ticker(symbol).history(period="1y")
    except:
        return pd.DataFrame()

# ----------------------------
# 📡 FAST INFO (LIGHT)
# ----------------------------
@st.cache_data(ttl=600)
def get_fast(symbol):
    try:
        time.sleep(1)
        return yf.Ticker(symbol).fast_info
    except:
        return {}

price = get_price(symbol)
fast = get_fast(symbol)

# ----------------------------
# 🧠 LOAD FINANCIALS (ON DEMAND)
# ----------------------------
fin, bal = None, None

if st.button("📄 Load Financials"):
    try:
        time.sleep(2)
        stock = yf.Ticker(symbol)
        fin = stock.financials
        bal = stock.balance_sheet
    except:
        st.warning("⚠️ Rate limit hit. Try again later.")

# ----------------------------
# 🧠 SAFE EXTRACT
# ----------------------------
def safe(df, key):
    try:
        return float(df.loc[key].iloc[0])
    except:
        return None

net_income = safe(fin, "Net Income") if fin is not None else None
revenue = safe(fin, "Total Revenue") if fin is not None else None
equity = safe(bal, "Total Stockholder Equity") if bal is not None else None
assets = safe(bal, "Total Assets") if bal is not None else None

price_val = fast.get("lastPrice", None)

# ----------------------------
# 📊 CALCULATIONS
# ----------------------------
def calc_roe():
    if net_income and equity:
        return round((net_income / equity) * 100, 2)
    return "N/A"

def calc_roce():
    if net_income and assets:
        return round((net_income / assets) * 100, 2)
    return "N/A"

def calc_margin():
    if net_income and revenue:
        return round((net_income / revenue) * 100, 2)
    return "N/A"

def calc_pe():
    if net_income and price_val:
        return round(price_val / (net_income / 1e7), 2)
    return "N/A"

# ----------------------------
# 🏢 BASIC INFO
# ----------------------------
st.header(company)

col1, col2, col3 = st.columns(3)
col1.metric("Price", price_val if price_val else "N/A")
col2.metric("Market Cap", fast.get("marketCap", "N/A"))
col3.metric("Listing Date", listing_date)

# ----------------------------
# 📈 CHART
# ----------------------------
st.subheader("📈 Price Chart")

if not price.empty:
    fig = px.line(price, x=price.index, y="Close")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Chart not available")

# ----------------------------
# 📊 RATIOS
# ----------------------------
st.subheader("📊 Fundamental Ratios")

ratios = {
    "PE Ratio": calc_pe(),
    "ROE (%)": calc_roe(),
    "ROCE (%)": calc_roce(),
    "Profit Margin (%)": calc_margin()
}

st.table(pd.DataFrame(ratios.items(), columns=["Metric", "Value"]))

# ----------------------------
# 📄 FINANCIALS (₹ MILLIONS)
# ----------------------------
st.subheader("📄 Financials (₹ Millions)")

def to_millions(df):
    if df is not None:
        return (df / 1_000_000).round(2)
    return pd.DataFrame()

if fin is not None:
    tab1, tab2 = st.tabs(["Income", "Balance Sheet"])

    with tab1:
        st.dataframe(to_millions(fin))

    with tab2:
        st.dataframe(to_millions(bal))
else:
    st.info("Click 'Load Financials' to view data")

# ----------------------------
# ⚔️ COMPARISON
# ----------------------------
st.sidebar.subheader("Compare")

comp = st.sidebar.selectbox("Second Company", df["Name"])
comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]

fast2 = get_fast(comp_symbol)

comp_df = pd.DataFrame({
    "Metric": ["Price", "Market Cap"],
    company: [
        price_val,
        fast.get("marketCap", "N/A")
    ],
    comp: [
        fast2.get("lastPrice", "N/A"),
        fast2.get("marketCap", "N/A")
    ]
})

st.subheader("⚔️ Comparison")
st.dataframe(comp_df)
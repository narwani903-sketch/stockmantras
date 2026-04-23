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
# 📡 PRICE (SAFE CACHE)
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
# 📡 LOAD FINANCIALS (BUTTON)
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
# 🧠 SAFE EXTRACT FUNCTION
# ----------------------------
def get_val(df, key):
    try:
        return float(df.loc[key].iloc[0])
    except:
        return None

# Extract values
net_income = get_val(fin, "Net Income") if fin is not None else None
revenue = get_val(fin, "Total Revenue") if fin is not None else None
equity = get_val(bal, "Total Stockholder Equity") if bal is not None else None
debt = get_val(bal, "Total Debt") if bal is not None else 0
assets = get_val(bal, "Total Assets") if bal is not None else None

# ----------------------------
# 📊 RATIOS (PROPER CALCULATION)
# ----------------------------
def calc_roe():
    if net_income and equity:
        return round((net_income / equity) * 100, 2)
    return "N/A"

def calc_roce():
    try:
        capital_employed = equity + debt
        return round((net_income / capital_employed) * 100, 2)
    except:
        return "N/A"

def calc_margin():
    if net_income and revenue:
        return round((net_income / revenue) * 100, 2)
    return "N/A"

def calc_pe():
    try:
        latest_price = price["Close"].iloc[-1]
        shares_est = equity / latest_price if equity else None
        eps = net_income / shares_est if shares_est else None
        return round(latest_price / eps, 2) if eps else "N/A"
    except:
        return "N/A"

# ----------------------------
# 🏢 BASIC INFO
# ----------------------------
st.header(company)

latest_price = price["Close"].iloc[-1] if not price.empty else "N/A"

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
# 📊 RATIOS DISPLAY
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
# ⚔️ COMPARISON (BASIC SAFE)
# ----------------------------
st.sidebar.subheader("Compare")

comp = st.sidebar.selectbox("Second Company", df["Name"])
comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]

price2 = get_price(comp_symbol)
price2_val = price2["Close"].iloc[-1] if not price2.empty else "N/A"

comp_df = pd.DataFrame({
    "Metric": ["Price"],
    company: [latest_price],
    comp: [price2_val]
})

st.subheader("⚔️ Comparison")
st.dataframe(comp_df)
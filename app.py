import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os

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
# 📡 DATA
# ----------------------------
@st.cache_data(ttl=300)
def get_price(symbol):
    return yf.Ticker(symbol).history(period="1y")

def get_data(symbol):
    stock = yf.Ticker(symbol)
    try:
        return stock.fast_info, stock.financials, stock.balance_sheet
    except:
        return {}, None, None

price = get_price(symbol)
fast, fin, bal = get_data(symbol)

# ----------------------------
# 🧠 MANUAL CALCULATIONS
# ----------------------------
def safe(series, key):
    try:
        return float(series.loc[key][0])
    except:
        return None

net_income = safe(fin, "Net Income")
revenue = safe(fin, "Total Revenue")
equity = safe(bal, "Total Stockholder Equity")
assets = safe(bal, "Total Assets")

def calc_pe(price, earnings):
    if price and earnings:
        return round(price / (earnings / 1e7), 2)  # approx EPS logic
    return "N/A"

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

# ----------------------------
# 🏢 BASIC INFO
# ----------------------------
st.header(company)

price_val = fast.get("lastPrice", "N/A")

col1, col2, col3 = st.columns(3)
col1.metric("Price", price_val)
col2.metric("Market Cap", fast.get("marketCap", "N/A"))
col3.metric("Listing Date", listing_date)

# ----------------------------
# 📈 CHART
# ----------------------------
st.subheader("📈 Price Chart")
fig = px.line(price, x=price.index, y="Close")
st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# 📊 RATIOS (NO N/A NOW)
# ----------------------------
st.subheader("📊 Fundamental Ratios")

ratios = {
    "PE Ratio": calc_pe(price_val, net_income),
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

tab1, tab2 = st.tabs(["Income", "Balance Sheet"])

with tab1:
    st.dataframe(to_millions(fin))

with tab2:
    st.dataframe(to_millions(bal))

# ----------------------------
# ⚔️ COMPARISON (PRO)
# ----------------------------
st.sidebar.subheader("Compare")
comp = st.sidebar.selectbox("Second Company", df["Name"])
comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]

fast2, fin2, bal2 = get_data(comp_symbol)

def extract(fin, bal):
    ni = safe(fin, "Net Income")
    eq = safe(bal, "Total Stockholder Equity")
    rev = safe(fin, "Total Revenue")

    roe = round((ni / eq) * 100, 2) if ni and eq else "N/A"
    margin = round((ni / rev) * 100, 2) if ni and rev else "N/A"

    return roe, margin

roe1, margin1 = extract(fin, bal)
roe2, margin2 = extract(fin2, bal2)

comp_df = pd.DataFrame({
    "Metric": ["Price", "ROE (%)", "Profit Margin (%)"],
    company: [price_val, roe1, margin1],
    comp: [fast2.get("lastPrice", "N/A"), roe2, margin2]
})

st.subheader("⚔️ Comparison")
st.dataframe(comp_df)
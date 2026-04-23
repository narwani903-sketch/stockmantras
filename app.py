import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 StockMantra - Fundamental Analyzer")

# ----------------------------
# 📂 COMPANY LIST
# ----------------------------
@st.cache_data
def load_companies():
    return pd.read_csv("companies.csv")

df = load_companies()

# Sidebar
st.sidebar.header("🔍 Select Company")
search = st.sidebar.text_input("Search")

if search:
    df_filtered = df[df["Name"].str.contains(search, case=False)]
else:
    df_filtered = df

company = st.sidebar.selectbox("Company", df_filtered["Name"])
symbol = df[df["Name"] == company]["Symbol"].values[0]
listing_date = df[df["Name"] == company]["ListingDate"].values[0]

# ----------------------------
# 📡 SAFE DATA FETCHING
# ----------------------------
@st.cache_data(ttl=300)
def get_data(symbol):
    stock = yf.Ticker(symbol)

    try:
        price = stock.history(period="1y")
    except:
        price = pd.DataFrame()

    try:
        fast = stock.fast_info
    except:
        fast = {}

    try:
        financials = stock.financials
        balance = stock.balance_sheet
        cashflow = stock.cashflow
    except:
        financials, balance, cashflow = None, None, None

    return price, fast, financials, balance, cashflow

price, info, fin, bal, cf = get_data(symbol)

# ----------------------------
# 🏢 BASIC INFO
# ----------------------------
st.header(company)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Price", info.get("lastPrice", "N/A"))
col2.metric("Market Cap", info.get("marketCap", "N/A"))
col3.metric("Volume", info.get("lastVolume", "N/A"))
col4.metric("Listing Date", listing_date)

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
st.subheader("📊 Key Ratios")

ratios = {
    "PE Ratio": info.get("trailingPE", "N/A"),
    "Day High": info.get("dayHigh", "N/A"),
    "Day Low": info.get("dayLow", "N/A")
}

st.table(pd.DataFrame(ratios.items(), columns=["Metric", "Value"]))

# ----------------------------
# 🧾 FINANCIALS
# ----------------------------
st.subheader("📄 Financial Statements")

tab1, tab2, tab3 = st.tabs(["Income", "Balance Sheet", "Cashflow"])

with tab1:
    if fin is not None:
        st.dataframe(fin)
    else:
        st.warning("Income data not available")

with tab2:
    if bal is not None:
        st.dataframe(bal)
    else:
        st.warning("Balance sheet not available")

with tab3:
    if cf is not None:
        st.dataframe(cf)
    else:
        st.warning("Cashflow not available")

# ----------------------------
# 🏦 SHAREHOLDING (STATIC DEMO)
# ----------------------------
st.subheader("🏦 Shareholding Pattern")

holding = pd.DataFrame({
    "Category": ["Promoters", "FIIs", "DIIs", "Public"],
    "Holding %": [50, 20, 15, 15]
})

fig2 = px.pie(holding, names="Category", values="Holding %")
st.plotly_chart(fig2)

# ----------------------------
# ⚔️ COMPARISON
# ----------------------------
st.sidebar.subheader("Compare")

comp = st.sidebar.selectbox("Second Company", df["Name"])

comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]
_, info2, _, _, _ = get_data(comp_symbol)

comp_df = pd.DataFrame({
    "Metric": ["Price", "Market Cap", "Volume"],
    company: [
        info.get("lastPrice", "N/A"),
        info.get("marketCap", "N/A"),
        info.get("lastVolume", "N/A")
    ],
    comp: [
        info2.get("lastPrice", "N/A"),
        info2.get("marketCap", "N/A"),
        info2.get("lastVolume", "N/A")
    ]
})

st.subheader("⚔️ Comparison")
st.table(comp_df)

import sys
import streamlit as st

st.write(sys.executable)
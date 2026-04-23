import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("📊 StockMantra - Fundamental Analyzer")

# ----------------------------
# 📂 LOAD COMPANY LIST
# ----------------------------
@st.cache_data
def load_companies():
    if os.path.exists("companies.csv"):
        return pd.read_csv("companies.csv")
    else:
        return pd.DataFrame({
            "Symbol": ["RELIANCE.NS", "TCS.NS"],
            "Name": ["Reliance Industries", "TCS"],
            "ListingDate": ["1977-11-08", "2004-08-25"]
        })

df = load_companies()

# ----------------------------
# 🔍 SIDEBAR
# ----------------------------
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
# 📡 DATA FUNCTIONS
# ----------------------------

# ✅ Cache ONLY price
@st.cache_data(ttl=300)
def get_price(symbol):
    try:
        return yf.Ticker(symbol).history(period="1y")
    except:
        return pd.DataFrame()

# ❌ NO CACHE HERE
def get_fast_info(symbol):
    try:
        return yf.Ticker(symbol).fast_info
    except:
        return {}

# ❌ NO CACHE HERE
def get_financials(symbol):
    stock = yf.Ticker(symbol)
    try:
        return stock.financials, stock.balance_sheet, stock.cashflow
    except:
        return None, None, None

# ----------------------------
# 📊 FETCH DATA
# ----------------------------
price = get_price(symbol)
info = get_fast_info(symbol)
fin, bal, cf = get_financials(symbol)

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
st.subheader("📊 Key Info")

ratios = {
    "Day High": info.get("dayHigh", "N/A"),
    "Day Low": info.get("dayLow", "N/A"),
    "Previous Close": info.get("previousClose", "N/A")
}

st.table(pd.DataFrame(ratios.items(), columns=["Metric", "Value"]))

# ----------------------------
# 📄 FINANCIALS
# ----------------------------
st.subheader("📄 Financial Statements")

tab1, tab2, tab3 = st.tabs(["Income", "Balance Sheet", "Cashflow"])

with tab1:
    st.dataframe(fin if fin is not None else pd.DataFrame())

with tab2:
    st.dataframe(bal if bal is not None else pd.DataFrame())

with tab3:
    st.dataframe(cf if cf is not None else pd.DataFrame())

# ----------------------------
# 🏦 SHAREHOLDING
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

info2 = get_fast_info(comp_symbol)

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
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

@st.cache_data(ttl=300)
def get_price(symbol):
    try:
        return yf.Ticker(symbol).history(period="1y")
    except:
        return pd.DataFrame()

def get_fast_info(symbol):
    try:
        return yf.Ticker(symbol).fast_info
    except:
        return {}

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
# 📈 PRICE CHART
# ----------------------------
st.subheader("📈 Price Chart")

if not price.empty:
    fig = px.line(price, x=price.index, y="Close")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Chart not available")

# ----------------------------
# 📊 KEY RATIOS
# ----------------------------
st.subheader("📊 Key Ratios")

ratios = {
    "PE Ratio": info.get("trailingPE", "N/A"),
    "ROE": info.get("returnOnEquity", "N/A"),
    "Profit Margin": info.get("profitMargins", "N/A"),
    "Operating Margin": info.get("operatingMargins", "N/A"),
    "Revenue Growth": info.get("revenueGrowth", "N/A")
}

st.table(pd.DataFrame(ratios.items(), columns=["Metric", "Value"]))

# ----------------------------
# 📄 FINANCIALS (IN MILLIONS)
# ----------------------------
st.subheader("📄 Financial Statements (₹ in Millions)")

def convert_to_millions(df):
    if df is not None and not df.empty:
        return (df / 1_000_000).round(2)
    return df

tab1, tab2, tab3 = st.tabs(["Income", "Balance Sheet", "Cashflow"])

with tab1:
    st.dataframe(convert_to_millions(fin))

with tab2:
    st.dataframe(convert_to_millions(bal))

with tab3:
    st.dataframe(convert_to_millions(cf))

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
# ⚔️ ADVANCED COMPARISON
# ----------------------------
st.sidebar.subheader("Compare")

comp = st.sidebar.selectbox("Second Company", df["Name"])
comp_symbol = df[df["Name"] == comp]["Symbol"].values[0]

info2 = get_fast_info(comp_symbol)

def get_ratios(i):
    return {
        "Price": i.get("lastPrice", "N/A"),
        "Market Cap": i.get("marketCap", "N/A"),
        "PE Ratio": i.get("trailingPE", "N/A"),
        "ROE": i.get("returnOnEquity", "N/A"),
        "Profit Margin": i.get("profitMargins", "N/A"),
        "Operating Margin": i.get("operatingMargins", "N/A"),
        "Revenue Growth": i.get("revenueGrowth", "N/A")
    }

r1 = get_ratios(info)
r2 = get_ratios(info2)

comp_df = pd.DataFrame({
    "Metric": list(r1.keys()),
    company: list(r1.values()),
    comp: list(r2.values())
})

st.subheader("⚔️ Fundamental Comparison")
st.dataframe(comp_df)
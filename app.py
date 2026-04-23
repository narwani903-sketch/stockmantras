import streamlit as st
import pandas as pd
import os
from tax_logic import TaxCalculator, compare_regimes
from visualizations import plot_slab_tax, plot_tax_components, plot_regime_comparison, plot_income_tax_trend
from reports import generate_excel_report, generate_pdf_report
from ui_components import apply_custom_css, render_metric_card, show_tax_suggestions

# Configuration
st.set_page_config(page_title="Income Tax Calculator FY 25-26", page_icon="₹", layout="wide")
apply_custom_css()

# Initialize session state for lead form
if 'lead_captured' not in st.session_state:
    st.session_state.lead_captured = False

# Sidebar - Inputs
st.sidebar.title("₹ Tax Calculator India")
st.sidebar.markdown("**FY 2025-26 | AY 2026-27**")

# Regime Selection
is_new_regime = st.sidebar.radio("Select Tax Regime", ["New Regime (Default)", "Old Regime"]) == "New Regime (Default)"

st.sidebar.markdown("---")
st.sidebar.markdown("<div class='section-income'><h3>Income Details</h3></div>", unsafe_allow_html=True)

# Income Inputs
salary = st.sidebar.number_input("Gross Salary", min_value=0, value=0, step=50000, help="Standard deduction will be applied automatically.")
house_property = st.sidebar.number_input("Income from House Property", value=0, step=10000)
business = st.sidebar.number_input("Income from Business/Profession", min_value=0, value=0, step=50000)

with st.sidebar.expander("Capital Gains"):
    ltcg_112a = st.number_input("LTCG (Equity - Sec 112A)", min_value=0, value=0, step=10000, help="Taxed at 12.5% (assuming >1.25L already adjusted or full amount if no exemption applies here)")
    stcg_111a = st.number_input("STCG (Equity - Sec 111A)", min_value=0, value=0, step=10000, help="Taxed at 20%")

with st.sidebar.expander("Other Incomes"):
    other_sources = st.number_input("Income from Other Sources (Interest, etc.)", min_value=0, value=0, step=10000)
    crypto_lottery = st.number_input("Crypto / Lottery / Winnings", min_value=0, value=0, step=10000, help="Taxed flat at 30%")
    agri_income = st.number_input("Net Agriculture Income", min_value=0, value=0, step=10000, help="Used for rate purposes (partial integration)")

# Deductions (Only if Old Regime)
deductions = 0
if not is_new_regime:
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='section-deductions'><h3>Deductions</h3></div>", unsafe_allow_html=True)
    deductions = st.sidebar.number_input("Total Chapter VI-A Deductions (80C, 80D, etc.)", min_value=0, value=0, step=10000)

# Build Input Dictionary
inputs = {
    'salary': salary,
    'house_property': house_property,
    'business': business,
    'ltcg_112a': ltcg_112a,
    'stcg_111a': stcg_111a,
    'other_sources': other_sources,
    'crypto_lottery': crypto_lottery,
    'agri_income': agri_income,
    'deductions': deductions
}

# Main Panel
st.title("Comprehensive Tax Dashboard")

# Lead Generation Form Modal / Area
if not st.session_state.lead_captured:
    with st.expander("Unlock Detailed Reports & AI Suggestions", expanded=True):
        st.write("Please enter your details to generate personalized reports.")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
        with col2:
            phone = st.text_input("Phone Number")
            city = st.text_input("City")
            
        if st.button("Generate Reports"):
            if name and email:
                # Save lead
                lead_data = pd.DataFrame([[name, email, phone, city]], columns=['Name', 'Email', 'Phone', 'City'])
                file_path = 'leads.csv'
                if not os.path.exists(file_path):
                    lead_data.to_csv(file_path, index=False)
                else:
                    lead_data.to_csv(file_path, mode='a', header=False, index=False)
                st.session_state.lead_captured = True
                st.session_state.user_info = {'name': name, 'email': email}
                st.rerun()
            else:
                st.error("Name and Email are required.")

# Perform Calculation
calc = TaxCalculator(is_new_regime=is_new_regime)
results = calc.calculate_tax(inputs)

# Top Row Metrics
col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card("Gross Total Income", results['total_income'])
with col2:
    render_metric_card("Total Tax Liability", results['total_tax_liability'])
with col3:
    effective_rate = (results['total_tax_liability'] / results['total_income'] * 100) if results['total_income'] > 0 else 0
    render_metric_card("Effective Tax Rate", effective_rate, prefix="")
    st.markdown(f"<div style='text-align: center; color: #6b7280; margin-top: -10px;'>%</div>", unsafe_allow_html=True)

st.markdown("---")

# Visualizations Row 1
col_v1, col_v2 = st.columns(2)

with col_v1:
    st.subheader("Tax Components")
    fig_pie = plot_tax_components(results)
    st.plotly_chart(fig_pie, width='stretch')
    
with col_v2:
    st.subheader("Slab-wise Breakdown")
    fig_bar = plot_slab_tax(results['breakdown'])
    st.plotly_chart(fig_bar, width='stretch')

st.markdown("---")

# Old vs New Comparison
st.subheader("Old vs New Regime Comparison")
comparison = compare_regimes(inputs)

col_c1, col_c2 = st.columns([1, 2])
with col_c1:
    st.write("")
    st.write("")
    st.metric(label="New Regime Tax", value=f"₹{comparison['New Regime']['total_tax_liability']:,.0f}")
    st.metric(label="Old Regime Tax", value=f"₹{comparison['Old Regime']['total_tax_liability']:,.0f}")
    
    if comparison['Recommendation'] == 'New Regime':
        st.success(f"**Recommendation:** Go with New Regime and save ₹{comparison['Savings']:,.0f}")
    elif comparison['Recommendation'] == 'Old Regime':
        st.info(f"**Recommendation:** Go with Old Regime and save ₹{comparison['Savings']:,.0f}")
    else:
        st.warning("Both regimes yield the same tax liability.")
        
with col_c2:
    fig_comp = plot_regime_comparison(comparison['New Regime'], comparison['Old Regime'])
    st.plotly_chart(fig_comp, width='stretch')

# Income vs Tax Simulation
st.markdown("---")
st.subheader("Income vs Tax Simulator")
fig_trend = plot_income_tax_trend(inputs, is_new_regime)
st.plotly_chart(fig_trend, width='stretch')

# Detailed Breakdown Table
st.markdown("---")
st.subheader("Detailed Computation Table")
df_breakdown = pd.DataFrame([{
    'Description': 'Total Taxable Income', 'Amount': f"₹{results['total_income']:,.0f}"
}, {
    'Description': 'Tax on Normal Rates', 'Amount': f"₹{results['tax_normal']:,.0f}"
}, {
    'Description': 'Tax on Special Rates (Capital Gains/Crypto)', 'Amount': f"₹{results['tax_special']:,.0f}"
}, {
    'Description': 'Less: Rebate u/s 87A', 'Amount': f"₹{results['rebate']:,.0f}"
}, {
    'Description': 'Less: Rebate Marginal Relief', 'Amount': f"₹{results['rebate_marginal_relief']:,.0f}"
}, {
    'Description': 'Add: Surcharge', 'Amount': f"₹{results['surcharge']:,.0f}"
}, {
    'Description': 'Less: Surcharge Marginal Relief', 'Amount': f"₹{results['surcharge_marginal_relief']:,.0f}"
}, {
    'Description': 'Add: Health & Education Cess (4%)', 'Amount': f"₹{results['cess']:,.0f}"
}, {
    'Description': 'Total Tax Liability', 'Amount': f"₹{results['total_tax_liability']:,.0f}"
}])
st.table(df_breakdown)

# AI Suggestions and Reports
if st.session_state.lead_captured:
    st.markdown("---")
    show_tax_suggestions(results, is_new_regime)
    
    st.markdown("### 📥 Download Reports")
    col_d1, col_d2, col_d3 = st.columns([1,1,2])
    
    excel_data = generate_excel_report(inputs, results, is_new_regime)
    with col_d1:
        st.download_button(
            label="📄 Download Excel",
            data=excel_data,
            file_name="tax_computation.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    pdf_data = generate_pdf_report(inputs, results, is_new_regime, st.session_state.user_info)
    with col_d2:
        st.download_button(
            label="📑 Download PDF",
            data=pdf_data,
            file_name="tax_report.pdf",
            mime="application/pdf"
        )

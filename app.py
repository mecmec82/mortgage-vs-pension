import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Mortgage vs Pension Strategy", layout="wide")

st.title("🏠 Mortgage vs. 📈 Pension Sacrifice Calculator")
st.write("Compare extending your mortgage term to increase pension contributions (Higher Rate Taxpayer).")

# --- Sidebar Inputs ---
st.sidebar.header("Mortgage Settings")
principal = st.sidebar.number_input("Mortgage Amount (£)", value=260000, step=5000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
current_term = st.sidebar.slider("Original Term (Years)", 10, 35, 17)
new_term = st.sidebar.slider("Extended Term (Years)", 10, 40, 30)

st.sidebar.header("Pension & Salary")
salary = st.sidebar.number_input("Annual Salary (£)", value=67000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000)
p_growth = st.sidebar.slider("Expected Pension Growth (%)", 1.0, 12.0, 5.0) / 100
sal_growth = st.sidebar.slider("Annual Salary Growth (%)", 0.0, 5.0, 1.0) / 100
years_to_sim = st.sidebar.slider("Years until 25% Tax-Free Access", 5, 25, 14)

st.sidebar.header("Contribution Strategy")
old_sacrifice = st.sidebar.slider("Current Sacrifice (%)", 0, 20, 7) / 100
new_sacrifice = st.sidebar.slider("New Sacrifice (%)", 0, 30, 10) / 100
employer_match = 0.10 # Fixed at 10% based on your prompt

# --- Calculations ---
# 1. Mortgage Monthly Payments
pmt_old = abs(npf.pmt(m_interest/12, current_term*12, principal))
pmt_new = abs(npf.pmt(m_interest/12, new_term*12, principal))
monthly_m_saving = pmt_old - pmt_new

# 2. Take Home Pay Delta (40% Tax + 2% NI saving)
extra_sacrifice_monthly = (salary * (new_sacrifice - old_sacrifice)) / 12
take_home_drop = extra_sacrifice_monthly * 0.58 

# 3. Pension Projection (Compound Interest)
pension_data = []
current_pot = initial_pension
m_balance = principal

for year in range(1, years_to_sim + 1):
    # Pension Growth
    yearly_contrib = (salary * (1 + sal_growth)**year) * (new_sacrifice + employer_match)
    current_pot = (current_pot + yearly_contrib) * (1 + p_growth)
    
    # Mortgage Balance (Extended Term)
    m_balance = abs(npf.fv(m_interest/12, year*12, pmt_new, -principal))
    
    pension_data.append({
        "Year": year,
        "Pension Pot": current_pot,
        "Mortgage Balance": m_balance,
        "Tax-Free Lump Sum (25%)": current_pot * 0.25
    })

df = pd.DataFrame(pension_data)

# --- UI Layout ---
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Mortgage Saving", f"£{monthly_m_saving:,.2f}")
col2.metric("Take-Home Pay Drop", f"£{take_home_drop:,.2f}", delta_color="inverse")
col3.metric("Net Monthly Buffer", f"£{monthly_m_saving - take_home_drop:,.2f}")

st.divider()

# Plotting the data
st.subheader("The Wealth Gap: Pension vs Mortgage Debt")
st.line_chart(df.set_index("Year")[["Pension Pot", "Mortgage Balance", "Tax-Free Lump Sum (25%)"]])

# Final Verdict Logic
final_lump_sum = df.iloc[-1]["Tax-Free Lump Sum (25%)"]
final_mortgage = df.iloc[-1]["Mortgage Balance"]
surplus = final_lump_sum - final_mortgage

st.subheader("Summary at Year " + str(years_to_sim))
if surplus > 0:
    st.success(f"✅ Success! Your tax-free lump sum (£{final_lump_sum:,.0f}) covers the remaining mortgage (£{final_mortgage:,.0f}) with £{surplus:,.0f} left over in cash.")
else:
    st.error(f"⚠️ Shortfall. Your lump sum (£{final_lump_sum:,.0f}) is short of the mortgage (£{final_mortgage:,.0f}) by £{abs(surplus):,.0f}.")

st.write(f"**Remaining Pension Pot (75%):** £{df.iloc[-1]['Pension Pot'] * 0.75:,.0f}")

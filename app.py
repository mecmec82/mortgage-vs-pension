import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Retirement Strategy at 60", layout="wide")

st.title("🏠 Retirement Wealth Strategy: Age 60 Target")

# --- Sidebar Inputs ---
st.sidebar.header("Personal Details")
current_age = st.sidebar.number_input("Current Age", value=43)
target_age = 60
sim_years = target_age - current_age

st.sidebar.header("Financials")
principal = st.sidebar.number_input("Mortgage Amount (£)", value=260000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
salary = st.sidebar.number_input("Annual Salary (£)", value=67000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000)
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
sal_growth = 0.01 
employer_match = 0.10

st.sidebar.header("Strategy Shift")
old_sac = st.sidebar.slider("Baseline Sacrifice (%)", 0, 20, 7) / 100
new_sac = st.sidebar.slider("New Strategy Sacrifice (%)", 0, 20, 10) / 100

def calculate_wealth_at_60(term, sacrifice):
    # 1. Mortgage Calculations
    monthly_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    # Remaining balance at age 60
    bal_at_60 = abs(npf.fv(m_interest/12, sim_years*12, monthly_pmt, -principal))
    
    # 2. Pension Calculations
    current_pot = initial_pension
    for yr in range(1, sim_years + 1):
        yearly_contrib = (salary * (1 + sal_growth)**yr) * (sacrifice + employer_match)
        current_pot = (current_pot + yearly_contrib) * (1 + p_growth)
    
    # 3. Take Home Pay
    diff_sacrifice_monthly = (salary * (sacrifice - old_sac)) / 12
    take_home_delta = -(diff_sacrifice_monthly * 0.58) if sacrifice > old_sac else 0
    
    # 4. Total Net Position at 60
    # Net Wealth = Pension Pot - Mortgage Debt (even if not paying it off yet)
    net_wealth = current_pot - bal_at_60
    
    return monthly_pmt, take_home_delta, bal_at_60, current_pot, net_wealth

# --- Compute ---
s1_pmt, s1_take, s1_bal, s1_pot, s1_net = calculate_wealth_at_60(17, old_sac)
s2_pmt, s2_take, s2_bal, s2_pot, s2_net = calculate_wealth_at_60(25, new_sac)
s3_pmt, s3_take, s3_bal, s3_pot, s3_net = calculate_wealth_at_60(30, new_sac)

# --- Table Data ---
data = {
    "Metric": [
        "Monthly Mortgage Payment",
        "Change in Take-Home Pay",
        "Mortgage Balance at Age 60",
        "Pension Pot at Age 60",
        "Net Position (Pot minus Debt)",
        "Total Savings vs Baseline"
    ],
    "Strategy 1: 17yr (Current)": [
        f"£{s1_pmt:,.2f}", "Baseline", f"£{s1_bal:,.2f}", f"£{s1_pot:,.2f}", 
        f"£{s1_net:,.2f}", "Baseline"
    ],
    "Strategy 2: 25yr (New)": [
        f"£{s2_pmt:,.2f}", f"£{s2_take:,.2f}", f"£{s2_bal:,.2f}", f"£{s2_pot:,.2f}", 
        f"£{s2_net:,.2f}", f"£{s2_net - s1_net:,.2f}"
    ],
    "Strategy 3: 30yr (New)": [
        f"£{s3_pmt:,.2f}", f"£{s3_take:,.2f}", f"£{s3_bal:,.2f}", f"£{s3_pot:,.2f}", 
        f"£{s3_net:,.2f}", f"£{s3_net - s1_net:,.2f}"
    ]
}

st.table(pd.DataFrame(data))

import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Mortgage vs Pension Strategy", layout="wide")

st.title("🏠 Strategy Comparison: 17yr vs 25yr vs 30yr")

# --- Sidebar Inputs ---
st.sidebar.header("Core Parameters")
principal = st.sidebar.number_input("Mortgage Amount (£)", value=260000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
salary = st.sidebar.number_input("Annual Salary (£)", value=67000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000)
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
sal_growth = 0.01 # 1% as requested
employer_match = 0.10

st.sidebar.header("Contribution Shift")
old_sac = st.sidebar.slider("Baseline Sacrifice (%)", 0, 20, 7) / 100
new_sac = st.sidebar.slider("New Strategy Sacrifice (%)", 0, 20, 10) / 100

# --- Helper Functions ---
def calculate_strategy(term, sacrifice):
    monthly_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    total_interest = (monthly_pmt * term * 12) - principal
    
    # Take Home Calculation (Simplified 42% tax/NI saving for higher rate)
    diff_sacrifice_monthly = (salary * (sacrifice - old_sac)) / 12
    take_home_delta = -(diff_sacrifice_monthly * 0.58) if sacrifice > old_sac else 0
    
    # Find the Break-even year (25% lump sum == Mortgage Balance)
    break_even_yr = "Never"
    current_pot = initial_pension
    for yr in range(1, 41):
        yearly_contrib = (salary * (1 + sal_growth)**yr) * (sacrifice + employer_match)
        current_pot = (current_pot + yearly_contrib) * (1 + p_growth)
        
        # Balance remaining on mortgage
        bal = abs(npf.fv(m_interest/12, yr*12, monthly_pmt, -principal))
        if (current_pot * 0.25) >= bal:
            break_even_yr = yr
            break
            
    return monthly_pmt, take_home_delta, break_even_yr, total_interest

# --- Compute Data ---
s1_mtg, s1_take, s1_yr, s1_int = calculate_strategy(17, old_sac)
s2_mtg, s2_take, s2_yr, s2_int = calculate_strategy(25, new_sac)
s3_mtg, s3_take, s3_yr, s3_int = calculate_strategy(30, new_sac)

# --- Comparison Table ---
data = {
    "Metric": [
        "Monthly Mortgage Payment", 
        "Change in Take-Home Pay", 
        "Years until 25% Lump Sum = Mortgage", 
        "Total Interest Paid to Bank"
    ],
    "17-Year (Current Plan)": [
        f"£{s1_mtg:,.2f}", "Baseline", f"{s1_yr} years", f"£{s1_int:,.2f}"
    ],
    "25-Year + Higher Sacrifice": [
        f"£{s2_mtg:,.2f}", f"£{s2_take:,.2f}", f"{s2_yr} years", f"£{s2_int:,.2f}"
    ],
    "30-Year + Higher Sacrifice": [
        f"£{s3_mtg:,.2f}", f"£{s3_take:,.2f}", f"{s3_yr} years", f"£{s3_int:,.2f}"
    ]
}

st.table(pd.DataFrame(data))

st.info("""
**Note on the Break-even Year:** This is the mathematical 'Tipping Point.' 
If the break-even is year 12, it means at age 55 you could theoretically pay off the entire remaining 
debt using only your tax-free lump sum.
""")

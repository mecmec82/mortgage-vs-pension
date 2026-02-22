import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Pension vs Mortgage Strategy", layout="wide")

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
    # Balance remaining at age 60
    bal_at_60 = abs(npf.fv(m_interest/12, sim_years*12, monthly_pmt, -principal))
    
    # 2. Pension Projection
    current_pot = initial_pension
    for yr in range(1, sim_years + 1):
        yearly_contrib = (salary * (1 + sal_growth)**yr) * (sacrifice + employer_match)
        current_pot = (current_pot + yearly_contrib) * (1 + p_growth)
    
    # 3. Take Home Pay Impact
    diff_sacrifice_monthly = (salary * (sacrifice - old_sac)) / 12
    take_home_delta = -(diff_sacrifice_monthly * 0.58) if sacrifice > old_sac else 0
    
    # 4. Net Wealth Logic
    lump_sum = current_pot * 0.25
    remaining_pension_after_lump = current_pot * 0.75
    # What is left AFTER using the lump sum to clear the mortgage?
    net_lump_sum_left = max(0, lump_sum - bal_at_60)
    total_wealth_at_60 = remaining_pension_after_lump + net_lump_sum_left
    
    return monthly_pmt, take_home_delta, bal_at_60, current_pot, lump_sum, total_wealth_at_60

# --- Execution ---
s1 = calculate_wealth_at_60(17, old_sac)
s2 = calculate_wealth_at_60(25, new_sac)
s3 = calculate_wealth_at_60(30, new_sac)

# --- UI Layout ---
st.title("🏠 Retirement Wealth Strategy Dashboard")

with st.expander("ℹ️ Why am I better off with a longer mortgage? (The 'Tax Arbitrage' Explainer)"):
    st.write("""
    ### 1. The 42% Head-Start
    As a higher-rate taxpayer, every £1,000 you put into a mortgage costs you **£1,000 of take-home pay**. 
    But every £1,000 put into your pension via salary sacrifice only costs you **£580 of take-home pay** (because you save 40% Income Tax and 2% NI). 
    You are essentially investing with "The Government's Money."
    
    ### 2. Compound Growth vs. Debt
    Mortgage interest is a 'linear' cost on a shrinking balance. Pension growth is 'exponential' on a growing balance. 
    By keeping your mortgage term long, you keep more money in the "Growth" bucket for longer.
    
    ### 3. The 'Final Swap' at 60
    The goal isn't to have a mortgage forever. The goal is to use the **Tax-Free Lump Sum** at age 60 to wipe out the mortgage. 
    Because that money grew inside the pension untaxed, the "surplus" cash you have left over is much higher than the money you would have saved by paying the mortgage off early.
    """)
    

# --- Comparison Table ---
st.subheader("Comparison Table: Age 60 Projection")
data = {
    "Metric": [
        "Monthly Mortgage Payment",
        "Change in Monthly Take-Home",
        "Mortgage Debt Remaining at 60",
        "Total Pension Pot at 60",
        "25% Tax-Free Lump Sum",
        "Cash Left After Clearing Debt",
        "Total Net Wealth (Pension + Surplus Cash)",
        "Strategy Gain vs. Baseline"
    ],
    "Baseline (17yr/7%)": [
        f"£{s1[0]:,.2f}", "Baseline", f"£{s1[2]:,.2f}", f"£{s1[3]:,.2f}", 
        f"£{s1[4]:,.2f}", f"£{s1[4]-s1[2]:,.2f}", f"£{s1[5]:,.2f}", "Baseline"
    ],
    "Strategy A (25yr/10%)": [
        f"£{s2[0]:,.2f}", f"£{s2[1]:,.2f}", f"£{s2[2]:,.2f}", f"£{s2[3]:,.2f}", 
        f"£{s2[4]:,.2f}", f"£{s2[4]-s2[2]:,.2f}", f"£{s2[5]:,.2f}", f"£{s2[5]-s1[5]:,.2f}"
    ],
    "Strategy B (30yr/10%)": [
        f"£{s3[0]:,.2f}", f"£{s3[1]:,.2f}", f"£{s3[2]:,.2f}", f"£{s3[3]:,.2f}", 
        f"£{s3[4]:,.2f}", f"£{s3[4]-s3[2]:,.2f}", f"£{s3[5]:,.2f}", f"£{s3[5]-s1[5]:,.2f}"
    ]
}

st.table(pd.DataFrame(data))

st.success(f"**The Verdict:** By choosing Strategy B, you end up with **£{s3[5]-s1[5]:,.0f}** more total wealth at age 60 compared to your current plan, even after paying off the house.")

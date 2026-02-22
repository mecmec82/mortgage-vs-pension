import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="The Long Leverage Strategy", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("Personal Details")
current_age = 43
access_age = 57
final_payoff_age = 70
sim_years = final_payoff_age - current_age

principal = st.sidebar.number_input("Mortgage Amount (£)", value=260000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
salary = st.sidebar.number_input("Annual Salary (£)", value=67000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000)
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
sal_growth = 0.01 
employer_match = 0.10

old_sac = st.sidebar.slider("Baseline Sacrifice (%)", 0, 20, 7) / 100
new_sac = st.sidebar.slider("New Strategy Sacrifice (%)", 0, 20, 10) / 100

def calculate_friction_strategy(term, sacrifice):
    # 1. Initial Monthly Payment
    monthly_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    
    # 2. Simulate years 43 to 70
    m_balance = principal
    p_pot = initial_pension
    lump_sum_vault = 0
    total_interest_paid = 0
    
    for yr in range(1, sim_years + 1):
        age = current_age + yr
        
        # Pension Growth
        yearly_contrib = (salary * (1 + sal_growth)**yr) * (sacrifice + employer_match)
        p_pot = (p_pot + yearly_contrib) * (1 + p_growth)
        
        # Mortgage Interest and Standard Payments
        for month in range(12):
            interest_charge = m_balance * (m_interest / 12)
            total_interest_paid += interest_charge
            principal_paid = monthly_pmt - interest_charge
            m_balance -= principal_paid
            
        # 3. Access 25% at Age 57
        if age == access_age:
            lump_sum_vault = p_pot * 0.25
            p_pot = p_pot * 0.75
            
        # 4. Overpayment Logic (10% limit) from age 57 onwards
        if age >= access_age and age < final_payoff_age and lump_sum_vault > 0:
            overpay_limit = m_balance * 0.10
            actual_overpay = min(overpay_limit, lump_sum_vault)
            m_balance -= actual_overpay
            lump_sum_vault -= actual_overpay
            
    # 5. Final Payoff at 70
    exit_fee = m_balance * 0.02
    final_cost_to_clear = m_balance + exit_fee
    remaining_cash = lump_sum_vault - final_cost_to_clear
    
    # Total Wealth = Remaining 75% pot (which grew) + leftover cash from the 25% vault
    total_wealth = p_pot + remaining_cash
    
    return monthly_pmt, m_balance, p_pot, total_wealth, total_interest_paid

# --- Execution ---
s1 = calculate_friction_strategy(17, old_sac) # Baseline
s2 = calculate_friction_strategy(25, new_sac) # Strategy A
s3 = calculate_friction_strategy(30, new_sac) # Strategy B

# --- UI ---
st.title("🏠 The 'Stay Leveraged' Strategy (Age 70 Target)")

with st.expander("📝 Strategy Logic: Friction & Growth"):
    st.write(f"""
    - **Ages 43-57:** You maximize pension sacrifice, letting the gross amount compound.
    - **Age 57:** You 'earmark' 25% of the pot (£{s3[2]*0.33:,.0f} approx) for the mortgage.
    - **Ages 57-69:** You overpay 10% of the balance annually from that tax-free vault.
    - **Age 70:** You settle the remainder, paying a 2% penalty. 
    - **Why?** The 75% remaining in your pension is likely growing faster than the 2% fee and the mortgage interest cost.
    """)

data = {
    "Metric": [
        "Monthly Mortgage Payment",
        "Remaining Debt at Age 70 (Before Fee)",
        "Pension Pot at Age 70 (75% portion)",
        "Total Interest Paid (43 to 70)",
        "Net Wealth at 70 (After 2% Fee & Payoff)",
        "Strategy Gain vs. Baseline"
    ],
    "Baseline (17yr)": [f"£{s1[0]:,.2f}", "£0", f"£{s1[2]:,.2f}", f"£{s1[4]:,.2f}", f"£{s1[3]:,.2f}", "Baseline"],
    "Strategy A (25yr)": [f"£{s2[0]:,.2f}", f"£{s2[1]:,.2f}", f"£{s2[2]:,.2f}", f"£{s2[4]:,.2f}", f"£{s2[3]:,.2f}", f"£{s2[3]-s1[3]:,.2f}"],
    "Strategy B (30yr)": [f"£{s3[0]:,.2f}", f"£{s3[1]:,.2f}", f"£{s3[2]:,.2f}", f"£{s3[4]:,.2f}", f"£{s3[3]:,.2f}", f"£{s3[3]-s1[3]:,.2f}"]
}

st.table(pd.DataFrame(data))

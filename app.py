import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Mortgage vs Pension Dashboard", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("1. Personal Details")
current_age = 43
access_age = 57
final_payoff_age = 70
sim_years = final_payoff_age - current_age

st.sidebar.header("2. Financials")
principal = st.sidebar.number_input("Mortgage Amount (£)", value=260000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
salary = st.sidebar.number_input("Annual Salary (£)", value=67000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000)
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
sal_growth = 0.01 
employer_match = 0.10

st.sidebar.header("3. Strategy Settings")
old_sac = st.sidebar.slider("Baseline Sacrifice (%)", 0, 20, 7) / 100
new_sac = st.sidebar.slider("Strategy Sacrifice (%)", 0, 25, 10) / 100

def run_simulation(term, sacrifice):
    monthly_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    m_balance = principal
    p_pot = initial_pension
    vault = 0
    total_interest_paid = 0
    balance_history = []
    
    for yr in range(1, sim_years + 2):
        age = current_age + yr - 1
        balance_history.append(max(0, m_balance))
        
        if yr <= sim_years:
            # Pension Growth
            yearly_contrib = (salary * (1 + sal_growth)**yr) * (sacrifice + employer_match)
            p_pot = (p_pot + yearly_contrib) * (1 + p_growth)
            
            # Mortgage standard amortization
            for _ in range(12):
                interest_charge = m_balance * (m_interest / 12)
                total_interest_paid += interest_charge
                m_balance -= (monthly_pmt - interest_charge)
                
            # Age 57: Move 25% to Tax-Free Vault
            if age == access_age:
                vault = p_pot * 0.25
                p_pot = p_pot * 0.75
                
            # Overpayment friction (10% limit)
            if age >= access_age and age < final_payoff_age and vault > 0:
                overpay_limit = m_balance * 0.10
                actual_overpay = min(overpay_limit, vault)
                m_balance -= actual_overpay
                vault -= actual_overpay

    # Final Payoff at 70
    exit_fee = m_balance * 0.02
    final_wealth = p_pot + (vault - (m_balance + exit_fee))
    
    return monthly_pmt, m_balance, p_pot, final_wealth, total_interest_paid, balance_history

# --- Execute ---
s1_metrics = run_simulation(17, old_sac)
s2_metrics = run_simulation(25, new_sac)
s3_metrics = run_simulation(30, new_sac)

# --- UI ---
st.title("🏠 Mortgage & Pension Strategy Dashboard")

# 1. Comparison Table
st.subheader("Strategy Comparison: Target Age 70")
data = {
    "Metric": [
        "Monthly Mortgage Payment",
        "Total Interest Paid (to Age 70)",
        "Pension Pot at 70 (75% portion)",
        "Net Wealth at 70 (After Payoff & Fees)",
        "Net Strategy Gain vs. Baseline"
    ],
    "Baseline (17yr/7%)": [
        f"£{s1_metrics[0]:,.2f}", f"£{s1_metrics[4]:,.2f}", f"£{s1_metrics[2]:,.2f}", 
        f"£{s1_metrics[3]:,.2f}", "Baseline"
    ],
    "Strategy A (25yr/New%)": [
        f"£{s2_metrics[0]:,.2f}", f"£{s2_metrics[4]:,.2f}", f"£{s2_metrics[2]:,.2f}", 
        f"£{s2_metrics[3]:,.2f}", f"£{s2_metrics[3]-s1_metrics[3]:,.2f}"
    ],
    "Strategy B (30yr/New%)": [
        f"£{s3_metrics[0]:,.2f}", f"£{s3_metrics[4]:,.2f}", f"£{s3_metrics[2]:,.2f}", 
        f"£{s3_metrics[3]:,.2f}", f"£{s3_metrics[3]-s1_metrics[3]:,.2f}"
    ]
}
st.table(pd.DataFrame(data))

# 2. Glide Path Chart
st.subheader("📉 Mortgage Balance Glide Path")
ages = list(range(current_age, final_payoff_age + 1))
chart_data = pd.DataFrame({
    "Age": ages,
    "17-Year": s1_metrics[5],
    "25-Year": s2_metrics[5],
    "30-Year": s3_metrics[5]
}).set_index("Age")
st.line_chart(chart_data)

# 3. Explainer
with st.expander("ℹ️ Why doesn't increasing pension contributions always increase net savings?"):
    st.write("""
    ### 1. The Mortgage 'Leak'
    By extending your mortgage to 30 years, you've created a 'leak' where 5% interest is charged on a large balance for a long time. If you increase your pension sacrifice, you are adding water to the bucket, but the leak is also getting bigger because the debt remains for decades.
    
    ### 2. The 10% Friction
    Because you can only pay off 10% of the mortgage per year from age 57, your extra pension money gets 'stuck' waiting to be used. While it waits, the bank continues to charge you interest on the full remaining mortgage balance.
    
    ### 3. Tax Relief Ceiling
    Once your taxable salary drops below £50,270, your tax relief drops from 40% to 20%. At that point, the 'profit' from the pension barely beats the 'cost' of a 5% mortgage.
    """)

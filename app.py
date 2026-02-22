import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Strategic Mortgage & Pension Dashboard", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("1. Core Variables")
principal = st.sidebar.number_input("Mortgage Amount (£)", value=260000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
salary = st.sidebar.number_input("Current Annual Salary (£)", value=67000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000)
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100

st.sidebar.header("2. Comparison Settings")
old_sac = st.sidebar.slider("Baseline Sacrifice (%)", 0, 20, 7) / 100
new_sac = st.sidebar.slider("Strategy Sacrifice (%)", 0, 25, 10) / 100

# Constants
current_age = 43
access_age = 57
final_age = 70
sal_growth = 0.01
emp_match = 0.10

# --- Helper Functions ---
def get_monthly_net_income(gross_annual, sacrifice_pct):
    """Calculates UK Monthly Take-Home after Tax/NI and Sacrifice."""
    sacrifice = gross_annual * sacrifice_pct
    taxable = gross_annual - sacrifice
    pa, br_limit = 12570, 50270
    
    # Income Tax (24/25)
    tax = 0
    if taxable > pa:
        tax = min(taxable - pa, br_limit - pa) * 0.20
        if taxable > br_limit:
            tax += (taxable - br_limit) * 0.40
            
    # NI (8% main, 2% higher)
    ni = 0
    if taxable > pa:
        ni = min(taxable - pa, br_limit - pa) * 0.08
        if taxable > br_limit:
            ni += (taxable - br_limit) * 0.02
            
    return (taxable - tax - ni) / 12

def simulate_strategy(term, sacrifice):
    m_balance = principal
    p_pot = initial_pension
    vault = 0
    total_interest = 0
    history = []
    
    # Initial PMT
    current_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    
    for age in range(current_age, final_age + 1):
        year_idx = age - current_age
        current_sal = salary * ((1 + sal_growth)**year_idx)
        monthly_take_home = get_monthly_net_income(current_sal, sacrifice)
        
        # Monthly mortgage payment for this year
        actual_pmt = current_pmt if m_balance > 0 else 0
        
        # Yearly Interest and Amortization
        for _ in range(12):
            if m_balance > 0:
                interest = m_balance * (m_interest / 12)
                total_interest += interest
                m_balance -= (actual_pmt - interest)
        
        # Pension Growth
        p_pot = (p_pot + (current_sal * (sacrifice + emp_match))) * (1 + p_growth)
        
        # Age 57: Extract 25% Vault
        if age == access_age:
            vault = p_pot * 0.25
            p_pot = p_pot * 0.75
            
        # Overpayment & Recalculation (Age 57-69)
        if access_age <= age < final_age and vault > 0 and m_balance > 0:
            overpay = min(m_balance * 0.10, vault)
            m_balance -= overpay
            vault -= overpay
            
            # Recalculate PMT for next year based on remaining term
            rem_months = (term * 12) - ((year_idx + 1) * 12)
            if rem_months > 0 and m_balance > 0:
                current_pmt = abs(npf.pmt(m_interest/12, rem_months, m_balance))
            else:
                current_pmt = 0
        
        history.append({
            "Age": age,
            "Balance": max(0, m_balance),
            "Monthly_Payment": actual_pmt,
            "Net_Monthly_Income": monthly_take_home - actual_pmt,
            "Pot": p_pot,
            "Vault": vault
        })
        
    # Final cleanup at age 70
    final_debt = m_balance * 1.02 # 2% fee
    final_wealth = p_pot + (vault - final_debt)
    return history, total_interest, final_wealth

# --- Run Simulations ---
h1, int1, w1 = simulate_strategy(17, old_sac)
h2, int2, w2 = simulate_strategy(25, new_sac)
h3, int3, w3 = simulate_strategy(30, new_sac)

# --- UI Presentation ---
st.title("🏦 Advanced Lifecycle Wealth Dashboard")

# 1. Comparison Table
st.subheader("High-Level Comparison (at Age 70)")
table_data = {
    "Strategy": ["Baseline (17yr/7%)", "New A (25yr/10%)", "New B (30yr/10%)"],
    "Initial Monthly Mortgage": [f"£{h1[0]['Monthly_Payment']:,.0f}", f"£{h2[0]['Monthly_Payment']:,.0f}", f"£{h3[0]['Monthly_Payment']:,.0f}"],
    "Total Interest Paid": [f"£{int1:,.0f}", f"£{int2:,.0f}", f"£{int3:,.0f}"],
    "Net Wealth at 70": [f"£{w1:,.0f}", f"£{w2:,.0f}", f"£{w3:,.0f}"],
    "Total Strategy Gain": ["-", f"£{w2-w1:,.0f}", f"£{w3-w1:,.0f}"]
}
st.table(pd.DataFrame(table_data))

# 2. Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📉 Mortgage Balance Glide Path")
    b_df = pd.DataFrame({"Age": [x['Age'] for x in h1], "17yr": [x['Balance'] for x in h1], "25yr": [x['Balance'] for x in h2], "30yr": [x['Balance'] for x in h3]}).set_index("Age")
    st.line_chart(b_df)

with col2:
    st.subheader("💸 Monthly Mortgage Payment")
    p_df = pd.DataFrame({"Age": [x['Age'] for x in h1], "17yr": [x['Monthly_Payment'] for x in h1], "25yr": [x['Monthly_Payment'] for x in h2], "30yr": [x['Monthly_Payment'] for x in h3]}).set_index("Age")
    st.line_chart(p_df)

st.subheader("💰 Net Monthly Income (After Mortgage & Pension)")
i_df = pd.DataFrame({"Age": [x['Age'] for x in h1], "Baseline": [x['Net_Monthly_Income'] for x in h1], "Strategy A": [x['Net_Monthly_Income'] for x in h2], "Strategy B": [x['Net_Monthly_Income'] for x in h3]}).set_index("Age")
st.line_chart(i_df)

# 3. Explainer
with st.expander("📝 Why does Net Income jump and drop?"):
    st.write("""
    1. **The 17-Year Spike:** In the baseline, your net income jumps massively at age 60 because the mortgage is paid off. 
    2. **The 25/30-Year Glide:** From age 57, your net income starts 'climbing' every year. This is because we are using your pension vault to overpay by 10%, causing the bank to recalculate and lower your monthly bill.
    3. **Strategy B Winner:** Even though the baseline has a 10-year 'head start' on high disposable income, Strategy B usually wins on **Total Wealth** because the pension growth on your £175k pot (plus contributions) is compounding on a much larger scale than the interest being charged.
    """)

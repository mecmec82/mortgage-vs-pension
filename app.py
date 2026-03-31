import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Mortgage vs Pension Strategy", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("1. Personal Details")
current_age = st.sidebar.number_input("Current Age", value=43, min_value=18, max_value=70)
salary = st.sidebar.number_input("Current Annual Salary (£)", value=67500, step=1000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=170000, step=5000)

st.sidebar.header("2. Mortgage & Finance")
principal = st.sidebar.number_input("Mortgage Principal (£)", value=270000, step=5000)
current_house_val = st.sidebar.number_input("Current House Value (£)", value=450000, step=10000)
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
h_growth = st.sidebar.slider("House Appreciation (%)", 0.0, 5.0, 2.0) / 100
strategy_term = st.sidebar.slider("New Mortgage Length (Years)", 18, 40, 23)

# Constants
access_age = 57
final_age = 70
sal_growth = 0.01
emp_match = 0.10
baseline_term = 18
baseline_sacrifice = 0.07

# --- Logic: Back-Calculation ---
pmt_baseline = abs(npf.pmt(m_interest/12, baseline_term*12, principal))
pmt_strategy = abs(npf.pmt(m_interest/12, strategy_term*12, principal))
monthly_mortgage_saving = pmt_baseline - pmt_strategy
extra_gross_pension_monthly = monthly_mortgage_saving / 0.58
extra_sacrifice_pct = (extra_gross_pension_monthly * 12) / salary
strategy_sacrifice = baseline_sacrifice + extra_sacrifice_pct

def simulate(term, sacrifice):
    m_balance = principal
    p_pot = initial_pension
    vault = 0
    total_interest = 0
    history = []
    current_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    
    for yr_idx in range(final_age - current_age + 1):
        age = current_age + yr_idx
        house_val = current_house_val * (1 + h_growth)**yr_idx
        cur_sal = salary * (1 + sal_growth)**yr_idx
        
        # 1. Take Tax-Free Lump Sum at 57
        if age == access_age:
            lump_sum = p_pot * 0.25
            p_pot -= lump_sum
            vault += lump_sum
            
        # 2. Annual Mortgage Payments & Interest
        monthly_take_home = 0 # Placeholder for income chart
        for _ in range(12):
            if m_balance > 0:
                interest = m_balance * (m_interest / 12)
                total_interest += interest
                m_balance -= (current_pmt - interest)
        
        # 3. Apply Vault to Mortgage (Capped at 10% of original principal per year)
        if vault > 0 and m_balance > 0:
            annual_cap = principal * 0.10
            overpay = min(vault, annual_cap, m_balance)
            m_balance -= overpay
            vault -= overpay
            # Recalculate remaining payments after overpayment
            rem_months = (term * 12) - ((yr_idx + 1) * 12)
            if rem_months > 0 and m_balance > 0:
                current_pmt = abs(npf.pmt(m_interest/12, rem_months, m_balance))
            else:
                current_pmt = 0
        
        # 4. Pension Growth
        p_pot = (p_pot + (cur_sal * (sacrifice + emp_match))) * (1 + p_growth)
        
        # 5. Net Worth Calculation
        net_worth = house_val - max(0, m_balance) + p_pot + vault
        
        history.append({
            "Age": age, 
            "M_Balance": max(0, m_balance), 
            "P_Balance": p_pot, 
            "Net_Worth": net_worth,
            "Monthly_Pmt": current_pmt if m_balance > 0 else 0
        })
    
    return history, total_interest, net_worth

# --- Run ---
h_base, int_base, w_base = simulate(baseline_term, baseline_sacrifice)
h_strat, int_strat, w_strat = simulate(strategy_term, strategy_sacrifice)

# --- UI ---
st.title("🛡️ Mortgage Reallocation Strategy")
st.success(f"### Strategy Gain at Age 70: £{w_strat - w_base:,.0f}")

col1, col2 = st.columns(2)
with col1:
    st.write("**Pension Balance (£)**")
    st.line_chart(pd.DataFrame({
        "Age": [x['Age'] for x in h_base], 
        "Baseline": [x['P_Balance'] for x in h_base], 
        "Strategy": [x['P_Balance'] for x in h_strat]
    }).set_index("Age"))
    st.caption("Note the drop at age 57 where 25% is moved to pay down the mortgage.")

with col2:
    st.write("**Total Net Worth (£)**")
    st.line_chart(pd.DataFrame({
        "Age": [x['Age'] for x in h_base], 
        "Baseline": [x['Net_Worth'] for x in h_base], 
        "Strategy": [x['Net_Worth'] for x in h_strat]
    }).set_index("Age"))
    st.caption("Includes: House Value + Pension - Mortgage Balance.")

# Secondary charts
c1, c2 = st.columns(2)
with c1:
    st.write("**Mortgage Balance (£)**")
    st.line_chart(pd.DataFrame({
        "Age": [x['Age'] for x in h_base], 
        "Baseline": [x['M_Balance'] for x in h_base], 
        "Strategy": [x['M_Balance'] for x in h_strat]
    }).set_index("Age"))
with c2:
    st.write("**Monthly Payment (£)**")
    st.line_chart(pd.DataFrame({
        "Age": [x['Age'] for x in h_base], 
        "Baseline": [x['Monthly_Pmt'] for x in h_base], 
        "Strategy": [x['Monthly_Pmt'] for x in h_strat]
    }).set_index("Age"))

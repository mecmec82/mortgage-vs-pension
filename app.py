import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Mortgage Glide Path", layout="wide")

# --- Core Inputs (Sync with previous logic) ---
principal = 260000
m_interest = 0.05
salary = 67000
initial_pension = 175000
p_growth = 0.05
sal_growth = 0.01
employer_match = 0.10
current_age = 43
access_age = 57
final_payoff_age = 70

st.title("📉 Mortgage Balance Glide Path: Ages 43 to 70")
st.write("Tracking how the mortgage balance behaves across the three strategies, including the 10% overpayment phase starting at age 57.")

def get_balance_curve(term, sacrifice):
    monthly_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    balances = []
    m_balance = principal
    p_pot = initial_pension
    vault = 0
    
    for age in range(current_age, final_payoff_age + 1):
        # Record balance at start of year
        balances.append(max(0, m_balance))
        
        # 1. Standard Amortization for the year
        for _ in range(12):
            interest = m_balance * (m_interest / 12)
            m_balance -= (monthly_pmt - interest)
            
        # 2. Pension Growth (to calculate the vault at 57)
        yearly_contrib = (salary * (1 + sal_growth)**(age-current_age)) * (sacrifice + employer_match)
        p_pot = (p_pot + yearly_contrib) * (1 + p_growth)
        
        # 3. Handle the 'Vault' at age 57
        if age == access_age:
            vault = p_pot * 0.25
            
        # 4. Apply 10% Overpayment Logic (Age 57-69)
        if age >= access_age and age < final_payoff_age and vault > 0:
            limit = m_balance * 0.10
            actual_pay = min(limit, vault)
            m_balance -= actual_pay
            vault -= actual_pay
            
    return balances

# Generate Curves
ages = list(range(current_age, final_payoff_age + 1))
curve1 = get_balance_curve(17, 0.07)
curve2 = get_balance_curve(25, 0.10)
curve3 = get_balance_curve(30, 0.10)

# Build DataFrame for Plotting
plot_df = pd.DataFrame({
    "Age": ages,
    "17-Year (Current)": curve1,
    "25-Year + Pension": curve2,
    "30-Year + Pension": curve3
}).set_index("Age")

# Display Chart
st.line_chart(plot_df)

st.info("""
**Chart Breakdown:**
* **The 17-Year Curve:** Hits zero at age 60. This is the 'Debt-Free' path.
* **The 25 & 30-Year Curves:** You'll notice a 'kink' in the line at **Age 57**. This represents the moment you begin using your pension lump sum to aggressively overpay the balance by 10% each year.
* **The Tail:** The small remaining balance at Age 70 is what you settle in full (plus the 2% fee).
""")

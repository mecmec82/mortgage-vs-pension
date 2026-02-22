import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Net-Zero Strategy Dashboard", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("1. Personal Details")
current_age = st.sidebar.number_input("Current Age", value=43, min_value=18, max_value=70)
salary = st.sidebar.number_input("Current Annual Salary (£)", value=67000, step=1000)
initial_pension = st.sidebar.number_input("Current Pension Pot (£)", value=175000, step=5000)

st.sidebar.header("2. Financial Levers")
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
strategy_term = st.sidebar.slider("New Mortgage Length (Years)", 18, 40, 25)

# Fixed Baseline Parameters
principal = 260000
access_age = 57
final_age = 70
sal_growth = 0.01
emp_match = 0.10
baseline_term = 17
baseline_sacrifice = 0.07

# --- Logic: The "Back-Calculation" ---
pmt_17 = abs(npf.pmt(m_interest/12, baseline_term*12, principal))
pmt_strategy = abs(npf.pmt(m_interest/12, strategy_term*12, principal))
monthly_mortgage_saving = pmt_17 - pmt_strategy

# Convert net saving into Gross Salary Sacrifice (using 40% tax + 2% NI = 0.58 multiplier)
extra_gross_pension_monthly = monthly_mortgage_saving / 0.58
extra_sacrifice_pct = (extra_gross_pension_monthly * 12) / salary
strategy_sacrifice = baseline_sacrifice + extra_sacrifice_pct

# --- Helper Functions ---
def get_monthly_net_income(gross_annual, sacrifice_pct):
    sacrifice = gross_annual * sacrifice_pct
    taxable = gross_annual - sacrifice
    pa, br_limit = 12570, 50270
    tax = 0
    if taxable > pa:
        tax = min(taxable - pa, br_limit - pa) * 0.20
        if taxable > br_limit: tax += (taxable - br_limit) * 0.40
    ni = 0
    if taxable > pa:
        ni = min(taxable - pa, br_limit - pa) * 0.08
        if taxable > br_limit: ni += (taxable - br_limit) * 0.02
    return (taxable - tax - ni) / 12

def simulate_strategy(term, sacrifice):
    m_balance = principal
    p_pot = initial_pension
    vault = 0
    total_interest = 0
    history = []
    current_pmt = abs(npf.pmt(m_interest/12, term*12, principal))
    sim_years = final_age - current_age
    
    for yr_idx in range(sim_years + 1):
        age = current_age + yr_idx
        current_sal = salary * ((1 + sal_growth)**yr_idx)
        monthly_take_home = get_monthly_net_income(current_sal, sacrifice)
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
            
            # Recalculate remaining term for next year's PMT
            rem_months = (term * 12) - ((yr_idx + 1) * 12)
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
        
    final_wealth = p_pot + (vault - (m_balance * 1.02))
    return history, total_interest, final_wealth

# --- Execution ---
h_base, int_base, w_base = simulate_strategy(baseline_term, baseline_sacrifice)
h_strat, int_strat, w_strat = simulate_strategy(strategy_term, strategy_sacrifice)

# --- Dashboard View ---
st.title("🛡️ Net-Zero Lifestyle Wealth Strategy")
st.write(f"Reallocating **£{monthly_mortgage_saving:,.2f}/mo** mortgage saving into a **£{extra_gross_pension_monthly:,.2f}/mo** pension contribution.")

# 1. Comparison Table
st.subheader("Comparison Table: Reallocation Strategy")
table_data = {
    "Metric": [
        "Mortgage Length (Years)", 
        "Monthly Mortgage Reduction",
        "Extra Monthly Pension (Gross)",
        "Total Pension Contribution (%)",
        "Total Interest Paid (to Age 70)", 
        "Net Wealth at 70 (After Payoff)"
    ],
    "Baseline Plan": [
        "17 Years", "-", "-", f"{baseline_sacrifice*100:.1f}%", f"£{int_base:,.0f}", f"£{w_base:,.0f}"
    ],
    "Optimized Strategy": [
        f"{strategy_term} Years", 
        f"£{monthly_mortgage_saving:,.2f}", 
        f"£{extra_gross_pension_monthly:,.2f}", 
        f"{strategy_sacrifice*100:.1f}%", 
        f"£{int_strat:,.0f}", 
        f"£{w_strat:,.0f}"
    ]
}
st.table(pd.DataFrame(table_data))

# 2. Charts
c1, c2, c3 = st.columns(3)
with c1:
    st.write("**Mortgage Balance (£)**")
    st.line_chart(pd.DataFrame({"Age": [x['Age'] for x in h_base], "Baseline": [x['Balance'] for x in h_base], "Strategy": [x['Balance'] for x in h_strat]}).set_index("Age"))
with c2:
    st.write("**Monthly Mortgage Cost (£)**")
    st.line_chart(pd.DataFrame({"Age": [x['Age'] for x in h_base], "Baseline": [x['Monthly_Payment'] for x in h_base], "Strategy": [x['Monthly_Payment'] for x in h_strat]}).set_index("Age"))
with c3:
    st.write("**Net Monthly Income (£)**")
    st.line_chart(pd.DataFrame({"Age": [x['Age'] for x in h_base], "Baseline": [x['Net_Monthly_Income'] for x in h_base], "Strategy": [x['Net_Monthly_Income'] for x in h_strat]}).set_index("Age"))

st.success(f"**Total Strategy Gain at Age 70:** £{w_strat - w_base:,.0f} extra wealth.")

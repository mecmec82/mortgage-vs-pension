import streamlit as st
import pandas as pd
import numpy_financial as npf

st.set_page_config(page_title="Net-Zero Strategy Dashboard", layout="wide")

# --- Sidebar Inputs ---
st.sidebar.header("1. Fixed Parameters")
principal = 260000
salary = 67000
initial_pension = 175000
current_age = 43
access_age = 57
final_age = 70
sal_growth = 0.01
emp_match = 0.10
baseline_term = 17
baseline_sacrifice = 0.07

st.sidebar.header("2. Variables")
m_interest = st.sidebar.slider("Mortgage Interest Rate (%)", 1.0, 10.0, 5.0) / 100
p_growth = st.sidebar.slider("Pension Growth (%)", 1.0, 10.0, 5.0) / 100
strategy_term = st.sidebar.slider("Strategy Mortgage Length (Years)", 18, 40, 25)

# --- Logic: The "Back-Calculation" ---
# 1. Calculate the monthly saving in mortgage payments
pmt_17 = abs(npf.pmt(m_interest/12, baseline_term*12, principal))
pmt_strategy = abs(npf.pmt(m_interest/12, strategy_term*12, principal))
monthly_saving = pmt_17 - pmt_strategy

# 2. Convert that net saving into a Gross Salary Sacrifice %
# To get £1 net, you need £1.72 gross (at 42% tax/NI saving) -> 1 / 0.58
gross_equivalent_monthly = monthly_saving / 0.58
annual_extra_sacrifice = gross_equivalent_monthly * 12
extra_sacrifice_pct = annual_extra_sacrifice / salary
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
    
    for age in range(current_age, final_age + 1):
        year_idx = age - current_age
        current_sal = salary * ((1 + sal_growth)**year_idx)
        monthly_take_home = get_monthly_net_income(current_sal, sacrifice)
        actual_pmt = current_pmt if m_balance > 0 else 0
        
        for _ in range(12):
            if m_balance > 0:
                interest = m_balance * (m_interest / 12)
                total_interest += interest
                m_balance -= (actual_pmt - interest)
        
        p_pot = (p_pot + (current_sal * (sacrifice + emp_match))) * (1 + p_growth)
        if age == access_age:
            vault = p_pot * 0.25
            p_pot = p_pot * 0.75
            
        if access_age <= age < final_age and vault > 0 and m_balance > 0:
            overpay = min(m_balance * 0.10, vault)
            m_balance -= overpay
            vault -= overpay
            rem_months = (term * 12) - ((year_idx + 1) * 12)
            if rem_months > 0 and m_balance > 0:
                current_pmt = abs(npf.pmt(m_interest/12, rem_months, m_balance))
            else:
                current_pmt = 0
        
        history.append({"Age": age, "Balance": max(0, m_balance), "Monthly_Payment": actual_pmt, "Net_Monthly_Income": monthly_take_home - actual_pmt, "Pot": p_pot, "Vault": vault})
        
    final_wealth = p_pot + (vault - (m_balance * 1.02))
    return history, total_interest, final_wealth

# --- Run ---
h1, int1, w1 = simulate_strategy(baseline_term, baseline_sacrifice)
h_strat, int_strat, w_strat = simulate_strategy(strategy_term, strategy_sacrifice)

# --- UI ---
st.title("🛡️ Net-Zero Lifestyle Wealth Strategy")
st.markdown(f"**The Goal:** Maintain your current net income, but reallocate the **£{monthly_saving:,.2f}/mo** saved from a longer mortgage into your pension.")

col_a, col_b = st.columns(2)
col_a.metric("New Calculated Sacrifice", f"{strategy_sacrifice*100:.2f}%", f"+{(extra_sacrifice_pct*100):.2f}% from Baseline")
col_b.metric("Projected Wealth Gain at 70", f"£{w_strat - w1:,.0f}")

# 1. Comparison Table
st.subheader("Strategy Comparison (Age 43 to 70)")
table_data = {
    "Metric": ["Mortgage Length", "Total Pension Contribution", "Net Monthly Income (Age 43)", "Total Interest Paid to Bank", "Net Wealth at 70 (After Payoff)"],
    "Baseline Plan": ["17 Years", f"{baseline_sacrifice*100:.1f}%", f"£{h1[0]['Net_Monthly_Income']:,.2f}", f"£{int1:,.0f}", f"£{w1:,.0f}"],
    "Optimized Strategy": [f"{strategy_term} Years", f"{strategy_sacrifice*100:.1f}%", f"£{h_strat[0]['Net_Monthly_Income']:,.2f}", f"£{int_strat:,.0f}", f"£{w_strat:,.0f}"]
}
st.table(pd.DataFrame(table_data))

# 2. Charts
c1, c2, c3 = st.columns(3)
with c1:
    st.write("**Mortgage Balance**")
    st.line_chart(pd.DataFrame({"Age": [x['Age'] for x in h1], "Baseline": [x['Balance'] for x in h1], "Strategy": [x['Balance'] for x in h_strat]}).set_index("Age"))
with c2:
    st.write("**Monthly Mortgage Cost**")
    st.line_chart(pd.DataFrame({"Age": [x['Age'] for x in h1], "Baseline": [x['Monthly_Payment'] for x in h1], "Strategy": [x['Monthly_Payment'] for x in h_strat]}).set_index("Age"))
with c3:
    st.write("**Net Monthly Income**")
    st.line_chart(pd.DataFrame({"Age": [x['Age'] for x in h1], "Baseline": [x['Net_Monthly_Income'] for x in h1], "Strategy": [x['Net_Monthly_Income'] for x in h_strat]}).set_index("Age"))

with st.expander("ℹ️ How the back-calculation works"):
    st.write(f"""
    1. We calculate the monthly payment for a 17-year mortgage: **£{pmt_17:,.2f}**.
    2. We calculate the payment for a {strategy_term}-year mortgage: **£{pmt_strategy:,.2f}**.
    3. The difference is **£{monthly_saving:,.2f}** in your pocket.
    4. To keep your take-home pay the same, we increase your pension sacrifice by **£{gross_equivalent_monthly:,.2f}** gross. 
    5. Because of the 40% tax relief and 2% NI saving, that **£{gross_equivalent_monthly:,.2f}** only reduces your take-home pay by exactly **£{monthly_saving:,.2f}**, cancelling it out.
    """)

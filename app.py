import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def add_text_logo():
    st.sidebar.markdown(
        """
        <style>
        .logo-text {
            font-size: 24px;
            font-weight: bold;
            color: #4682B4;
            text-align: left;
            margin-left: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<p class="logo-text">CompCal</p>', unsafe_allow_html=True)

def calculate_equity(performance, benchmarks, equity_level, growth_rates):
    if performance <= benchmarks['Median']:
        return equity_level['Minimum'] + (equity_level['Median'] - equity_level['Minimum']) * (performance / benchmarks['Median']) ** growth_rates['Min to Median']
    elif performance <= benchmarks['Top Quartile']:
        return equity_level['Median'] + (equity_level['Top Quartile'] - equity_level['Median']) * ((performance - benchmarks['Median']) / (benchmarks['Top Quartile'] - benchmarks['Median'])) ** growth_rates['Median to Top Quartile']
    elif performance <= benchmarks['Top Decile']:
        return equity_level['Top Quartile'] + (equity_level['Top Decile'] - equity_level['Top Quartile']) * ((performance - benchmarks['Top Quartile']) / (benchmarks['Top Decile'] - benchmarks['Top Quartile'])) ** growth_rates['Top Quartile to Top Decile']
    else:
        return equity_level['Top Decile'] + (equity_level['Maximum'] - equity_level['Top Decile']) * ((performance - benchmarks['Top Decile']) / benchmarks['Top Decile']) ** growth_rates['Above Top Decile']

def calculate_proportional_bonus(actual_revenue, target_revenue, base_salary, bonus_base_percentage):
    return (actual_revenue / target_revenue) * (base_salary * (bonus_base_percentage / 100))

def calculate_excess_revenue_bonus(actual_revenue, target_revenue, exchange_rate, excess_bonus_percentage):
    # Calculate the excess revenue in USD
    excess_revenue_usd = actual_revenue - target_revenue
    
    # Only consider positive excess revenue
    if excess_revenue_usd > 0:
        # Convert the excess revenue to INR
        excess_revenue_inr = excess_revenue_usd * exchange_rate * 1000000
        
        # Calculate the excess bonus in INR
        excess_bonus = excess_revenue_inr * (excess_bonus_percentage / 100) * (1/100000)
    else:
        # If excess revenue is not positive, the bonus is zero
        excess_bonus = 0
    
    return excess_bonus

def calculate_compensation(revenue, year, benchmarks, base_salary, joining_bonus, equity_level, bonus_base_percentage, excess_bonus_percentage, free_cash_flow, growth_rates, exchange_rate):
    equity = calculate_equity(revenue, benchmarks, equity_level, growth_rates)
    
    target_revenue = benchmarks['Top Quartile']
    
    # Proportional Bonus Method
    proportional_bonus = calculate_proportional_bonus(revenue, target_revenue, base_salary, bonus_base_percentage)
    total_comp_proportional = base_salary + proportional_bonus
    
    if year == 1:
        # total_comp_proportional += joining_bonus
        total_comp_proportional = max(0, total_comp_proportional - joining_bonus)
    
    # Excess Revenue Bonus Method
    excess_bonus = calculate_excess_revenue_bonus(revenue, target_revenue, exchange_rate, excess_bonus_percentage)
    base_bonus = base_salary * (bonus_base_percentage / 100)
    
    total_bonus_excess = base_bonus + excess_bonus
    
    if year == 1:
        total_bonus_excess = max(0, total_bonus_excess - joining_bonus)
    
    total_comp_excess = base_salary + total_bonus_excess
    
    # if year == 1:
    #     total_comp_excess += joining_bonus
    
    return equity, proportional_bonus, total_comp_proportional, base_bonus, excess_bonus, total_comp_excess


def save_results(results_df, fig):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        results_df.to_excel(writer, sheet_name='Compensation Results')
        workbook = writer.book
        worksheet = writer.sheets['Compensation Results']
        
        chart_img = BytesIO()
        fig.savefig(chart_img, format='png')
        worksheet.insert_image('M2', '', {'image_data': chart_img})
        
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="compensation_results.xlsx">Download Results</a>'
    return href

def main():
    st.set_page_config(layout="wide")
    add_text_logo()
    st.title("SaaS Compensation Calculator")

    st.sidebar.header("Input Parameters")
    exchange_rate = st.sidebar.number_input("USD to INR Exchange Rate", min_value=1.0, value=83.0, step=0.1, format="%.1f")
    
    st.sidebar.subheader("Salary and Bonus Parameters")
    initial_base_salary_lakhs = st.sidebar.number_input("Initial Base Salary (Lakhs INR)", min_value=0.0, value=25.0, step=1.0, format="%.1f")
    joining_bonus_lakhs = st.sidebar.number_input("Joining Bonus (Lakhs INR)", min_value=0.0, value=10.0, step=1.0, format="%.1f")
    salary_increase_rate = st.sidebar.number_input("Annual Salary Increase Rate (%)", min_value=0.0, value=10.0, step=0.1, format="%.1f") / 100
    st.sidebar.subheader("Bonus Parameters")
    bonus_base_percentage = st.sidebar.number_input("Bonus Base (% of Base Salary)", min_value=0.0, value=125.0, step=1.0, format="%.1f")
    excess_bonus_percentage = st.sidebar.number_input("Excess Bonus (% of Base Salary per $1M Excess Revenue)", min_value=0.0, value=10.0, step=0.1, format="%.1f")

    st.sidebar.subheader("Equity Parameters")
    st.sidebar.write("Specify the equity percentages for each year at different performance levels:")
    equity_levels = []
    
    for year in range(1, 5):
        year_equity = {}
        col1, col2, col3, col4, col5 = st.sidebar.columns(5)

        # Set the default values based on the year
        if year == 1:
            year_equity['Minimum'] = col1.number_input(f"Min Y{year}", key=f"min_eq_{year}", value=1.0, step=0.1, format="%.1f")
            year_equity['Median'] = col2.number_input(f"Med Y{year}", key=f"med_eq_{year}", value=2.0, step=0.1, format="%.1f")
            year_equity['Top Quartile'] = col3.number_input(f"TQ Y{year}", key=f"tq_eq_{year}", value=3.0, step=0.1, format="%.1f")
            year_equity['Top Decile'] = col4.number_input(f"TD Y{year}", key=f"td_eq_{year}", value=4.0, step=0.1, format="%.1f")
            year_equity['Maximum'] = col5.number_input(f"Max Y{year}", key=f"max_eq_{year}", value=5.0, step=0.1, format="%.1f")
        elif year == 2:
            year_equity['Minimum'] = col1.number_input(f"Min Y{year}", key=f"min_eq_{year}", value=1.0, step=0.1, format="%.1f")
            year_equity['Median'] = col2.number_input(f"Med Y{year}", key=f"med_eq_{year}", value=2.0, step=0.1, format="%.1f")
            year_equity['Top Quartile'] = col3.number_input(f"TQ Y{year}", key=f"tq_eq_{year}", value=3.0, step=0.1, format="%.1f")
            year_equity['Top Decile'] = col4.number_input(f"TD Y{year}", key=f"td_eq_{year}", value=4.0, step=0.1, format="%.1f")
            year_equity['Maximum'] = col5.number_input(f"Max Y{year}", key=f"max_eq_{year}", value=5.0, step=0.1, format="%.1f")
        elif year == 3:
            year_equity['Minimum'] = col1.number_input(f"Min Y{year}", key=f"min_eq_{year}", value=1.0, step=0.1, format="%.1f")
            year_equity['Median'] = col2.number_input(f"Med Y{year}", key=f"med_eq_{year}", value=2.0, step=0.1, format="%.1f")
            year_equity['Top Quartile'] = col3.number_input(f"TQ Y{year}", key=f"tq_eq_{year}", value=3.0, step=0.1, format="%.1f")
            year_equity['Top Decile'] = col4.number_input(f"TD Y{year}", key=f"td_eq_{year}", value=4.0, step=0.1, format="%.1f")
            year_equity['Maximum'] = col5.number_input(f"Max Y{year}", key=f"max_eq_{year}", value=5.0, step=0.1, format="%.1f")
        else:  # year == 4
            year_equity['Minimum'] = col1.number_input(f"Min Y{year}", key=f"min_eq_{year}", value=1.0, step=0.1, format="%.1f")
            year_equity['Median'] = col2.number_input(f"Med Y{year}", key=f"med_eq_{year}", value=2.0, step=0.1, format="%.1f")
            year_equity['Top Quartile'] = col3.number_input(f"TQ Y{year}", key=f"tq_eq_{year}", value=3.0, step=0.1, format="%.1f")
            year_equity['Top Decile'] = col4.number_input(f"TD Y{year}", key=f"td_eq_{year}", value=4.0, step=0.1, format="%.1f")
            year_equity['Maximum'] = col5.number_input(f"Max Y{year}", key=f"max_eq_{year}", value=5.0, step=0.1, format="%.1f")
        
        equity_levels.append(year_equity)

    st.sidebar.subheader("Equity Growth Rates")
    growth_rates = {
        'Min to Median': st.sidebar.number_input("Growth Rate: Minimum to Median", min_value=0.1, value=1.0, step=0.1, format="%.1f"),
        'Median to Top Quartile': st.sidebar.number_input("Growth Rate: Median to Top Quartile", min_value=0.1, value=1.0, step=0.1, format="%.1f"),
        'Top Quartile to Top Decile': st.sidebar.number_input("Growth Rate: Top Quartile to Top Decile", min_value=0.1, value=1.0, step=0.1, format="%.1f"),
        'Above Top Decile': st.sidebar.number_input("Growth Rate: Above Top Decile", min_value=0.1, value=0.5, step=0.1, format="%.1f")
    }

    benchmarks = pd.DataFrame({
        'Year': [1, 2, 3, 4],
        'Top Decile': [1.5, 5.5, 11.4, 17.0],
        'Top Quartile': [0.75, 1.875, 5.25, 12.6],
        'Median': [0.4, 0.8, 1.7, 3.0]
    })

    st.sidebar.subheader("Expected Revenue and Free Cash Flow")
    col1, col2 = st.sidebar.columns(2)
    actual_revenue = {}
    free_cash_flow = {}
    for year in range(1, 5):
        actual_revenue[year] = col1.number_input(f"Revenue Year {year} ($M)", 
                                                 min_value=0.0, value=benchmarks.loc[year-1, 'Top Quartile'], step=0.1, format="%.2f")
        free_cash_flow[year] = col2.number_input(f"FCF Year {year} ($M)", 
                                                 min_value=0.0, value=actual_revenue[year] * 0.2, step=0.1, format="%.2f")

    st.header("Performance Visualization")
    chart_data = benchmarks.melt(id_vars=['Year'], var_name='Benchmark', value_name='Revenue')
    actual_data = pd.DataFrame({
        'Year': range(1, 5),
        'Benchmark': 'Actual',
        'Revenue': [actual_revenue[y] for y in range(1, 5)]
    })
    chart_data = pd.concat([chart_data, actual_data])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    for column in ['Actual', 'Median', 'Top Quartile', 'Top Decile']:
        ax.plot(chart_data[chart_data['Benchmark'] == column]['Year'], 
                chart_data[chart_data['Benchmark'] == column]['Revenue'], 
                marker='o', label=column)
    ax.set_xlabel('Year')
    ax.set_ylabel('Revenue (Million USD)')
    ax.set_title('Performance Comparison')
    ax.legend()
    st.pyplot(fig)

    results = {
        'Actual Revenue': [],
        'Free Cash Flow': [],
        'Base Salary': [],
        'Proportional Bonus': [],
        'Total Comp (Proportional)': [],
        'Base Bonus': [],
        'Excess Revenue Bonus': [],
        'Total Comp (Excess Revenue)': [],
        'Equity': [],
        'Median Equity': [],
        'Median Comp': [],
        'Top Quartile Equity': [],
        'Top Quartile Comp': [],
    }

    for year in range(1, 5):
        base_salary = initial_base_salary_lakhs * (1 + salary_increase_rate) ** (year - 1)
        year_benchmarks = benchmarks.loc[year-1, ['Median', 'Top Quartile', 'Top Decile']].to_dict()
        
        equity, proportional_bonus, total_comp_proportional, base_bonus, excess_bonus, total_comp_excess = calculate_compensation(
            actual_revenue[year], year, year_benchmarks, base_salary, joining_bonus_lakhs, 
            equity_levels[year-1], bonus_base_percentage, excess_bonus_percentage, 
            free_cash_flow[year], growth_rates, exchange_rate
        )
        
        median_equity, _, median_total, _, _, _ = calculate_compensation(
            year_benchmarks['Median'], year, year_benchmarks, base_salary, joining_bonus_lakhs, 
            equity_levels[year-1], bonus_base_percentage, excess_bonus_percentage, 
            free_cash_flow[year], growth_rates, exchange_rate
        )
        
        quartile_equity, _, quartile_total, _, _, _ = calculate_compensation(
            year_benchmarks['Top Quartile'], year, year_benchmarks, base_salary, joining_bonus_lakhs, 
            equity_levels[year-1], bonus_base_percentage, excess_bonus_percentage, 
            free_cash_flow[year], growth_rates, exchange_rate
        )

        results['Actual Revenue'].append(actual_revenue[year])
        results['Free Cash Flow'].append(free_cash_flow[year])
        results['Base Salary'].append(base_salary)
        results['Proportional Bonus'].append(proportional_bonus)
        results['Total Comp (Proportional)'].append(total_comp_proportional)
        results['Base Bonus'].append(base_bonus)
        results['Excess Revenue Bonus'].append(excess_bonus)
        results['Total Comp (Excess Revenue)'].append(total_comp_excess)
        results['Equity'].append(equity)
        results['Median Equity'].append(median_equity)
        results['Median Comp'].append(median_total)
        results['Top Quartile Equity'].append(quartile_equity)
        results['Top Quartile Comp'].append(quartile_total)

    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Transpose the DataFrame
    results_df = results_df.transpose()
    
    # Set column names
    results_df.columns = ['Year 1', 'Year 2', 'Year 3', 'Year 4']

    def format_value(val, is_percentage=False, is_money=False, is_usd=False):
        if pd.isna(val):
            return ''
        if is_percentage:
            return f"{val:.2f}%"
        if is_money:
            return f"₹{val:.2f}L"
        if is_usd:
            return f"${val:.2f}M"
        return f"{val:.2f}"

    for col in results_df.columns:
        for idx in results_df.index:
            value = results_df.loc[idx, col]
            if 'Equity' in idx:
                results_df.loc[idx, col] = format_value(value, is_percentage=True)
            elif 'Salary' in idx or 'Bonus' in idx or 'Comp' in idx:
                results_df.loc[idx, col] = format_value(value, is_money=True)
            elif 'Revenue' in idx or 'Flow' in idx:
                results_df.loc[idx, col] = format_value(value, is_usd=True)

    def highlight_rows(row):
        styles = [''] * len(row)
        if row.name in ['Total Comp (Proportional)', 'Total Comp (Excess Revenue)']:
            styles = ['background-color: yellow; font-weight: bold'] * len(row)
        elif 'Bonus' in row.name:
            styles = ['background-color: lightblue'] * len(row)
        return styles

    styled_df = results_df.style.apply(highlight_rows, axis=1)
    st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)

    if st.button("Save Results"):
        href = save_results(results_df, fig)
        st.markdown(href, unsafe_allow_html=True)

    st.header("Explanation of Calculations")

    st.subheader("Revenue Benchmarks")
    st.write("""
    The revenue benchmarks are based on the ChartMogul SaaS Growth Report:

    **Median**: 
    - Year 1: $0.4M
    - Year 2: $0.8M
    - Year 3: $1.7M
    - Year 4: $3.0M

    **Top Quartile**: 
    - Year 1: $0.75M
    - Year 2: $1.875M
    - Year 3: $5.25M
    - Year 4: $12.6M

    **Top Decile**: 
    - Year 1: $1.5M
    - Year 2: $5.5M
    - Year 3: $11.4M
    - Year 4: $17.0M
    """)

    st.subheader("Equity Calculation")
    st.write("""
    The equity calculation is based on company performance levels: Median, Top Quartile, and Top Decile. As your company’s revenue increases, the amount of equity awarded grows based on these benchmarks.

    Here’s how the equity is calculated:

    **Formula 1: Performance ≤ Median**

    If the company’s performance is below or equal to the median revenue benchmark, equity is calculated as:

    $$ 
    Equity = Min + (Median - Min) \\times \\left( \\frac{Performance}{Median} \\right)^{\\text{Growth Rate from Min to Median}}
    $$

    **Formula 2: Median < Performance ≤ Top Quartile**

    If performance is between the median and top quartile:

    $$ 
    Equity = Median + (Top Quartile - Median) \\times \\left( \\frac{Performance - Median}{Top Quartile - Median} \\right)^{\\text{Growth Rate from Median to Top Quartile}}
    $$

    **Formula 3: Top Quartile < Performance ≤ Top Decile**

    For performance between the top quartile and top decile:

    $$ 
    Equity = Top Quartile + (Top Decile - Top Quartile) \\times \\left( \\frac{Performance - Top Quartile}{Top Decile - Top Quartile} \\right)^{\\text{Growth Rate from Top Quartile to Top Decile}}
    $$

    **Formula 4: Performance > Top Decile**

    If the company exceeds the top decile revenue benchmark:

    $$ 
    Equity = Top Decile + (Max - Top Decile) \\times \\left( \\frac{Performance - Top Decile}{Top Decile} \\right)^{\\text{Growth Rate Above Top Decile}}
    $$

    These formulas help determine how much equity employees earn based on how well the company performs compared to benchmarks.
    """)

    st.subheader("Bonus Calculation")
    st.write("""
    Bonuses are calculated using two methods: **Proportional Bonus** and **Excess Revenue Bonus**.

    **Proportional Bonus** rewards you based on how close or far you are from the target revenue. **Excess Revenue Bonus** rewards additional performance when actual revenue exceeds the target.

    ### 1. Proportional Bonus Calculation:

    If the company’s revenue is below or equal to the target revenue, the proportional bonus is:

    $$
    Proportional\\ Bonus = \\left( \\frac{\\text{Actual Revenue}}{\\text{Target Revenue}} \\right) \\times (\\text{Base Salary} \\times \\frac{\\text{Bonus Base Percentage}}{100})
    $$

    - This method ensures that the bonus is proportional to how close the actual revenue is to the target revenue.

    ### 2. Excess Revenue Bonus Calculation:

    If the actual revenue exceeds the target revenue, you will earn an **Excess Revenue Bonus**:

    a. First, calculate the **Base Bonus**:

    $$ 
    Base\\ Bonus = \\text{Base Salary} \\times \\frac{\\text{Bonus Base Percentage}}{100}
    $$

    b. Then, calculate the **Excess Revenue**:

    $$ 
    Excess\\ Revenue = \\text{Actual Revenue} - \\text{Target Revenue}
    $$

    c. If Free Cash Flow (FCF) is positive, the **Excess Bonus** is calculated:

    $$ 
    Excess\\ Bonus = Excess\\ Revenue \\times \\frac{\\text{Excess Bonus Percentage}}{100}
    $$

    d. If Free Cash Flow (FCF) is negative, the excess bonus is zero.

    ### Total Bonus:
    Finally, the total bonus is the sum of the **Base Bonus** and **Excess Bonus**:

    $$
    Total\\ Bonus = Base\\ Bonus + Excess\\ Bonus
    $$

    This approach ensures that you are rewarded not only for meeting targets but also for exceeding them, as long as the company maintains profitability.
    """)

    st.subheader("Total Compensation")
    st.write("""
    Your total compensation for each year is the sum of your base salary and the bonuses calculated using the **Proportional Bonus** and **Excess Revenue Bonus** methods.

    ### 1. Total Compensation (Proportional Bonus):

    $$
    Total\\ Compensation = Base\\ Salary + Proportional\\ Bonus
    $$

    ### 2. Total Compensation (Excess Revenue Bonus):

    $$
    Total\\ Compensation = Base\\ Salary + Total\\ Bonus\\ (Base\\ Bonus + Excess\\ Bonus)
    $$

    **Note**:
    - For the first year, the joining bonus is factored into the total compensation.
    - Your base salary increases each year according to the **Annual Salary Increase Rate** you input.
    """)

if __name__ == "__main__":
    main()
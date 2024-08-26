import streamlit as st
import pandas as pd
import numpy as np
import math

# Function to add text logo
def add_text_logo():
    st.markdown(
        """
        <style>
        .logo-text {
            font-size: 24px;
            font-weight: bold;
            color: #4682B4;
            text-align: right;
            margin-right: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<p class="logo-text">CompCal</p>', unsafe_allow_html=True)

def calculate_equity(performance, median, top_quartile, top_decile, base_equity, min_equity, max_equity, median_ratio):
    if performance <= median:
        equity = max(min_equity, base_equity * median_ratio * (performance / median))
    elif performance <= top_quartile:
        equity = base_equity * median_ratio + (base_equity - base_equity * median_ratio) * ((performance - median) / (top_quartile - median))
    else:
        equity = base_equity * (math.log(performance / top_quartile, 3) + 1)
    return min(max_equity, equity)

def calculate_cash_bonus(performance, top_quartile, base_salary, bonus_base_percentage):
    target_bonus = base_salary * (bonus_base_percentage / 100)
    return target_bonus * (math.log(performance / top_quartile, 3) + 1)

def calculate_compensation(revenue, year, benchmarks, base_salary, joining_bonus, equity_distribution, bonus_base_percentage, min_equity_percentages, max_equity_percentages, median_equity_ratio):
    top_quartile = benchmarks.loc[year-1, 'Top Quartile']
    top_decile = benchmarks.loc[year-1, 'Top Decile']
    median = benchmarks.loc[year-1, 'Median']
    
    base_equity = equity_distribution[year-1]
    min_equity = min_equity_percentages[year-1]
    max_equity = max_equity_percentages[year-1]
    
    equity = calculate_equity(revenue, median, top_quartile, top_decile, base_equity, min_equity, max_equity, median_equity_ratio)
    bonus = calculate_cash_bonus(revenue, top_quartile, base_salary, bonus_base_percentage)
    
    if year == 1:
        bonus = max(0, bonus - joining_bonus)
        total_comp = base_salary + joining_bonus + bonus
    else:
        total_comp = base_salary + bonus
    
    return equity, bonus, total_comp

def main():
    st.set_page_config(layout="wide")
    add_text_logo()
    st.title("SaaS Compensation Calculator")

    # Input fields
    st.sidebar.header("Input Parameters")
    exchange_rate = st.sidebar.number_input("USD to INR Exchange Rate", min_value=1.0, value=83.0, step=0.1, format="%.1f")
    
    st.sidebar.subheader("Salary and Bonus Parameters")
    initial_base_salary_lakhs = st.sidebar.number_input("Initial Base Salary (Lakhs INR)", min_value=0.0, value=100.0, step=1.0, format="%.1f")
    joining_bonus_lakhs = st.sidebar.number_input("Joining Bonus (Lakhs INR)", min_value=0.0, value=20.0, step=1.0, format="%.1f")
    salary_increase_rate = st.sidebar.number_input("Annual Salary Increase Rate (%)", min_value=0.0, value=10.0, step=0.1, format="%.1f") / 100
    bonus_base_percentage = st.sidebar.number_input("Bonus Base (% of Base Salary)", min_value=0.0, value=100.0, step=1.0, format="%.1f")

    st.sidebar.subheader("Equity Parameters")
    col1, col2, col3 = st.sidebar.columns(3)
    equity_distribution = []
    min_equity_percentages = []
    max_equity_percentages = []
    for i in range(4):
        with col1:
            equity = st.number_input(f"Base Equity Year {i+1} (%)", min_value=0.0, value=4.0 if i < 3 else 3.0, step=0.1, format="%.1f")
            equity_distribution.append(equity)
        with col2:
            min_equity = st.number_input(f"Min Equity Year {i+1} (%)", min_value=0.0, value=2.0 if i < 3 else 1.5, step=0.1, format="%.1f")
            min_equity_percentages.append(min_equity)
        with col3:
            max_equity = st.number_input(f"Max Equity Year {i+1} (%)", min_value=0.0, value=6.0 if i < 3 else 4.5, step=0.1, format="%.1f")
            max_equity_percentages.append(max_equity)

    median_equity_ratio = st.sidebar.number_input("Median to Top Quartile Equity Ratio", min_value=0.0, max_value=1.0, value=0.8333, step=0.01, format="%.4f")

    # Input for actual revenue for each year
    st.sidebar.subheader("Actual Revenue")
    actual_revenue = {}
    for year in range(1, 5):
        actual_revenue[year] = st.sidebar.number_input(f"Actual Revenue for Year {year} (Million USD)", 
                                                       min_value=0.0, value=0.75 * (2 ** (year - 1)), step=0.1, format="%.2f")

    # Define benchmarks
    benchmarks = pd.DataFrame({
        'Year': [1, 2, 3, 4],
        'Top Decile': [1.5, 5.5, 11.4, 17.0],
        'Top Quartile': [0.75, 1.875, 5.25, 12.6],
        'Median': [0.4, 0.8, 1.7, 3.0]
    })

    # Performance visualization
    st.header("Performance Visualization")
    chart_data = benchmarks.melt(id_vars=['Year'], var_name='Benchmark', value_name='Revenue')
    actual_data = pd.DataFrame({
        'Year': range(1, 5),
        'Benchmark': 'Actual',
        'Revenue': [actual_revenue[y] for y in range(1, 5)]
    })
    chart_data = pd.concat([chart_data, actual_data])
    
    st.line_chart(chart_data.pivot(index='Year', columns='Benchmark', values='Revenue'))

    # Calculate results
    results = {
        'Actual Revenue': [],
        'Base Salary': [],
        'Equity': [],
        'Cash Bonus': [],
        'Total Compensation': [],
        'Median Equity': [],
        'Median Comp': [],
        'Top Quartile Equity': [],
        'Top Quartile Comp': [],
        'Top Decile Equity': [],
        'Top Decile Comp': []
    }

    for year in range(1, 5):
        base_salary = initial_base_salary_lakhs * (1 + salary_increase_rate) ** (year - 1)
        
        equity, bonus, total_comp = calculate_compensation(actual_revenue[year], year, benchmarks, base_salary, joining_bonus_lakhs, equity_distribution, bonus_base_percentage, min_equity_percentages, max_equity_percentages, median_equity_ratio)
        median_equity, median_bonus, median_total = calculate_compensation(benchmarks.loc[year-1, 'Median'], year, benchmarks, base_salary, joining_bonus_lakhs, equity_distribution, bonus_base_percentage, min_equity_percentages, max_equity_percentages, median_equity_ratio)
        quartile_equity, quartile_bonus, quartile_total = calculate_compensation(benchmarks.loc[year-1, 'Top Quartile'], year, benchmarks, base_salary, joining_bonus_lakhs, equity_distribution, bonus_base_percentage, min_equity_percentages, max_equity_percentages, median_equity_ratio)
        decile_equity, decile_bonus, decile_total = calculate_compensation(benchmarks.loc[year-1, 'Top Decile'], year, benchmarks, base_salary, joining_bonus_lakhs, equity_distribution, bonus_base_percentage, min_equity_percentages, max_equity_percentages, median_equity_ratio)

        results['Actual Revenue'].append(actual_revenue[year])
        results['Base Salary'].append(base_salary)
        results['Equity'].append(equity)
        results['Cash Bonus'].append(bonus)
        results['Total Compensation'].append(total_comp)
        results['Median Equity'].append(median_equity)
        results['Median Comp'].append(median_total)
        results['Top Quartile Equity'].append(quartile_equity)
        results['Top Quartile Comp'].append(quartile_total)
        results['Top Decile Equity'].append(decile_equity)
        results['Top Decile Comp'].append(decile_total)

    # Display results in a table
    st.header("Compensation Results")
    results_df = pd.DataFrame(results, index=['Year 1', 'Year 2', 'Year 3', 'Year 4'])
    
    # Calculate totals
    total_actual_revenue = sum(results['Actual Revenue'])
    total_base_salary = sum(results['Base Salary'])
    total_equity = sum(results['Equity'])
    total_cash_bonus = sum(results['Cash Bonus'])
    total_compensation = sum(results['Total Compensation'])
    total_median_equity = sum(results['Median Equity'])
    total_median_comp = sum(results['Median Comp'])
    total_top_quartile_equity = sum(results['Top Quartile Equity'])
    total_top_quartile_comp = sum(results['Top Quartile Comp'])
    total_top_decile_equity = sum(results['Top Decile Equity'])
    total_top_decile_comp = sum(results['Top Decile Comp'])

    # Add total row
    results_df.loc['Total'] = [
        total_actual_revenue,
        total_base_salary,
        total_equity,
        total_cash_bonus,
        total_compensation,
        total_median_equity,
        total_median_comp,
        total_top_quartile_equity,
        total_top_quartile_comp,
        total_top_decile_equity,
        total_top_decile_comp
    ]
    
    # Format the dataframe
    for col in results_df.columns:
        if col in ['Equity', 'Median Equity', 'Top Quartile Equity', 'Top Decile Equity']:
            results_df[col] = results_df[col].apply(lambda x: f"{x:.2f}%")
        elif col == 'Actual Revenue':
            results_df[col] = results_df[col].apply(lambda x: f"${x:.2f}M")
        else:
            results_df[col] = results_df[col].apply(lambda x: f"₹{x:.2f}L")
    
    # Highlight total row
    def highlight_total(row):
        if row.name == 'Total':
            return ['background-color: yellow'] * len(row)
        return [''] * len(row)

    st.table(results_df.T.style.apply(highlight_total, axis=1))

    # Display benchmarks
    st.header("Performance Benchmarks (Million USD)")
    st.table(benchmarks.set_index('Year'))

    # Explanation of calculations
    st.header("Explanation of Calculations")
    st.subheader("Base Salary Calculation")
    st.write(f"""
    The base salary starts at ₹{initial_base_salary_lakhs:.2f} lakhs and increases by {salary_increase_rate*100:.1f}% each year.
    """)

    st.subheader("Equity Calculation")
    st.write(f"""
    The equity is calculated as follows:
    - At top quartile performance: Yearly values as specified in the sidebar
    - At median performance: {median_equity_ratio:.4f} of the top quartile value for each year
    - Minimum equity per year: As specified in the sidebar for each year
    - Maximum equity per year: As specified in the sidebar for each year
    - Above top quartile: Increases logarithmically (base 3)
    - Below median: Scales linearly down to the minimum
    The total equity over 4 years is the sum of the equity percentages for each year.
    """)

    st.subheader("Bonus Calculation")
    st.write(f"""
    The bonus is calculated using the formula:
    ```
    Bonus = Target Bonus * (log(Actual Revenue / Top Quartile Revenue, 3) + 1)
    ```
    Where:
    - Target Bonus is {bonus_base_percentage:.1f}% of the base salary
    - The logarithmic function scales the bonus based on performance relative to the top quartile benchmark

    For the first year, the joining bonus of ₹{joining_bonus_lakhs:.2f} lakhs is subtracted from the calculated bonus.
    """)

    st.subheader("Total Compensation")
    st.write("""
    The total compensation for each year is calculated as:
    ```
    Total Compensation = Base Salary + Cash Bonus
    ```
    For the first year, the joining bonus is included in the total compensation.

    The total compensation over 4 years is the sum of the total compensation for each year.
    """)

    st.subheader("Performance Scenarios")
    st.write("""
    The calculator provides compensation details for different performance scenarios:
    1. Actual Performance: Based on the revenue input for each year
    2. Median Performance: Compensation if revenue matches the median benchmark
    3. Top Quartile Performance: Compensation if revenue matches the top quartile benchmark
    4. Top Decile Performance: Compensation if revenue matches the top decile benchmark

    This allows for easy comparison of potential outcomes based on different performance levels.
    """)

if __name__ == "__main__":
    main()

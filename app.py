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

    st.header("SaaS Compensation Calculator User Guide")

    st.markdown("""
    Welcome to the **CompCal** app! This tool is designed to help you calculate and visualize compensation for SaaS companies, taking into account factors like base salary, equity, bonuses, and revenue performance. Here’s a step-by-step guide to get the most out of the app.

    ## Exploring the App

    ### 1. Input Parameters (Set Your Scenario)

    In the sidebar, you’ll find various input fields that let you customize the scenario. Let’s break them down:

    - **Exchange Rate (USD to INR):** This is the conversion rate from US dollars to Indian rupees. This rate impacts all salary and bonus calculations in the app.

    - **Initial Base Salary (Lakhs INR):** This is the starting salary (in lakhs) for the first year. The salary can increase each year based on the **Annual Salary Increase Rate**.

    - **Joining Bonus (Lakhs INR):** A one-time bonus given in the first year. This bonus is subtracted from the first year’s calculated bonus.

    - **Annual Salary Increase Rate (%):** This rate determines how much the base salary increases each year. For example, a 10% rate means the salary for year 2 is 110% of the year 1 salary.

    - **Bonus Base (% of Base Salary):** This is the target bonus percentage of the base salary. For example, 100% means the bonus equals the base salary if performance meets expectations.

    - **Equity Parameters:** Equity represents ownership in the company and is a critical part of compensation in startups. You can adjust:
    - **Base Equity (%):** The target equity given each year.
    - **Min Equity (%):** The minimum possible equity based on poor performance.
    - **Max Equity (%):** The maximum possible equity based on outstanding performance.
    - **Median to Top Quartile Equity Ratio:** This ratio adjusts equity when performance is median-level compared to top quartile performance.

    - **Actual Revenue (Million USD):** Enter the expected revenue for each year. The app uses this to calculate how well the company performs against benchmarks.

    ### 2. Understanding the Benchmarks

    The app compares actual revenue against three benchmarks:
    - **Median:** Average performance.
    - **Top Quartile:** Strong performance in the top 25%.
    - **Top Decile:** Outstanding performance in the top 10%.

    These benchmarks help you see where your company’s performance stands.

    ### 3. How Calculations Work

    The app computes equity, bonuses, and total compensation based on the inputs and benchmarks.

    - **Equity Calculation:**
    - **Below Median:** Equity scales down to the minimum value.
    - **Between Median and Top Quartile:** Equity increases linearly.
    - **Above Top Quartile:** Equity increases logarithmically (less aggressively) as performance improves further.

    **Formula:**
    ```
    if performance <= median:
    equity = max(min_equity, base_equity * median_ratio * (performance / median))
    elif performance <= top_quartile:
    equity = base_equity * median_ratio + (base_equity - base_equity * median_ratio) * ((performance - median) / (top_quartile - median))
    else:
    equity = base_equity * (math.log(performance / top_quartile, 3) + 1)
    ```
    - **Bonus Calculation:**
    - The bonus is computed as a percentage of the base salary, adjusted by performance compared to the top quartile revenue using a logarithmic function. For the first year, the joining bonus is subtracted from the total bonus.

    **Formula:**
    ```
    target_bonus = base_salary * (bonus_base_percentage / 100)
    bonus = target_bonus * (math.log(performance / top_quartile, 3) + 1)
    ```
    ### 4. Visualizing Performance

    The app provides a chart comparing actual revenue against benchmarks, helping you visualize your company’s performance. This chart gives a quick overview of how your expected revenue measures up.

    ### 5. Reviewing Results

    The app summarizes the results in a table, showing:
    - **Actual Revenue** for each year.
    - **Base Salary** progression over the years.
    - **Equity, Cash Bonus, and Total Compensation** for each year and in total.

    ### 6. Understanding the Results

    The app also provides detailed explanations of how each component is calculated:
    - **Base Salary:** Starts with the initial salary and grows by the defined percentage each year.
    - **Equity:** Adjusts based on performance, with the highest potential when performance exceeds top quartile benchmarks.
    - **Bonus:** Scales with performance, rewarding higher revenue with a logarithmically increasing bonus.

    ### Example Scenario

    Imagine a scenario where your company expects to achieve the following revenues:
    - Year 1: $0.75M
    - Year 2: $1.875M
    - Year 3: $5.25M
    - Year 4: $12.6M

    Using these inputs, the app will calculate the resulting equity, bonus, and total compensation based on how your performance compares with benchmarks like the top decile.

    ## Experiment and Play

    Feel free to experiment with different values in the sidebar. See how changes in salary, revenue, or equity parameters affect the total compensation. This interactive approach helps you understand how each factor contributes to the overall compensation package.

    Happy exploring!
    """)

if __name__ == "__main__":
    main()

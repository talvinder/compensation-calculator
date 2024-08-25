import streamlit as st
import pandas as pd
import numpy as np
import math

def calculate_equity(performance, top_quartile, base_equity):
    return base_equity * (math.log(performance / top_quartile, 3) + 1)

def calculate_cash_bonus(performance, top_quartile, base_salary):
    target_bonus = base_salary  # 100% of base salary at top quartile performance
    return target_bonus * (math.log(performance / top_quartile, 3) + 1)

def main():
    st.set_page_config(layout="wide")
    st.title("SaaS Compensation Calculator")

    # Sidebar for inputs
    st.sidebar.header("Input Parameters")
    exchange_rate = st.sidebar.number_input("USD to INR Exchange Rate", min_value=1.0, value=83.0, step=0.1, format="%.1f")
    
    st.sidebar.subheader("Salary and Bonus Parameters")
    initial_base_salary_lakhs = st.sidebar.number_input("Initial Base Salary (Lakhs INR)", min_value=0.0, value=100.0, step=1.0, format="%.1f")
    joining_bonus_lakhs = st.sidebar.number_input("Joining Bonus (Lakhs INR)", min_value=0.0, value=20.0, step=1.0, format="%.1f")
    salary_increase_rate = st.sidebar.number_input("Annual Salary Increase Rate (%)", min_value=0.0, value=10.0, step=0.1, format="%.1f") / 100

    st.sidebar.subheader("Equity Parameters")
    equity_distribution = [
        st.sidebar.number_input(f"Base Equity for Year {i}", min_value=0.0, value=v, step=0.1, format="%.1f")
        for i, v in enumerate([4.0, 4.0, 4.0, 3.0], start=1)
    ]

    # Load benchmarks (in million USD)
    benchmarks = pd.DataFrame({
        'Year': [1, 2, 3, 4],
        'Top Decile': [1.5, 5.5, 11.4, 17.0],
        'Top Quartile': [0.75, 1.875, 5.25, 12.6],
        'Median': [0.4, 0.8, 1.7, 3.0]
    })

    # Input for actual revenue for each year
    actual_revenue = {}
    for year in range(1, 5):
        actual_revenue[year] = st.sidebar.number_input(f"Actual Revenue for Year {year} (Million USD)", 
                                                       min_value=0.0, value=benchmarks.loc[year-1, 'Top Quartile'], 
                                                       step=0.1, format="%.2f")

    # Display benchmarks in main view
    st.header("Performance Benchmarks (Million USD)")
    st.table(benchmarks.set_index('Year'))

    # Calculate results
    results = []
    total_equity = 0
    for year in range(1, 5):
        top_quartile = benchmarks.loc[year-1, 'Top Quartile']
        base_salary = initial_base_salary_lakhs * (1 + salary_increase_rate) ** (year - 1)
        
        equity_percentage = calculate_equity(actual_revenue[year], top_quartile, equity_distribution[year-1])
        total_equity += equity_percentage
        
        cash_bonus_lakhs = calculate_cash_bonus(actual_revenue[year], top_quartile, base_salary)
        
        if year == 1:
            cash_bonus_lakhs = max(0, cash_bonus_lakhs - joining_bonus_lakhs)  # Adjust first year bonus
            total_comp = base_salary + joining_bonus_lakhs + cash_bonus_lakhs
        else:
            total_comp = base_salary + cash_bonus_lakhs

        results.append({
            'Year': year,
            'Actual Revenue': f"${actual_revenue[year]:.2f}M",
            'Base Salary': f"₹{base_salary:.2f}L",
            'Equity': f"{equity_percentage:.2f}%",
            'Cash Bonus': f"₹{cash_bonus_lakhs:.2f}L",
            'Total Compensation': f"₹{total_comp:.2f}L"
        })

    # Display results in a table
    st.header("Compensation Results")
    results_df = pd.DataFrame(results).set_index('Year')
    st.table(results_df)

    st.write(f"Total Equity Over 4 Years: {total_equity:.2f}%")

    # Explanation of calculations
    st.header("Explanation of Calculations")
    st.subheader("Base Salary Calculation")
    st.write(f"""
    The base salary starts at ₹{initial_base_salary_lakhs:.2f} lakhs and increases by {salary_increase_rate*100:.1f}% each year.
    """)

    st.subheader("Equity Calculation")
    st.write("""
    The equity is calculated using the formula:
    ```
    Equity = Base Equity * (log(Actual Revenue / Top Quartile Revenue, 3) + 1)
    ```
    - If actual revenue equals the top quartile, the equity awarded is exactly the base equity.
    - If actual revenue is above the top quartile, the equity increases logarithmically.
    - If actual revenue is below the top quartile, the equity decreases logarithmically.
    """)

    st.subheader("Bonus Calculation")
    st.write(f"""
    The bonus is calculated using the formula:
    ```
    Bonus = Target Bonus * (log(Actual Revenue / Top Quartile Revenue, 3) + 1)
    ```
    Where Target Bonus is 100% of the base salary for that year.
    - If actual revenue equals the top quartile, the bonus is exactly 100% of the base salary.
    - If actual revenue is above the top quartile, the bonus increases logarithmically.
    - If actual revenue is below the top quartile, the bonus decreases logarithmically.

    For the first year, the joining bonus of ₹{joining_bonus_lakhs:.2f} lakhs is subtracted from the calculated bonus.
    """)

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

if __name__ == "__main__":
    main()

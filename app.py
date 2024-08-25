import streamlit as st
import pandas as pd
import numpy as np
import math

def calculate_equity(performance, top_quartile, base_equity):
    return base_equity * (math.log(performance / top_quartile, 3) + 1)

def calculate_cash_bonus(performance, top_quartile, exchange_rate, base_bonus_usd, over_performance_rate):
    over_performance = max(0, performance - top_quartile)
    bonus_usd = base_bonus_usd + over_performance * over_performance_rate
    return bonus_usd * exchange_rate * 10  # Convert to INR lakhs

def main():
    st.set_page_config(layout="wide")
    st.title("SaaS Compensation Calculator")

    # Sidebar for inputs
    st.sidebar.header("Input Parameters")
    exchange_rate = st.sidebar.number_input("USD to INR Exchange Rate", min_value=1.0, value=83.0, step=0.1, format="%.1f")
    
    st.sidebar.subheader("Equity Parameters")
    equity_distribution = [
        st.sidebar.number_input(f"Base Equity for Year {i}", min_value=0.0, value=v, step=0.1, format="%.1f")
        for i, v in enumerate([4.0, 4.0, 4.0, 3.0], start=1)
    ]
    
    st.sidebar.subheader("Bonus Parameters")
    base_bonus_usd = st.sidebar.number_input("Base Bonus (Million USD)", min_value=0.0, value=0.1, step=0.01, format="%.2f")
    over_performance_rate = st.sidebar.number_input("Over-performance Rate", min_value=0.0, value=0.1, step=0.01, format="%.2f")
    
    base_salary_lakhs = st.sidebar.number_input("Base Salary (Lakhs INR)", min_value=0.0, value=60.0, step=1.0, format="%.1f")

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
        equity_percentage = calculate_equity(actual_revenue[year], top_quartile, equity_distribution[year-1])
        total_equity += equity_percentage
        cash_bonus_lakhs = calculate_cash_bonus(actual_revenue[year], top_quartile, exchange_rate, base_bonus_usd, over_performance_rate)
        results.append({
            'Year': year,
            'Actual Revenue': f"${actual_revenue[year]:.2f}M",
            'Equity': f"{equity_percentage:.2f}%",
            'Cash Bonus': f"₹{cash_bonus_lakhs:.2f}L",
            'Base Salary': f"₹{base_salary_lakhs:.2f}L"
        })

    # Display results in a table
    st.header("Compensation Results")
    results_df = pd.DataFrame(results).set_index('Year')
    st.table(results_df)

    st.write(f"Total Equity Over 4 Years: {total_equity:.2f}%")

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

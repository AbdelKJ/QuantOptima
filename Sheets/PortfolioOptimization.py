import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from sklearn.model_selection import train_test_split
import plotly.express as px
from skfolio import Population
from skfolio import RiskMeasure
from skfolio.optimization import EqualWeighted, MaximumDiversification, MeanRisk, ObjectiveFunction
from skfolio.preprocessing import prices_to_returns

# ======================================================
st.title("🎯 Portfolio Optimization and Suggested Allocation")

# ======================================================
# Initial Checks
# ======================================================

if "close_prices" not in st.session_state or st.session_state.close_prices is None:
    st.error("⚠️ Please fetch and select your assets first!")
    st.stop()

close_prices = st.session_state.close_prices

# Define asset classes
selected_assets = ["Equities", "Fixed Income", "Real Estate", "Commodities", "Alternatives"]

# Mock ETF -> Asset Class mapping
if "asset_class_map" not in st.session_state:
    st.session_state.asset_class_map = {etf: np.random.choice(selected_assets) for etf in close_prices.columns}
asset_class_map = st.session_state.asset_class_map

# Optimization Models
optimization_models = {
    "Equal Weighted": EqualWeighted(),
    "Maximum Diversification": MaximumDiversification(),
    "Minimum CVaR": MeanRisk(risk_measure=RiskMeasure.CVAR, objective_function=ObjectiveFunction.MINIMIZE_RISK),
    "Mean-Variance (Max Sharpe)": MeanRisk(risk_measure=RiskMeasure.STANDARD_DEVIATION, objective_function=ObjectiveFunction.MAXIMIZE_RATIO),
}

# ======================================================
# CLEAR BUTTON
# ======================================================

if st.button("🧹 Clear All Results"):
    for key in ["summary_generated", "population_weights", "optimized_asset_alloc", "manual_asset_alloc", "detailed_model_run", "population", "metrics_list"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("✅ Cleared! Start fresh.")

# ======================================================
# PART 1: Optimization Models Summary
# ======================================================

st.subheader("🚀 Generate Optimization Models Summary")

if st.button("🔵 Run Optimization Models Summary") or st.session_state.get("summary_generated"):
    st.session_state.summary_generated = True

    returns = prices_to_returns(close_prices)
    returns_train, returns_test = train_test_split(returns, test_size=0.33, shuffle=False)
    returns_train = returns_train.dropna(axis=1, how='any')
    returns_train = returns_train.loc[:, returns_train.std() > 0]

    # Simulate random portfolios
    simulated_metrics = []
    num_simulations = 100
    tickers = returns_train.columns.tolist()

    for _ in range(num_simulations):
        weights = np.random.dirichlet(np.ones(len(tickers)), size=1).flatten()
        simulated_returns = returns_test @ weights
        cum_returns = (1 + simulated_returns).cumprod()

        ann_return = (1 + simulated_returns.mean()) ** 252 - 1
        volatility = simulated_returns.std() * np.sqrt(252)
        sharpe = ann_return / volatility if volatility != 0 else 0
        max_drawdown = (cum_returns / cum_returns.cummax() - 1).min()

        simulated_metrics.append({
            "Portfolio": "Simulated",
            "Annualized Return (%)": round(ann_return * 100, 2),
            "Volatility (%)": round(volatility * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown (%)": round(max_drawdown * 100, 2),
        })

    # Save in session state for use in PDF
    st.session_state.simulated_metrics = simulated_metrics

    metrics_list = []
    st.session_state.population_weights = {}
    portfolio_list = []

    for name, model in optimization_models.items():
        try:
            model.fit(returns_train)
            optimized_portfolio = model.predict(returns_test)
            optimized_portfolio.name = name
            portfolio_list.append(optimized_portfolio)

            weights = pd.Series(optimized_portfolio.weights, index=optimized_portfolio.assets)
            st.session_state.population_weights[name] = weights

            portfolio_returns = returns_test @ weights
            cumulative_returns = (1 + portfolio_returns).cumprod()
            ann_return = (1 + portfolio_returns.mean()) ** 252 - 1
            volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe = ann_return / volatility if volatility != 0 else 0
            max_drawdown = (cumulative_returns / cumulative_returns.cummax() - 1).min()

            metrics_list.append({
                "Portfolio": name,
                "Annualized Return (%)": round(ann_return * 100, 2),
                "Volatility (%)": round(volatility * 100, 2),
                "Sharpe Ratio": round(sharpe, 2),
                "Max Drawdown (%)": round(max_drawdown * 100, 2),
            })

        except Exception as e:
            st.error(f"❌ {name} Optimization failed: {e}")

    st.session_state.population = Population(portfolio_list)
    st.session_state.metrics_list = metrics_list

    summary_df = pd.DataFrame(metrics_list)
    st.dataframe(summary_df, use_container_width=True)

    if not summary_df.empty:
        best_model = summary_df.loc[summary_df['Sharpe Ratio'].idxmax(), 'Portfolio']
        safest_model = summary_df.loc[summary_df['Max Drawdown (%)'].idxmin(), 'Portfolio']
        st.success(f"👉 **Best Sharpe Ratio**: {best_model} | 🛡️ **Lowest Drawdown**: {safest_model}")

st.markdown("""<hr style='border:0;height:2px;background:linear-gradient(to right, #FFB343, #6F1D1B);margin:20px 0;'>""", unsafe_allow_html=True)

# ======================================================
# PART 2: Manual Suggested Allocation
# ======================================================

st.subheader("🛠️ Input Suggested Allocation")

manual_allocation = {}
with st.form("manual_allocation_form"):
    total_alloc = 0
    for asset in selected_assets:
        manual_allocation[asset] = st.number_input(f"{asset} (%)", min_value=0, max_value=100, step=1, key=f"manual_{asset}")
        total_alloc += manual_allocation[asset]

    confirm_manual = st.form_submit_button("✅ Confirm Suggested Allocation")

if confirm_manual:
    if total_alloc > 100:
        st.error("🚫 Total allocation exceeds 100%! Please adjust.")
    else:
        cash = 100 - total_alloc
        manual_allocation["Cash"] = round(cash, 2)
        st.session_state.manual_asset_alloc = manual_allocation
        st.success("✅ Suggested allocation saved!")

# ======================================================
# PART 3: Allocation Comparison
# ======================================================

st.subheader("📋 Compare Current and Suggested Allocations")

current_allocation = st.session_state.get("current_allocation", {asset: 20 for asset in selected_assets})
current_allocation['Cash'] = round(100 - sum(current_allocation.values()), 2)

manual_allocation = st.session_state.get("manual_asset_alloc", {asset: 0 for asset in selected_assets})
if "Cash" not in manual_allocation:
    manual_allocation['Cash'] = 100

allocation_df = pd.DataFrame({
    "Current Allocation (%)": pd.Series(current_allocation),
    "Suggested Allocation (%)": pd.Series(manual_allocation),
})

allocation_df["% Difference"] = allocation_df["Suggested Allocation (%)"] - allocation_df["Current Allocation (%)"]

total_row = pd.DataFrame({
    "Current Allocation (%)": [allocation_df['Current Allocation (%)'].sum()],
    "Suggested Allocation (%)": [allocation_df['Suggested Allocation (%)'].sum()],
    "% Difference": [allocation_df['% Difference'].sum()]
}, index=["TOTAL"])

full_allocation = pd.concat([allocation_df, total_row])
st.dataframe(full_allocation.style.format("{:.2f}"), use_container_width=True)

# ======================================================
# PART 4: Bigger Pie Charts
# ======================================================

st.subheader("📊 Visual Comparison")

col1, col2 = st.columns(2)

with col1:
    nonzero_current = allocation_df[allocation_df['Current Allocation (%)'] > 0]
    fig1 = px.pie(
        names=nonzero_current.index,
        values=nonzero_current['Current Allocation (%)'],
        title="Current Allocation",
        hole=0.3
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    nonzero_manual = allocation_df[allocation_df['Suggested Allocation (%)'] > 0]
    fig2 = px.pie(
        names=nonzero_manual.index,
        values=nonzero_manual['Suggested Allocation (%)'],
        title="Suggested Allocation",
        hole=0.3
    )
    st.plotly_chart(fig2, use_container_width=True)
    #
    # st.write("✅ population.summary() DataFrame:")
    # st.dataframe(summary_df)
    #
    # st.write("✅ dtypes:")
    # st.write(summary_df.dtypes)

# ======================================================
# END
# ======================================================
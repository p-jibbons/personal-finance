import streamlit as st
from components.portfolio_form import render_portfolio_form
from components.stock_chart import render_portfolio_chart
from services.portfolio_service import (
    load_portfolio,
    add_position,
    delete_position,
    enrich_portfolio,
    calculate_portfolio_history,
    get_position_performance,
)

st.set_page_config(page_title="Personal Finance", layout="wide")
st.title("Personal Finance Dashboard")

# Create tabs
tab1, tab2 = st.tabs(["📊 Portfolio Management", "📈 Analysis"])

with tab1:
    st.header("Portfolio Management")

    # Render the form
    form_data = render_portfolio_form()

    # Handle form submission
    if form_data:
        try:
            add_position(
                symbol=form_data["symbol"],
                buy_date=form_data["buy_date"],
                shares=form_data["shares"],
                sell_date=form_data["sell_date"],
            )
            st.success(f"Added {form_data['shares']} shares of {form_data['symbol']}")
            st.rerun()
        except Exception as e:
            st.error(f"Error adding position: {str(e)}")

    # Display current portfolio
    st.subheader("Your Portfolio")
    portfolio = load_portfolio()

    if portfolio.empty:
        st.info("No positions yet. Add your first position above!")
    else:
        # Enrich portfolio with calculated fields
        with st.spinner("Fetching prices and calculating metrics..."):
            enriched = enrich_portfolio(portfolio)

        # Select columns to display
        display_cols = [
            "symbol",
            "buy_date",
            "shares",
            "buy_price",
            "cost_basis",
            "status",
            "current_price",
            "current_value",
            "sell_date",
            "sell_price",
            "sold_value",
            "gain_loss",
            "gain_loss_pct",
        ]

        # Format the display DataFrame
        display_df = enriched[display_cols].copy()

        # Format numeric columns
        display_df["buy_price"] = display_df["buy_price"].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "-"
        )
        display_df["sell_price"] = display_df["sell_price"].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "-"
        )
        display_df["current_price"] = display_df["current_price"].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "-"
        )
        display_df["cost_basis"] = display_df["cost_basis"].apply(
            lambda x: f"${x:,.2f}"
        )
        display_df["current_value"] = display_df["current_value"].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "-"
        )
        display_df["sold_value"] = display_df["sold_value"].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "-"
        )
        display_df["gain_loss"] = display_df["gain_loss"].apply(
            lambda x: f"${x:,.2f}" if x != 0 else "$0.00"
        )
        display_df["gain_loss_pct"] = display_df["gain_loss_pct"].apply(
            lambda x: f"{x:,.2f}%" if x != 0 else "0.00%"
        )
        display_df["sell_date"] = display_df["sell_date"].apply(
            lambda x: x if x else "-"
        )

        # Rename columns for better display
        display_df.columns = [
            "Symbol",
            "Buy Date",
            "Shares",
            "Buy Price",
            "Cost Basis",
            "Status",
            "Current Price",
            "Current Value",
            "Sell Date",
            "Sell Price",
            "Sold Value",
            "Gain/Loss $",
            "Gain/Loss %",
        ]

        # Display the enriched portfolio
        st.dataframe(display_df, width="stretch", hide_index=True)

        # Summary metrics
        st.subheader("Portfolio Summary")
        col1, col2, col3, col4 = st.columns(4)

        total_cost = enriched["cost_basis"].sum()
        total_current = enriched[enriched["status"] == "Open"]["current_value"].sum()
        total_sold = enriched[enriched["status"] == "Closed"]["sold_value"].sum()
        total_gain_loss = enriched["gain_loss"].sum()

        with col1:
            st.metric("Total Invested", f"${total_cost:,.2f}")
        with col2:
            st.metric("Current Holdings Value", f"${total_current:,.2f}")
        with col3:
            st.metric("Total Sold Value", f"${total_sold:,.2f}")
        with col4:
            gain_loss_pct = (
                (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            )
            st.metric(
                "Total Gain/Loss",
                f"${total_gain_loss:,.2f}",
                f"{gain_loss_pct:,.2f}%",
            )

        # Add delete functionality
        st.subheader("Delete Position")
        if len(portfolio) > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                delete_index = st.selectbox(
                    "Select position to delete",
                    options=portfolio.index.tolist(),
                    format_func=lambda x: (
                        f"{portfolio.loc[x, 'symbol']} - "
                        f"{portfolio.loc[x, 'buy_date']} - "
                        f"{portfolio.loc[x, 'shares']} shares"
                    ),
                )
            with col2:
                if st.button("Delete", type="secondary"):
                    try:
                        delete_position(delete_index)
                        st.success("Position deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting position: {str(e)}")

with tab2:
    st.header("Portfolio Analysis")

    portfolio = load_portfolio()

    if portfolio.empty:
        st.info("Add some positions in the Portfolio Management tab to see analysis.")
    else:
        # Enrich portfolio for performance metrics
        with st.spinner("Calculating portfolio metrics..."):
            enriched = enrich_portfolio(portfolio)

        # Display summary metrics at top
        st.subheader("Overall Performance")
        col1, col2, col3 = st.columns(3)

        total_cost = enriched["cost_basis"].sum()
        total_current = enriched[enriched["status"] == "Open"]["current_value"].sum()
        total_sold = enriched[enriched["status"] == "Closed"]["sold_value"].sum()
        total_value = total_current + total_sold
        total_gain_loss = enriched["gain_loss"].sum()

        with col1:
            st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        with col2:
            st.metric("Total Invested", f"${total_cost:,.2f}")
        with col3:
            gain_loss_pct = (
                (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            )
            st.metric(
                "Total Return",
                f"${total_gain_loss:,.2f}",
                f"{gain_loss_pct:,.2f}%",
            )

        # Net Worth Over Time Chart
        st.subheader("Portfolio Value Over Time")
        with st.spinner("Calculating historical portfolio values..."):
            history = calculate_portfolio_history(portfolio)

        if not history.empty:
            render_portfolio_chart(history)

            # Show date range
            start_date = history["date"].min().strftime("%Y-%m-%d")
            end_date = history["date"].max().strftime("%Y-%m-%d")
            st.caption(f"Showing portfolio value from {start_date} to {end_date}")
        else:
            st.info("Not enough data to generate portfolio history chart.")

        # Position Performance Breakdown
        st.subheader("Position Performance")
        performance = get_position_performance(enriched)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Top Gainers**")
            if not performance["top_gainers"].empty:
                gainers_display = performance["top_gainers"][
                    ["symbol", "gain_loss", "gain_loss_pct", "status"]
                ].copy()
                gainers_display["gain_loss"] = gainers_display["gain_loss"].apply(
                    lambda x: f"${x:,.2f}"
                )
                gainers_display["gain_loss_pct"] = gainers_display[
                    "gain_loss_pct"
                ].apply(lambda x: f"{x:,.2f}%")
                gainers_display.columns = ["Symbol", "Gain/Loss", "%", "Status"]
                st.dataframe(gainers_display, width="stretch", hide_index=True)
            else:
                st.info("No data available")

        with col2:
            st.write("**Top Losers**")
            if not performance["top_losers"].empty:
                losers_display = performance["top_losers"][
                    ["symbol", "gain_loss", "gain_loss_pct", "status"]
                ].copy()
                losers_display["gain_loss"] = losers_display["gain_loss"].apply(
                    lambda x: f"${x:,.2f}"
                )
                losers_display["gain_loss_pct"] = losers_display["gain_loss_pct"].apply(
                    lambda x: f"{x:,.2f}%"
                )
                losers_display.columns = ["Symbol", "Gain/Loss", "%", "Status"]
                st.dataframe(losers_display, width="stretch", hide_index=True)
            else:
                st.info("No data available")

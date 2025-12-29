import streamlit as st
from datetime import date
from config.settings import SYMBOLS


def render_portfolio_form():
    """Render form for adding new portfolio positions."""
    st.subheader("Add New Position")

    with st.form("add_position_form"):
        col1, col2 = st.columns(2)

        with col1:
            symbol = st.selectbox(
                "Stock Symbol", SYMBOLS, help="Select the stock ticker symbol"
            )
            buy_date = st.date_input(
                "Buy Date", max_value=date.today(), help="Date you purchased the stock"
            )

        with col2:
            shares = st.number_input(
                "Number of Shares",
                min_value=0.0,
                step=0.01,
                help="How many shares did you buy?",
            )
            sell_date = st.date_input(
                "Sell Date (Optional)",
                value=None,
                max_value=date.today(),
                help="Leave blank if you still own the stock",
            )

        submitted = st.form_submit_button("Add Position")

        if submitted:
            # Validation
            if shares <= 0:
                st.error("Number of shares must be greater than 0")
                return None
            if sell_date and sell_date < buy_date:
                st.error("Sell date cannot be before buy date")
                return None

            return {
                "symbol": symbol.strip().upper(),
                "buy_date": buy_date.strftime("%Y-%m-%d"),
                "shares": shares,
                "sell_date": sell_date.strftime("%Y-%m-%d") if sell_date else None,
            }

    return None

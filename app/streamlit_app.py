import streamlit as st
from components.portfolio_form import render_portfolio_form
from services.portfolio_service import (
    load_portfolio,
    add_position,
    delete_position,
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
        # Display portfolio as table
        st.dataframe(portfolio, use_container_width=True)

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
    st.info("Analysis features coming soon!")

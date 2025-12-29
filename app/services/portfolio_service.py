import pandas as pd
from pathlib import Path
from .stock_service import get_close_price, get_current_price


PORTFOLIO_FILE = Path(__file__).parent.parent.parent / "data" / "portfolio.csv"


def load_portfolio():
    """Load portfolio from CSV file."""
    if not PORTFOLIO_FILE.exists():
        # Create empty portfolio with correct columns and dtypes
        df = pd.DataFrame(
            {
                "symbol": pd.Series(dtype="str"),
                "buy_date": pd.Series(dtype="str"),
                "shares": pd.Series(dtype="float"),
                "sell_date": pd.Series(dtype="str"),
            }
        )
        PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(PORTFOLIO_FILE, index=False)
        return df
    # Keep empty strings as empty strings, not NaN
    df = pd.read_csv(PORTFOLIO_FILE, keep_default_na=False)
    return df


def save_portfolio(df):
    """Save portfolio DataFrame to CSV file."""
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PORTFOLIO_FILE, index=False)


def add_position(symbol, buy_date, shares, sell_date=None):
    """Add a new position to the portfolio."""
    df = load_portfolio()
    new_row = {
        "symbol": symbol.upper(),
        "buy_date": buy_date,
        "shares": shares,
        "sell_date": sell_date if sell_date else "",
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_portfolio(df)
    return df


def delete_position(index):
    """Delete a position from the portfolio by index."""
    df = load_portfolio()
    df = df.drop(index)
    df = df.reset_index(drop=True)
    save_portfolio(df)
    return df


def enrich_portfolio(df):
    """
    Enrich portfolio DataFrame with calculated fields.

    Adds columns:
    - buy_price: Price at purchase date
    - sell_price: Price at sell date (if sold)
    - current_price: Current market price (for open positions)
    - cost_basis: Total cost (shares * buy_price)
    - current_value: Current total value (for open positions)
    - sold_value: Total sold value (for closed positions)
    - gain_loss: Dollar gain/loss
    - gain_loss_pct: Percentage gain/loss
    - status: 'Open' or 'Closed'
    """
    if df.empty:
        return df

    # Initialize new columns
    enriched = df.copy()
    enriched["buy_price"] = 0.0
    enriched["sell_price"] = 0.0
    enriched["current_price"] = 0.0
    enriched["cost_basis"] = 0.0
    enriched["current_value"] = 0.0
    enriched["sold_value"] = 0.0
    enriched["gain_loss"] = 0.0
    enriched["gain_loss_pct"] = 0.0
    enriched["status"] = ""

    # Process each position
    for idx in enriched.index:
        symbol = enriched.loc[idx, "symbol"]
        shares = enriched.loc[idx, "shares"]
        buy_date = enriched.loc[idx, "buy_date"]
        sell_date = enriched.loc[idx, "sell_date"]

        # Fetch buy price
        buy_price = get_close_price(symbol, buy_date)
        if buy_price is None:
            buy_price = 0.0
        enriched.loc[idx, "buy_price"] = buy_price

        # Calculate cost basis
        cost_basis = shares * buy_price
        enriched.loc[idx, "cost_basis"] = cost_basis

        # Check if position is open or closed
        is_closed = sell_date and sell_date != ""

        if is_closed:
            # Closed position
            enriched.loc[idx, "status"] = "Closed"
            sell_price = get_close_price(symbol, sell_date)
            if sell_price is None:
                sell_price = 0.0
            enriched.loc[idx, "sell_price"] = sell_price

            sold_value = shares * sell_price
            enriched.loc[idx, "sold_value"] = sold_value

            gain_loss = sold_value - cost_basis
            enriched.loc[idx, "gain_loss"] = gain_loss

            if cost_basis > 0:
                enriched.loc[idx, "gain_loss_pct"] = (gain_loss / cost_basis) * 100
        else:
            # Open position
            enriched.loc[idx, "status"] = "Open"
            current_price = get_current_price(symbol)
            if current_price is None:
                current_price = 0.0
            enriched.loc[idx, "current_price"] = current_price

            current_value = shares * current_price
            enriched.loc[idx, "current_value"] = current_value

            gain_loss = current_value - cost_basis
            enriched.loc[idx, "gain_loss"] = gain_loss

            if cost_basis > 0:
                enriched.loc[idx, "gain_loss_pct"] = (gain_loss / cost_basis) * 100

    return enriched


def calculate_portfolio_history(df):
    """
    Calculate daily portfolio value over time.

    For each day from earliest buy date to today:
    - Include all positions that were held on that day
    - Calculate value based on historical prices

    Returns:
        DataFrame with columns: date, portfolio_value
    """
    if df.empty:
        return pd.DataFrame(columns=["date", "portfolio_value"])

    from datetime import datetime

    # Find earliest buy date
    earliest_date = pd.to_datetime(df["buy_date"]).min()
    today = datetime.now()

    # Generate date range
    date_range = pd.date_range(start=earliest_date, end=today, freq="D")

    portfolio_values = []

    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")
        daily_value = 0.0

        # Check each position
        for idx in df.index:
            buy_date = pd.to_datetime(df.loc[idx, "buy_date"])
            sell_date_str = df.loc[idx, "sell_date"]
            sell_date = pd.to_datetime(sell_date_str) if sell_date_str else None
            symbol = df.loc[idx, "symbol"]
            shares = df.loc[idx, "shares"]

            # Check if position was held on this date
            if date < buy_date:
                continue  # Not bought yet
            if sell_date and date > sell_date:
                continue  # Already sold

            # Get price for this date
            if sell_date and date.date() == sell_date.date():
                # Use sell price on sell date
                price = get_close_price(symbol, date_str)
            elif date.date() == today.date():
                # Use current price for today
                price = get_current_price(symbol)
            else:
                # Use historical close price
                price = get_close_price(symbol, date_str)

            if price:
                daily_value += shares * price

        portfolio_values.append({"date": date, "portfolio_value": daily_value})

    result = pd.DataFrame(portfolio_values)
    return result


def get_position_performance(enriched_df):
    """
    Analyze position performance and return top/bottom performers.

    Args:
        enriched_df: Enriched portfolio DataFrame

    Returns:
        Dictionary with 'top_gainers' and 'top_losers' DataFrames
    """
    if enriched_df.empty:
        return {"top_gainers": pd.DataFrame(), "top_losers": pd.DataFrame()}

    # Select relevant columns for performance view
    perf_df = enriched_df[
        [
            "symbol",
            "shares",
            "cost_basis",
            "current_value",
            "sold_value",
            "gain_loss",
            "gain_loss_pct",
            "status",
        ]
    ].copy()

    # Sort by gain/loss percentage
    sorted_df = perf_df.sort_values("gain_loss_pct", ascending=False)

    # Get top 5 gainers and losers
    top_gainers = sorted_df.head(5)
    top_losers = sorted_df.tail(5).sort_values("gain_loss_pct", ascending=True)

    return {"top_gainers": top_gainers, "top_losers": top_losers}

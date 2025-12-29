import pandas as pd
from pathlib import Path


PORTFOLIO_FILE = Path(__file__).parent.parent.parent / "data" / "portfolio.csv"


def load_portfolio():
    """Load portfolio from CSV file."""
    if not PORTFOLIO_FILE.exists():
        # Create empty portfolio with correct columns
        df = pd.DataFrame(columns=["symbol", "buy_date", "shares", "sell_date"])
        PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(PORTFOLIO_FILE, index=False)
        return df
    return pd.read_csv(PORTFOLIO_FILE)


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

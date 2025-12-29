import yfinance as yf


def get_stock_data(ticker: str, period: str = "1y"):
    """Fetch stock history for a given ticker."""
    stock = yf.Ticker(ticker)
    return stock.history(period=period)


def get_stock_info(ticker: str):
    """Get company info (name, sector, market cap)"""
    return yf.Ticker(ticker).info

import yfinance as yf
from datetime import datetime, timedelta
import time

# Simple cache to avoid repeated API calls
_price_cache = {}

# Track errors for UI display
_errors = []


def get_errors():
    """Get list of errors encountered during price fetching."""
    return _errors.copy()


def clear_errors():
    """Clear the error list."""
    global _errors
    _errors = []


def get_close_price(ticker: str, date: str):
    """
    Get the close price for a ticker on a specific date.

    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        date: Date string in format 'YYYY-MM-DD'

    Returns:
        Close price as float, or None if data not available
    """
    # Check cache first
    cache_key = f"{ticker}_{date}"
    if cache_key in _price_cache:
        return _price_cache[cache_key]
    
    try:
        # Parse the date
        target_date = datetime.strptime(date, "%Y-%m-%d")

        # Fetch data for a range around the target date
        # (in case target date is weekend/holiday)
        start_date = target_date - timedelta(days=7)
        end_date = target_date + timedelta(days=1)

        stock = yf.Ticker(ticker)
        history = stock.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )
        
        # Add small delay to avoid rate limiting
        time.sleep(0.1)

        if history.empty:
            return None

        # Find the closest date to our target
        # Remove timezone info if present
        if hasattr(history.index, "tz_localize"):
            history.index = history.index.tz_localize(None)  # type: ignore
        closest_date = min(history.index, key=lambda x: abs(x - target_date))

        close_price = history.loc[closest_date, "Close"]
        result = float(close_price)  # type: ignore
        
        # Cache the result
        _price_cache[cache_key] = result
        return result

    except Exception as e:
        error_msg = f"Error fetching price for {ticker} on {date}: {str(e)}"
        print(error_msg)
        _errors.append(error_msg)
        return None


def get_current_price(ticker: str):
    """
    Get the current/latest price for a ticker.

    Args:
        ticker: Stock symbol (e.g., 'AAPL')

    Returns:
        Current price as float, or None if data not available
    """
    # Check cache (with today's date as key)
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"{ticker}_current_{today}"
    if cache_key in _price_cache:
        return _price_cache[cache_key]
    
    try:
        stock = yf.Ticker(ticker)
        # Get last 2 days of data to ensure we have recent price
        history = stock.history(period="2d")
        
        # Add small delay to avoid rate limiting
        time.sleep(0.1)

        if history.empty:
            return None

        current_price = history["Close"].iloc[-1]
        result = float(current_price)  # type: ignore
        
        # Cache the result
        _price_cache[cache_key] = result
        return result

    except Exception as e:
        error_msg = f"Error fetching current price for {ticker}: {str(e)}"
        print(error_msg)
        _errors.append(error_msg)
        return None


def get_stock_data(ticker: str, period: str = "1y"):
    """Fetch stock history for a given ticker."""
    stock = yf.Ticker(ticker)
    return stock.history(period=period)


def get_stock_info(ticker: str):
    """Get company info (name, sector, market cap)"""
    return yf.Ticker(ticker).info

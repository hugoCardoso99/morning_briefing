"""
Stocks node — fetches market data using yfinance.
Returns ticker, previous close, current price, and daily % change.
Skipped entirely on weekends (returns empty list).
"""

import yfinance as yf
from datetime import datetime


def stocks_node(state) -> dict:
    """Fetch stock data for configured tickers."""
    is_weekend = state.is_weekend
    tickers = state.tickers

    # Skip on weekends — markets are closed
    if is_weekend:
        return {"stocks": []}

    if not tickers:
        return {"stocks": []}

    results = []

    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info

            previous_close = getattr(info, "previous_close", None)
            current_price = getattr(info, "last_price", None)

            # Calculate daily % change
            daily_change_pct = None
            if previous_close and current_price and previous_close != 0:
                daily_change_pct = ((current_price - previous_close) / previous_close) * 100

            # Determine last trading day for staleness annotation
            hist = ticker.history(period="5d")
            last_trading_date = None
            if not hist.empty:
                last_trading_date = hist.index[-1].strftime("%Y-%m-%d")

            results.append({
                "symbol": symbol,
                "previous_close": round(previous_close, 2) if previous_close else None,
                "current_price": round(current_price, 2) if current_price else None,
                "daily_change_pct": round(daily_change_pct, 2) if daily_change_pct else None,
                "last_trading_date": last_trading_date,
                "error": None,
            })

        except Exception as e:
            results.append({
                "symbol": symbol,
                "previous_close": None,
                "current_price": None,
                "daily_change_pct": None,
                "last_trading_date": None,
                "error": str(e),
            })

    return {"stocks": results}

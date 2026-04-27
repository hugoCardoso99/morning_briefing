"""
Router node — applies business rules to filter, prioritize, and annotate
the data collected by the API nodes.

Rules:
1. Weekend logic: skip stocks, deprioritize calendar if no notable dates
2. Severe weather: promote weather section to top with warning
3. Market staleness: annotate stale stock data
4. Keyword flagging: pin matching headlines to top of news
5. Holiday alert: flag if today or tomorrow is a Portuguese holiday
"""

from datetime import datetime


def router_node(state) -> dict:
    """Apply routing rules and produce annotations for the compiler."""
    is_weekend = state.is_weekend
    weather_data = state.weather
    news_data = state.news
    calendar_data = state.calendar
    stocks_data = state.stocks
    keywords = state.news_keywords

    alerts = []
    skipped_sections = []
    flagged_headlines = []

    # Default section order
    sections_order = ["weather", "calendar", "news", "stocks"]

    # -----------------------------------------------------------------------
    # Rule 1: Weekend logic
    # -----------------------------------------------------------------------
    if is_weekend:
        skipped_sections.append("stocks")
        if "stocks" in sections_order:
            sections_order.remove("stocks")

        # Deprioritize calendar if no notable dates
        today_notable = calendar_data.get("today_notable", [])
        tomorrow_notable = calendar_data.get("tomorrow_notable", [])
        if not today_notable and not tomorrow_notable:
            if "calendar" in sections_order:
                sections_order.remove("calendar")
                sections_order.append("calendar")  # move to end
            alerts.append("Weekend mode — no notable dates, calendar moved to end")

    # -----------------------------------------------------------------------
    # Rule 2: Severe weather — promote to top
    # -----------------------------------------------------------------------
    has_severe = False
    for city, data in weather_data.items():
        if isinstance(data, dict) and data.get("severe_warnings"):
            has_severe = True
            for warning in data["severe_warnings"]:
                alerts.append(f"⚠ {city}: {warning}")

    if has_severe and sections_order[0] != "weather":
        sections_order.remove("weather")
        sections_order.insert(0, "weather")

    # -----------------------------------------------------------------------
    # Rule 3: Market staleness annotation
    # -----------------------------------------------------------------------
    today_str = state.date or datetime.now().strftime("%Y-%m-%d")
    for stock in stocks_data:
        last_trade = stock.get("last_trading_date")
        if last_trade and last_trade != today_str:
            stock["stale_note"] = f"Last trading day: {last_trade}"

    # -----------------------------------------------------------------------
    # Rule 4: Keyword flagging on news
    # -----------------------------------------------------------------------
    if keywords:
        lower_keywords = [k.lower() for k in keywords]
        for article in news_data:
            headline_lower = article.get("headline", "").lower()
            matched = [
                kw for kw in lower_keywords
                if kw in headline_lower
            ]
            if matched:
                flagged_headlines.append({
                    **article,
                    "matched_keywords": matched,
                })

    # -----------------------------------------------------------------------
    # Rule 5: Holiday alert — promote if notable, demote to last if empty
    # -----------------------------------------------------------------------
    today_notable = calendar_data.get("today_notable", [])
    tomorrow_notable = calendar_data.get("tomorrow_notable", [])
    has_notable = bool(today_notable or tomorrow_notable)

    if has_notable:
        if calendar_data.get("is_holiday_today"):
            for note in today_notable:
                alerts.insert(0, f"🎉 Today is {note}")
        if calendar_data.get("is_holiday_tomorrow"):
            for note in tomorrow_notable:
                alerts.append(f"📅 Tomorrow is {note}")
    else:
        # No notable dates — move calendar to the end
        if "calendar" in sections_order:
            sections_order.remove("calendar")
            sections_order.append("calendar")

    return {
        "alerts": alerts,
        "sections_order": sections_order,
        "flagged_headlines": flagged_headlines,
        "skipped_sections": skipped_sections,
    }

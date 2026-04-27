"""
Compiler node — assembles all data and router annotations into a
well-formatted Markdown briefing document.
"""

from datetime import datetime


def _compile_alerts(alerts: list[str]) -> str:
    """Render alert banners at the top."""
    if not alerts:
        return ""
    lines = ["## Alerts", ""]
    for alert in alerts:
        lines.append(f"> {alert}")
        lines.append(">")
    lines.append("")
    return "\n".join(lines)


def _temp_emoji(temp) -> str:
    """Return an emoji based on temperature."""
    if temp is None:
        return "🌡️"
    if temp >= 35:
        return "🔥"
    if temp >= 25:
        return "☀️"
    if temp >= 15:
        return "🌤️"
    if temp >= 5:
        return "🧥"
    return "🥶"


def _rain_emoji(probability) -> str:
    """Return an emoji based on rain probability."""
    if probability is None:
        return "❓"
    if probability >= 70:
        return "🌧️"
    if probability >= 40:
        return "🌦️"
    if probability >= 10:
        return "🌥️"
    return "☀️"


def _wind_emoji(speed) -> str:
    """Return an emoji based on wind speed."""
    if speed is None:
        return "🌬️"
    if speed >= 50:
        return "💨💨"
    if speed >= 30:
        return "💨"
    return "🍃"


def _weather_remark(temp, rain_prob, wind_max, weather_code) -> str:
    """Generate a funny remark based on weather conditions."""
    # Check most impactful conditions first
    if weather_code is not None and weather_code >= 95:
        return "⛈️ Stay home, watch Netflix, and pretend you planned this!"
    if rain_prob is not None and rain_prob >= 80:
        return "☔ Grab an umbrella... or two. Noah vibes today!"
    if rain_prob is not None and rain_prob >= 50:
        return "🌂 An umbrella wouldn't hurt — the clouds look suspicious."
    if wind_max is not None and wind_max >= 50:
        return "💨 Hold onto your hat! Literally."
    if temp is not None and temp >= 35:
        return "🔥 Oh if we could wear sandals to work... stay hydrated!"
    if temp is not None and temp >= 30:
        return "😎 Sunglasses mandatory. Sunscreen non-negotiable."
    if temp is not None and temp >= 25:
        return "🌞 T-shirt weather! Life is good."
    if temp is not None and temp >= 18:
        return "👌 Perfect weather — no complaints allowed today."
    if temp is not None and temp >= 12:
        return "🧥 Grab a jacket, just in case. You know how it is."
    if temp is not None and temp >= 5:
        return "🧣 Grab a coat! Scarf wouldn't hurt either."
    if temp is not None and temp < 5:
        return "🥶 Bundle up! It's freezing out there. Hot coffee mandatory."
    if weather_code is not None and weather_code >= 71:
        return "❄️ Snow day! Build a snowman or call it a remote work day."
    return "🤷 Weather is... weather. Dress in layers and hope for the best."


def _compile_weather(weather_data: dict) -> str:
    """Render weather section with emojis and funny remarks."""
    if not weather_data:
        return "_No weather data available._\n"

    lines = ["## 🌍 Weather", ""]

    for city, data in weather_data.items():
        if isinstance(data, dict) and data.get("error"):
            lines.append(f"### {city}")
            lines.append(f"_Error: {data['error']}_")
            lines.append("")
            continue

        current = data.get("current", {})
        daily = data.get("daily", {})
        warnings = data.get("severe_warnings", [])

        lines.append(f"### {city}")
        lines.append("")

        if warnings:
            for w in warnings:
                lines.append(f"> ⚠️ **{w}**")
            lines.append("")

        temp_now = current.get('temperature')
        weather_code = current.get('weathercode')
        lines.append(f"**Currently:** {_temp_emoji(temp_now)} {temp_now}°C — {current.get('description', '?')}")
        lines.append("")

        temp_max = daily.get('temp_max')
        temp_min = daily.get('temp_min')
        rain_prob = daily.get('rain_probability')
        wind_max = daily.get('wind_max')

        # Funny remark based on conditions
        remark = _weather_remark(temp_max, rain_prob, wind_max, weather_code)
        lines.append(f"> _{remark}_")
        lines.append("")

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| {_temp_emoji(temp_max)} High / {_temp_emoji(temp_min)} Low | {temp_max}°C / {temp_min}°C |")
        lines.append(f"| {_rain_emoji(rain_prob)} Rain probability | {rain_prob}% |")
        lines.append(f"| {_wind_emoji(wind_max)} Max wind | {wind_max} km/h |")
        lines.append(f"| 🌅 Sunrise / 🌇 Sunset | {daily.get('sunrise', '?')} / {daily.get('sunset', '?')} |")
        lines.append("")

    return "\n".join(lines)


def _compile_calendar(calendar_data: dict) -> str:
    """Render calendar section — Portuguese holidays and notable dates."""
    if not calendar_data:
        return "_No calendar data available._\n"

    lines = ["## 📅 Notable Dates (Portugal)", ""]

    today_date = calendar_data.get("today_date", "")
    tomorrow_date = calendar_data.get("tomorrow_date", "")
    today_notable = calendar_data.get("today_notable", [])
    tomorrow_notable = calendar_data.get("tomorrow_notable", [])

    # Today
    lines.append(f"### Today — {today_date}")
    lines.append("")
    if today_notable:
        for note in today_notable:
            lines.append(f"- **{note}**")
    else:
        lines.append("_No holidays or notable dates today._")
    lines.append("")

    # Tomorrow
    lines.append(f"### Tomorrow — {tomorrow_date}")
    lines.append("")
    if tomorrow_notable:
        for note in tomorrow_notable:
            lines.append(f"- **{note}**")
    else:
        lines.append("_No holidays or notable dates tomorrow._")
    lines.append("")

    return "\n".join(lines)


CATEGORY_EMOJIS = {
    "Economia": "💰",
    "Política": "🏛️",
    "Desporto": "⚽",
    "Sociedade": "👥",
    "Mundo": "🌍",
    "Internacional": "🌍",
    "Tecnologia": "💻",
    "Cultura": "🎭",
    "Opinião": "💬",
    "Ciência": "🔬",
    "Saúde": "🏥",
    "Educação": "📚",
    "Justiça": "⚖️",
    "Local": "📍",
    "País": "🇵🇹",
    "Geral": "📰",
}


def _compile_news(news_data: list[dict], flagged: list[dict]) -> str:
    """Render news section grouped by category with flagged headlines pinned to top."""
    if not news_data:
        return "_No news articles available._\n"

    lines = ["## 📰 News", ""]

    # Pinned / flagged headlines first
    if flagged:
        lines.append("### 🔔 Flagged Headlines")
        lines.append("")
        for article in flagged:
            keywords_str = ", ".join(article.get("matched_keywords", []))
            headline = article["headline"]
            url = article.get("url", "")
            source = article.get("source", "")

            if url:
                lines.append(f"- **[{headline}]({url})** _({source} | keywords: {keywords_str})_")
            else:
                lines.append(f"- **{headline}** _({source} | keywords: {keywords_str})_")
        lines.append("")

    # Group remaining articles by category
    flagged_headlines_set = {a["headline"] for a in flagged}
    remaining = [a for a in news_data if a["headline"] not in flagged_headlines_set]

    categories: dict[str, list[dict]] = {}
    for article in remaining:
        cat = article.get("category", "Geral")
        categories.setdefault(cat, []).append(article)

    for category, articles in sorted(categories.items()):
        emoji = CATEGORY_EMOJIS.get(category, "📰")
        lines.append(f"### {emoji} {category}")
        lines.append("")
        for article in articles:
            headline = article["headline"]
            url = article.get("url", "")
            source = article.get("source", "")

            if url:
                lines.append(f"- **[{headline}]({url})** _({source})_")
            else:
                lines.append(f"- **{headline}** _({source})_")
        lines.append("")

    return "\n".join(lines)


def _change_emoji(change) -> str:
    """Return an emoji based on stock daily % change."""
    if change is None:
        return "➖"
    if change >= 3:
        return "🚀"
    if change >= 1:
        return "📈"
    if change > 0:
        return "🟢"
    if change == 0:
        return "➖"
    if change > -1:
        return "🔴"
    if change > -3:
        return "📉"
    return "💥"


def _compile_stocks(stocks_data: list[dict], finance_news: list[dict] = None) -> str:
    """Render stocks section as a table with emojis, plus finance news."""
    if not stocks_data and not finance_news:
        return "_Stock data not available (markets may be closed)._\n"

    lines = ["## 📊 Stocks", ""]
    lines.append("| | Ticker | Prev Close | Current | Change |")
    lines.append("|--|--------|-----------|---------|--------|")

    for stock in stocks_data:
        if stock.get("error"):
            lines.append(f"| ⚠️ | {stock['symbol']} | — | — | _Error_ |")
            continue

        symbol = stock["symbol"]
        prev = f"€{stock['previous_close']}" if stock.get("previous_close") else "—"
        current = f"€{stock['current_price']}" if stock.get("current_price") else "—"

        change = stock.get("daily_change_pct")
        emoji = _change_emoji(change)
        if change is not None:
            arrow = "+" if change >= 0 else ""
            change_str = f"{arrow}{change}%"
        else:
            change_str = "—"

        lines.append(f"| {emoji} | {symbol} | {prev} | {current} | {change_str} |")

    # Add staleness notes
    stale_notes = [s.get("stale_note") for s in stocks_data if s.get("stale_note")]
    if stale_notes:
        lines.append("")
        for note in stale_notes:
            lines.append(f"_⏳ {note}_")

    # Finance news below the table
    if finance_news:
        lines.append("")
        lines.append("### 📰 Finance News")
        lines.append("")
        for article in finance_news:
            title = article.get("title", "")
            url = article.get("url", "")
            publisher = article.get("publisher", "")
            pub_str = f" _({publisher})_" if publisher else ""

            if url:
                lines.append(f"- **[{title}]({url})**{pub_str}")
            else:
                lines.append(f"- **{title}**{pub_str}")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


# Section renderer mapping
SECTION_RENDERERS = {
    "weather": lambda state: _compile_weather(state.weather),
    "calendar": lambda state: _compile_calendar(state.calendar),
    "news": lambda state: _compile_news(state.news, state.flagged_headlines),
    "stocks": lambda state: _compile_stocks(state.stocks, state.finance_news),
}


def compiler_node(state) -> dict:
    """Assemble the final markdown briefing."""
    date = state.date or datetime.now().strftime("%Y-%m-%d")
    day = state.day_of_week
    alerts = state.alerts
    sections_order = state.sections_order
    skipped = set(state.skipped_sections)

    parts = []

    # Header
    parts.append(f"# Morning Briefing — {day}, {date}")
    parts.append("")
    parts.append(f"_Generated at {datetime.now().strftime('%H:%M')}_")
    parts.append("")

    # Alerts
    if alerts:
        parts.append(_compile_alerts(alerts))

    parts.append("---")
    parts.append("")

    # Sections in router-determined order
    for section in sections_order:
        if section in skipped:
            continue
        renderer = SECTION_RENDERERS.get(section)
        if renderer:
            parts.append(renderer(state))
            parts.append("---")
            parts.append("")

    # Footer
    parts.append("_End of briefing._")

    markdown = "\n".join(parts)
    return {"markdown": markdown}

"""
Review node — human-in-the-loop checkpoint between router and compiler.

Uses LangGraph's interrupt() to pause the graph and present the user
with a summary of what the router decided. The caller (main.py) collects
user input and applies any overrides directly to the state via
graph.update_state() before resuming. This node simply pauses and resumes.
"""

from langgraph.types import interrupt


def _section_summary(state) -> dict:
    """Build a summary of each section's content for the review UI."""
    summary = {}

    # Weather
    weather = state.weather
    if weather:
        cities = list(weather.keys())
        errors = [c for c, d in weather.items() if isinstance(d, dict) and d.get("error")]
        severe = []
        for c, d in weather.items():
            if isinstance(d, dict):
                for w in d.get("severe_warnings", []):
                    severe.append(f"{c}: {w}")
        summary["weather"] = {
            "count": len(cities),
            "detail": f"{len(cities)} cities ({', '.join(cities)})",
            "warnings": severe,
            "errors": errors,
            "empty": False,
        }
    else:
        summary["weather"] = {"count": 0, "detail": "no data", "empty": True}

    # News
    news = state.news
    if news:
        sources = {}
        for a in news:
            src = a.get("source", "?")
            sources[src] = sources.get(src, 0) + 1
        source_str = ", ".join(f"{count} from {src}" for src, count in sources.items())
        categories = set(a.get("category", "Geral") for a in news)
        summary["news"] = {
            "count": len(news),
            "detail": f"{len(news)} articles ({source_str}) across {len(categories)} categories",
            "empty": False,
        }
    else:
        summary["news"] = {"count": 0, "detail": "no articles scraped", "empty": True}

    # Calendar
    calendar = state.calendar
    today_notable = calendar.get("today_notable", []) if calendar else []
    tomorrow_notable = calendar.get("tomorrow_notable", []) if calendar else []
    has_notable = bool(today_notable or tomorrow_notable)
    if has_notable:
        items = today_notable + tomorrow_notable
        summary["calendar"] = {
            "count": len(items),
            "detail": "; ".join(items),
            "empty": False,
        }
    else:
        summary["calendar"] = {
            "count": 0,
            "detail": "no holidays or notable dates",
            "empty": True,
        }

    # Stocks
    stocks = state.stocks
    finance_news = state.finance_news
    if stocks:
        tickers = [s["symbol"] for s in stocks if s.get("symbol")]
        errors = [s["symbol"] for s in stocks if s.get("error")]
        summary["stocks"] = {
            "count": len(stocks),
            "detail": f"{len(stocks)} tickers ({', '.join(tickers)})",
            "finance_news_count": len(finance_news),
            "errors": errors,
            "empty": False,
        }
    elif finance_news:
        summary["stocks"] = {
            "count": 0,
            "detail": f"no ticker data, but {len(finance_news)} finance news articles",
            "finance_news_count": len(finance_news),
            "empty": False,
        }
    else:
        summary["stocks"] = {
            "count": 0,
            "detail": "no data (markets may be closed)",
            "finance_news_count": 0,
            "empty": True,
        }

    return summary


def review_node(state) -> dict:
    """
    Pause execution and present the routing plan for human review.

    The interrupt payload contains the current routing plan plus a summary
    of each section's content so the user can make informed decisions.
    The caller applies overrides to state directly (via graph.update_state),
    then resumes the graph.
    """
    review_payload = {
        "sections_order": list(state.sections_order),
        "skipped_sections": list(state.skipped_sections),
        "alerts": list(state.alerts),
        "flagged_headlines": [
            {"headline": h.get("headline", ""), "keywords": h.get("matched_keywords", [])}
            for h in state.flagged_headlines
        ],
        "available_sections": ["weather", "calendar", "news", "stocks"],
        "section_summary": _section_summary(state),
    }

    # This pauses the graph and returns the payload to the caller
    interrupt(review_payload)

    # State overrides have already been applied by main.py via graph.update_state()
    return {}

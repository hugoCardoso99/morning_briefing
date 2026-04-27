"""
LangGraph definition for the Morning Briefing Orchestrator.

Graph topology:
  init → [weather, news, calendar, stocks] (parallel)
  stocks → finance_news (chained)
  [weather, news, calendar, finance_news] → router → compiler
"""

from typing import Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

from nodes.init_node import init_node
from nodes.weather import weather_node
from nodes.news import news_node
from nodes.calendar_node import calendar_node
from nodes.stocks import stocks_node
from nodes.finance_news import finance_news_node
from nodes.router import router_node
from nodes.compiler import compiler_node


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class BriefingState(BaseModel):
    # --- User configuration (set at input) ---
    cities: list[str] = Field(default_factory=list, description="Cities to check weather for")
    tickers: list[str] = Field(default_factory=list, description="Stock tickers to track")
    news_keywords: list[str] = Field(default_factory=list, description="Keywords to flag in news")

    # --- Context (populated by init node) ---
    date: str = ""
    day_of_week: str = ""
    is_weekend: bool = False

    # --- Results (populated by API nodes) ---
    weather: dict[str, Any] = Field(default_factory=dict, description="City -> forecast data")
    news: list[dict[str, Any]] = Field(default_factory=list, description="Scraped articles")
    calendar: dict[str, Any] = Field(default_factory=dict, description="Today/tomorrow events")
    stocks: list[dict[str, Any]] = Field(default_factory=list, description="Ticker data")
    finance_news: list[dict[str, Any]] = Field(default_factory=list, description="General finance news")

    # --- Router annotations ---
    alerts: list[str] = Field(default_factory=list, description="Warnings for top of briefing")
    sections_order: list[str] = Field(
        default_factory=lambda: ["weather", "calendar", "news", "stocks"],
        description="Ordered section names",
    )
    flagged_headlines: list[dict[str, Any]] = Field(default_factory=list, description="Keyword-matched headlines")
    skipped_sections: list[str] = Field(default_factory=list, description="Excluded sections")

    # --- Output ---
    markdown: str = ""


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Build and compile the morning briefing graph."""

    graph = StateGraph(BriefingState)

    # Register nodes
    graph.add_node("init", init_node)
    graph.add_node("weather", weather_node)
    graph.add_node("news", news_node)
    graph.add_node("calendar", calendar_node)
    graph.add_node("stocks", stocks_node)
    graph.add_node("finance_news", finance_news_node)
    graph.add_node("router", router_node)
    graph.add_node("compiler", compiler_node)

    # Entry point
    graph.set_entry_point("init")

    # After init, fan out to all four API nodes in parallel
    graph.add_edge("init", "weather")
    graph.add_edge("init", "news")
    graph.add_edge("init", "calendar")
    graph.add_edge("init", "stocks")

    # Chain: stocks → finance_news (sequential)
    graph.add_edge("stocks", "finance_news")

    # All branches converge into the router
    graph.add_edge("weather", "router")
    graph.add_edge("news", "router")
    graph.add_edge("calendar", "router")
    graph.add_edge("finance_news", "router")

    # Router flows into the compiler, then we're done
    graph.add_edge("router", "compiler")
    graph.add_edge("compiler", END)

    return graph.compile()

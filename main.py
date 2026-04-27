"""
Morning Briefing Orchestrator — Entry Point

A LangGraph pipeline that combines weather, news, calendar, and stock data
into a formatted morning briefing markdown document.

Usage:
    python main.py

Configure your preferences in the USER_CONFIG section below.
"""

import os
import sys
from datetime import datetime

# Add project root to path so node imports work
sys.path.insert(0, os.path.dirname(__file__))

from graph import build_graph


# ===========================================================================
# USER CONFIGURATION — edit these to personalise your briefing
# ===========================================================================

USER_CONFIG = {
    # Cities to check weather for (geocoded automatically)
    "cities": ["Vila Verde", "Braga"],

    # Stock tickers to track (skipped on weekends)
    "tickers": ["VWCE.DE", "VUAA.DE"],

    # Keywords to flag in news headlines (case-insensitive)
    "news_keywords": ["economia", "política", "tecnologia"],
}


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("Building morning briefing graph...")
    graph = build_graph()

    print("Running pipeline...")
    print(f"  Cities:   {USER_CONFIG['cities']}")
    print(f"  Tickers:  {USER_CONFIG['tickers']}")
    print(f"  Keywords: {USER_CONFIG['news_keywords']}")
    print()

    # Run the graph with the user config as initial state
    result = graph.invoke({
        "cities": USER_CONFIG["cities"],
        "tickers": USER_CONFIG["tickers"],
        "news_keywords": USER_CONFIG["news_keywords"],
    })

    # Write the markdown output
    markdown = result.get("markdown", "# No output generated")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"briefing_{date_str}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Briefing saved to: {filepath}")
    print()


if __name__ == "__main__":
    main()

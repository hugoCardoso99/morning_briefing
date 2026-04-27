"""
Init node — populates date/time context into the graph state.
"""

from datetime import datetime


def init_node(state: dict) -> dict:
    """Determine date context and pass through user config."""
    now = datetime.now()
    day_of_week = now.strftime("%A")
    is_weekend = day_of_week in ("Saturday", "Sunday")

    return {
        "date": now.strftime("%Y-%m-%d"),
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
    }

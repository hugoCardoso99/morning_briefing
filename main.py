"""
Morning Briefing Orchestrator — Entry Point

A LangGraph pipeline that combines weather, news, calendar, and stock data
into a formatted morning briefing markdown document.

Usage:
    python main.py          # interactive mode (human-in-the-loop review)
    python main.py --auto   # automatic mode (skip review, compile directly)

Configure your preferences in the USER_CONFIG section below.
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

# Add project root to path so node imports work
sys.path.insert(0, os.path.dirname(__file__))

from graph import build_graph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command


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
# Human-in-the-loop review UI
# ===========================================================================

def _display_review(payload: dict) -> dict:
    """
    Display the routing plan and collect user input.
    Returns a dict of overrides (or approval).
    """
    print("\n" + "=" * 60)
    print("📋 REVIEW — Here's what the router decided:")
    print("=" * 60)

    # Section order
    sections = payload.get("sections_order", [])
    skipped = payload.get("skipped_sections", [])
    summary = payload.get("section_summary", {})

    # Section details with status indicators
    section_icons = {"weather": "🌍", "calendar": "📅", "news": "📰", "stocks": "📊"}
    print("\n  Sections (in order):")
    for i, section in enumerate(sections, 1):
        icon = section_icons.get(section, "📄")
        info = summary.get(section, {})
        detail = info.get("detail", "")
        empty = info.get("empty", False)
        status = "⚠ EMPTY" if empty else f"✓ {detail}"
        print(f"    {i}. {icon} {section:<10} — {status}")

    if skipped:
        print(f"\n  Skipped sections:")
        for section in skipped:
            icon = section_icons.get(section, "📄")
            info = summary.get(section, {})
            detail = info.get("detail", "")
            empty = info.get("empty", False)
            status = "empty" if empty else detail
            print(f"    ✗ {icon} {section:<10} — {status}")

    # Alerts
    alerts = payload.get("alerts", [])
    if alerts:
        print(f"\n  Alerts ({len(alerts)}):")
        for i, alert in enumerate(alerts):
            print(f"    [{i}] {alert}")

    # Flagged headlines
    flagged = payload.get("flagged_headlines", [])
    if flagged:
        print(f"\n  Flagged headlines ({len(flagged)}):")
        for h in flagged:
            kws = ", ".join(h.get("keywords", []))
            print(f"    • {h.get('headline', '?')} (keywords: {kws})")

    # Collect input
    print("\n" + "-" * 60)
    print("Options:")
    print("  [Enter]     Approve and compile")
    print("  [r]         Reorder sections (e.g. 'news,weather,stocks,calendar')")
    print("  [s]         Skip a section (e.g. 'calendar,stocks')")
    print("  [u]         Unskip — bring back a skipped section")
    print("  [d]         Dismiss alerts by index (e.g. '0,2')")
    print("-" * 60)

    choice = input("\nYour choice: ").strip().lower()

    if not choice:
        return {"approved": True}

    overrides = {}

    if choice == "r":
        new_order = input("New section order (comma-separated): ").strip()
        if new_order:
            overrides["sections_order"] = [s.strip() for s in new_order.split(",")]

    elif choice == "s":
        to_skip = input("Sections to skip (comma-separated): ").strip()
        if to_skip:
            skip_list = [s.strip() for s in to_skip.split(",")]
            overrides["skipped_sections"] = list(set(skipped + skip_list))
            # Also remove from sections_order
            new_order = [s for s in sections if s not in skip_list]
            overrides["sections_order"] = new_order

    elif choice == "u":
        available = payload.get("available_sections", [])
        not_shown = [s for s in available if s not in sections]
        if not_shown:
            print(f"  Currently skipped/absent: {', '.join(not_shown)}")
            to_add = input("Sections to bring back (comma-separated): ").strip()
            if to_add:
                add_list = [s.strip() for s in to_add.split(",")]
                overrides["sections_order"] = sections + add_list
                overrides["skipped_sections"] = [s for s in skipped if s not in add_list]
        else:
            print("  All sections are already included.")
            return {"approved": True}

    elif choice == "d":
        indices = input("Alert indices to dismiss (comma-separated): ").strip()
        if indices:
            overrides["remove_alerts"] = [int(i.strip()) for i in indices.split(",")]

    else:
        print("  Unrecognised option, approving as-is.")
        return {"approved": True}

    return overrides


# ===========================================================================
# Main
# ===========================================================================

def _save_briefing(markdown: str):
    """Save the markdown briefing to a file."""
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"briefing_{date_str}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\nBriefing saved to: {filepath}")


def main():
    auto_mode = "--auto" in sys.argv

    if auto_mode:
        print("Running in auto mode (no review step)...\n")
        graph = build_graph(checkpointer=None)

        result = graph.invoke({
            "cities": USER_CONFIG["cities"],
            "tickers": USER_CONFIG["tickers"],
            "news_keywords": USER_CONFIG["news_keywords"],
        })

        markdown = result.markdown if hasattr(result, 'markdown') else result.get("markdown", "")
        _save_briefing(markdown)
        return

    # Interactive mode with human-in-the-loop
    print("Running in interactive mode (use --auto to skip review)...\n")

    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print(f"  Cities:   {USER_CONFIG['cities']}")
    print(f"  Tickers:  {USER_CONFIG['tickers']}")
    print(f"  Keywords: {USER_CONFIG['news_keywords']}")
    print("\nFetching data from all sources...")

    # First invocation — runs until the interrupt in the review node
    result = graph.invoke(
        {
            "cities": USER_CONFIG["cities"],
            "tickers": USER_CONFIG["tickers"],
            "news_keywords": USER_CONFIG["news_keywords"],
        },
        config=config,
    )

    # Check if we hit an interrupt
    state = graph.get_state(config)

    if state.next:
        # We're paused at the review node — get the interrupt payload
        interrupt_data = state.tasks
        payload = {}
        for task in interrupt_data:
            if hasattr(task, "interrupts") and task.interrupts:
                payload = task.interrupts[0].value
                break

        if payload:
            # Show review UI and get user overrides
            user_response = _display_review(payload)

            # Apply overrides directly to the graph state before resuming
            if not user_response.get("approved", False):
                state_updates = {}

                if "sections_order" in user_response:
                    state_updates["sections_order"] = user_response["sections_order"]

                if "skipped_sections" in user_response:
                    state_updates["skipped_sections"] = user_response["skipped_sections"]

                if "remove_alerts" in user_response:
                    indices_to_remove = set(user_response["remove_alerts"])
                    current_alerts = payload.get("alerts", [])
                    state_updates["alerts"] = [
                        a for i, a in enumerate(current_alerts)
                        if i not in indices_to_remove
                    ]

                if state_updates:
                    graph.update_state(config, state_updates, as_node="review")

            # Resume the graph
            print("\nCompiling briefing...")
            result = graph.invoke(
                Command(resume={"approved": True}),
                config=config,
            )
        else:
            print("\nNo interrupt payload found, compiling as-is...")
            result = graph.invoke(None, config=config)

    # Extract markdown from final state
    final_state = graph.get_state(config)
    markdown = final_state.values.markdown if hasattr(final_state.values, 'markdown') else ""

    if not markdown:
        # Fallback: try result directly
        markdown = result.markdown if hasattr(result, 'markdown') else result.get("markdown", "")

    if markdown:
        _save_briefing(markdown)
    else:
        print("\nError: No markdown output generated.")


if __name__ == "__main__":
    main()

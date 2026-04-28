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
from utils.interrupt_handlers.handlers_registry import INTERRUPT_HANDLERS


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
# Helpers
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


def _get_interrupt_payload(graph_state) -> dict:
    """Extract the interrupt payload from the current graph state."""
    for task in graph_state.tasks:
        if hasattr(task, "interrupts") and task.interrupts:
            return task.interrupts[0].value
    return {}


def _handle_interrupts(graph, config):
    """
    Generic interrupt loop. Checks which node is paused, dispatches to
    the registered handler, applies state updates, and resumes.
    Repeats until the graph reaches END.
    """
    while True:
        state = graph.get_state(config)

        if not state.next:
            break  # graph finished

        paused_at = state.next[0]
        payload = _get_interrupt_payload(state)

        if not payload:
            print(f"\nNo interrupt payload at '{paused_at}', resuming...")
            graph.invoke(Command(resume=None), config=config)
            continue

        handler = INTERRUPT_HANDLERS.get(paused_at)
        if not handler:
            print(f"\nNo handler for interrupt at '{paused_at}', approving as-is...")
            graph.invoke(Command(resume=None), config=config)
            continue

        # Run the handler to get state updates and resume value
        state_updates, resume_value = handler(payload)

        # Apply overrides to graph state if any
        if state_updates:
            graph.update_state(config, state_updates, as_node=paused_at)

        # Resume the graph
        print("\nCompiling briefing...")
        graph.invoke(Command(resume=resume_value), config=config)

    return graph.get_state(config)


# ===========================================================================
# Main
# ===========================================================================

def main():
    auto_mode = "--auto" in sys.argv
    initial_input = {
        "cities": USER_CONFIG["cities"],
        "tickers": USER_CONFIG["tickers"],
        "news_keywords": USER_CONFIG["news_keywords"],
    }

    if auto_mode:
        print("Running in auto mode (no review step)...\n")
        graph = build_graph(checkpointer=None)
        result = graph.invoke(initial_input)
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

    # First invocation — runs until the first interrupt (or END)
    graph.invoke(initial_input, config=config)

    # Handle any interrupts until the graph completes
    final_state = _handle_interrupts(graph, config)

    # Extract and save the briefing
    markdown = ""
    if hasattr(final_state, "values"):
        vals = final_state.values
        markdown = vals.markdown if hasattr(vals, "markdown") else vals.get("markdown", "")

    if markdown:
        _save_briefing(markdown)
    else:
        print("\nError: No markdown output generated.")


if __name__ == "__main__":
    main()

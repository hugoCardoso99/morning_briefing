"""
Interrupt handlers — UI and state-update logic for each human-in-the-loop node.

Each handler receives the interrupt payload and returns a tuple:
    (state_updates: dict, resume_value: Any)

- state_updates: fields to apply via graph.update_state() before resuming.
                  Empty dict means no overrides (approve as-is).
- resume_value:   the value passed to Command(resume=...).
"""

# ---------------------------------------------------------------------------
# Review node handler
# ---------------------------------------------------------------------------

SECTION_ICONS = {
    "weather": "🌍",
    "calendar": "📅",
    "news": "📰",
    "stocks": "📊",
}


def _display_review_ui(payload: dict) -> dict:
    """
    Display the routing plan and collect user input.
    Returns a dict of overrides, or {"approved": True} if no changes.
    """
    print("\n" + "=" * 60)
    print("📋 REVIEW — Here's what the router decided:")
    print("=" * 60)

    sections = payload.get("sections_order", [])
    skipped = payload.get("skipped_sections", [])
    summary = payload.get("section_summary", {})

    # Section details with status indicators
    print("\n  Sections (in order):")
    for i, section in enumerate(sections, 1):
        icon = SECTION_ICONS.get(section, "📄")
        info = summary.get(section, {})
        detail = info.get("detail", "")
        empty = info.get("empty", False)
        status = "⚠ EMPTY" if empty else f"✓ {detail}"
        print(f"    {i}. {icon} {section:<10} — {status}")

    if skipped:
        print(f"\n  Skipped sections:")
        for section in skipped:
            icon = SECTION_ICONS.get(section, "📄")
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


def _build_review_state_updates(user_response: dict, payload: dict) -> dict:
    """
    Convert user overrides from the review UI into graph state updates.
    Returns an empty dict if no overrides are needed.
    """
    if user_response.get("approved", False):
        return {}

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

    return state_updates


def handle_review(payload: dict) -> tuple[dict, any]:
    """
    Full handler for the review interrupt.

    Returns:
        (state_updates, resume_value)
    """
    user_response = _display_review_ui(payload)
    state_updates = _build_review_state_updates(user_response, payload)
    return state_updates, {"approved": True}
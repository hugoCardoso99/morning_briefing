from utils.interrupt_handlers.review_handler import handle_review

# ---------------------------------------------------------------------------
# Handler registry — maps node name to its interrupt handler
# ---------------------------------------------------------------------------

INTERRUPT_HANDLERS = {
    "review": handle_review,
}

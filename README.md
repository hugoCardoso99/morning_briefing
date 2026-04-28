# Morning Briefing Orchestrator

A LangGraph pipeline that combines weather, news, Portuguese holidays, and stock data into a formatted morning briefing.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Edit `USER_CONFIG` in `main.py` to set your cities, tickers, and news keywords, then:

```bash
python main.py          # interactive mode — review before compiling
python main.py --auto   # automatic mode — skip review, compile directly
```

In interactive mode, the pipeline pauses after routing and shows you what it plans to include. You can reorder sections, skip sections, bring back skipped ones, or dismiss alerts before the briefing is compiled.

Output is saved to `output/briefing_YYYY-MM-DD.md`.

## Architecture

```
                ┌─► weather ─────────────────┐
                ├─► news ────────────────────┤
init (context) ─┤                            ├─► router ─► review (HITL) ─► compiler ─► .md
                ├─► calendar ────────────────┤
                └─► stocks ─► finance_news ──┘
```

Parallel fan-out from `init` to four branches. The `stocks → finance_news` chain runs sequentially on its own branch while the other three run independently. All branches converge into the `router` (fan-in), which applies business rules (weekend logic, severe weather promotion, keyword flagging, holiday alerts). The `review` node uses LangGraph's `interrupt()` for human-in-the-loop approval before the `compiler` assembles the final markdown.

Built with LangGraph's `StateGraph`, Pydantic state, and `MemorySaver` checkpointing — no LLMs, just API orchestration with conditional routing and human-in-the-loop.

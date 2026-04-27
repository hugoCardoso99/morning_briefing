# Morning Briefing Orchestrator

A LangGraph pipeline that combines weather, news, Portuguese holidays, and stock data into a formatted morning briefing.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Edit `USER_CONFIG` in `main.py` to set your cities, tickers, and news keywords, then:

```bash
python main.py
```

Output is saved to `output/briefing_YYYY-MM-DD.md`.

## Architecture

```
                ┌─► weather ─────────────────┐
                ├─► news ────────────────────┤
init (context) ─┤                            ├─► router (rules) ─► compiler ─► .md
                ├─► calendar ────────────────┤
                └─► stocks ─► finance_news ──┘
```

Parallel fan-out from `init` to four branches. The `stocks → finance_news` chain runs sequentially on its own branch while the other three run independently. All branches converge into the `router` (fan-in), which applies business rules (weekend logic, severe weather promotion, keyword flagging, holiday alerts), then the `compiler` assembles the final markdown.

Built with LangGraph's `StateGraph` and Pydantic state — no LLMs, just API orchestration with conditional routing.

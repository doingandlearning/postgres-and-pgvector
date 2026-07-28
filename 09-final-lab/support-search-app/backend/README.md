# Support Ticket Search -- Backend

Small Flask app that sits on top of the `09-final-lab/non-python-starter`
capstone data. It does two jobs: serves `../frontend/index.html` as a
static page, and exposes the `/api/*` routes that page calls -- so
there's a single process and a single port, not a backend command and a
separate frontend server. The API pattern itself is the exact same
embed-then-query flow from `embed_text.py`, just wrapped in an HTTP
endpoint instead of printed to the terminal.

## Prerequisites

- The non-python-starter lab's Steps 1-3 already completed: `support_tickets`,
  `customers`, and `knowledge_base` exist and are populated
- `python embed_text.py --bulk` already run, so every row has a real
  bge-m3 embedding (not the placeholder hash function)
- Ollama running locally with `bge-m3` pulled
- Postgres reachable on `localhost:5050` (same as the rest of the course)
- Optional: an `OPENAI_API_KEY` if you want the AI-drafted response
  summary (see below) -- the app works fine without one, it just skips
  that step

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # optional: add OPENAI_API_KEY to enable the AI summary
python app.py
```

Then open `http://localhost:5200` -- that's the whole app, frontend and API together.

## Endpoints

### `GET /api/health`

Returns `{"status": "ok"}` -- the frontend pings this on load so it can
tell you plainly if the backend isn't running, rather than failing
silently on the first search.

### `POST /api/search`

```json
{
  "query": "users can't log in, blank screen after auth",
  "priority": null,
  "category": null,
  "resolved_only": true,
  "limit": 5
}
```

Returns:

```json
{
  "query": "...",
  "results": [
    {
      "ticket_number": "TK-2024-001",
      "issue_description": "...",
      "priority": "high",
      "status": "resolved",
      "resolution_time_hours": 8,
      "satisfaction_score": 4,
      "tags": ["dashboard", "login", "ui"],
      "resolution_steps": ["Clear browser cache", "..."],
      "root_cause": "cached CSS conflict",
      "distance": 0.0421,
      "confidence": "high"
    }
  ],
  "weak_results": [],
  "has_confident_match": true,
  "ai_summary": "Try clearing the browser cache and checking user permissions first (Ticket TK-2024-001) -- that resolved an identical blank-dashboard issue in 8 hours.",
  "ai_summary_note": null
}
```

If nothing clears the `NO_CONFIDENT_MATCH` threshold in `app.py`, `results`
comes back empty and `weak_results` holds what was found instead --
that's the hook the frontend uses to show an honest "nothing confidently
matches this" state instead of quietly presenting a bad match as if it
were a good one (see the RAG UX module: a confident wrong answer erodes
trust faster than an honest miss).

The confidence thresholds (`CONFIDENCE_HIGH`, `CONFIDENCE_MEDIUM`,
`NO_CONFIDENT_MATCH`) are heuristics tuned by eyeballing this small
sample dataset -- with more real tickets, re-check them against the
actual distance distribution rather than trusting the defaults.

### The generation half of RAG

`generate_agent_summary()` in `app.py` is the piece that was missing
before: retrieval alone gets you a list of similar tickets, but an agent
still has to read all of them and synthesize a response. This step
sends the *already-retrieved* tickets (not the whole table) to an LLM
and asks it to draft a short suggested response, grounded only in those
tickets and citing ticket numbers.

Two deliberate constraints, both straight out of the UX module:

- It only ever runs when `has_confident_match` is true. Summarizing a
  weak retrieval would produce a fluent-sounding answer built on a bad
  foundation -- exactly the failure mode worth avoiding.
- The frontend always shows the source tickets alongside the summary,
  never the summary alone, so the agent can verify it rather than
  trusting it blindly.

Without `OPENAI_API_KEY` set, `ai_summary` comes back `null` and
`ai_summary_note` explains why -- the app still returns the ticket
matches themselves, it just skips the drafted response.

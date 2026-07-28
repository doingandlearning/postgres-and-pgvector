"""
app.py -- Support Ticket Search API + frontend server

Serves the frontend/index.html demo that sits on top of the Final Lab
capstone (09-final-lab/non-python-starter). Assumes you've already run
that lab's Steps 1-3 -- support_tickets, customers, and knowledge_base
are populated and every row has a real bge-m3 embedding via
`python embed_text.py --bulk`.

This is deliberately the smallest possible wrapper around the pattern
you've used by hand all week:

    1. embed the query text with Ollama (same call as embed_text.py)
    2. run a hybrid SQL query: vector similarity + WHERE filters
    3. shape the response for the frontend, including a plain-language
       confidence label instead of a raw cosine distance -- see the
       "UX considerations" module: nobody outside this room knows what
       0.31 vs 0.34 means.

This process also serves ../frontend/index.html directly, so there's
only one command to run and one port to visit.

It also does the generation half of RAG, not just retrieval: once a
confident match is found, it asks an LLM to draft a suggested response
for the agent, grounded in those specific tickets (see
generate_agent_summary below). This step is optional -- without an
OPENAI_API_KEY the app still works, it just skips straight to showing
the raw ticket matches, same as before.

Run with:
    pip install -r requirements.txt
    cp .env.example .env   # then add your OPENAI_API_KEY
    python app.py
Then open http://localhost:5200 in a browser.
"""

import json
import os

import psycopg
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

load_dotenv()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050",
}

OLLAMA_URL = "http://localhost:11434/api/embed"
OLLAMA_MODEL = "bge-m3"

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Cosine-distance thresholds used to translate a raw score into a plain-
# language confidence label. These are heuristics, not physics -- tune
# them against your own data if the labels feel wrong once you have more
# than a handful of tickets.
CONFIDENCE_HIGH = 0.35
CONFIDENCE_MEDIUM = 0.55
NO_CONFIDENT_MATCH = 0.75  # beyond this, don't pretend we found something useful

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


def get_embedding(text: str) -> list[float]:
    response = requests.post(
        OLLAMA_URL, json={"model": OLLAMA_MODEL, "input": text}, timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if "embeddings" not in data or not data["embeddings"]:
        raise RuntimeError("Ollama returned no embedding for this query.")
    return data["embeddings"][0]


def confidence_label(distance: float) -> str:
    if distance <= CONFIDENCE_HIGH:
        return "high"
    if distance <= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"


def generate_agent_summary(query_text: str, results: list[dict]) -> tuple[str | None, str | None]:
    """
    Ask an LLM to draft a suggested response, grounded only in the
    tickets we already retrieved. Returns (summary, error) -- exactly one
    will be set. This is deliberately never called for weak/no-confidence
    matches (see the /api/search handler): drafting a fluent-sounding
    summary from a bad retrieval is the exact failure mode the UX module
    warned about -- a confident wrong answer is worse than an honest miss.
    """
    if not OPENAI_API_KEY:
        return None, "AI summary unavailable: set OPENAI_API_KEY in backend/.env to enable it."

    ticket_context = "\n\n".join(
        f"Ticket {r['ticket_number']} ({r['category']}, {r['priority']} priority):\n"
        f"Issue: {r['issue_description']}\n"
        f"Resolution steps: {', '.join(r['resolution_steps']) if r['resolution_steps'] else 'not recorded'}\n"
        f"Root cause: {r['root_cause'] or 'not recorded'}"
        for r in results
    )

    prompt = f"""A support agent is looking at a new issue:
"{query_text}"

Here are the most similar past tickets, already resolved:

{ticket_context}

Write a short suggested response for the agent (3-5 sentences). Only use
information from the tickets above -- do not invent steps that aren't
listed. If the tickets don't fully cover the new issue, say so plainly
rather than guessing. Reference ticket numbers so the agent can verify
the source."""

    try:
        response = requests.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a support-desk assistant. Stay strictly "
                        "within the provided ticket context and cite ticket numbers.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 250,
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content, None
    except requests.exceptions.RequestException as exc:
        return None, f"AI summary failed: {exc}"
    except (KeyError, IndexError):
        return None, "AI summary failed: unexpected response from the LLM."


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    query_text = (data.get("query") or "").strip()

    if not query_text:
        return jsonify({"error": "Provide a 'query' string to search for."}), 400

    priority_filter = data.get("priority") or None
    category_filter = data.get("category") or None
    resolved_only = data.get("resolved_only", True)
    result_limit = int(data.get("limit", 5))

    try:
        query_embedding = get_embedding(query_text)
    except requests.exceptions.ConnectionError:
        return jsonify(
            {
                "error": "Could not reach Ollama at localhost:11434. "
                "Make sure it's running (see PRECOURSE_SETUP.md)."
            }
        ), 503
    except Exception as exc:  # noqa: BLE001 - surface any embedding failure plainly
        return jsonify({"error": f"Embedding failed: {exc}"}), 502

    sql = """
        SELECT
            st.ticket_number,
            st.issue_description,
            st.department,
            st.category,
            st.priority,
            st.status,
            st.resolution_time_hours,
            st.satisfaction_score,
            st.metadata->'tags' AS tags,
            st.metadata->'resolution_steps' AS resolution_steps,
            st.metadata->>'root_cause' AS root_cause,
            (st.metadata->>'affected_users')::int AS affected_users,
            c.customer_name,
            c.subscription_tier,
            st.embedding <=> %(query_vector)s AS distance
        FROM support_tickets st
        JOIN customers c ON st.customer_id = c.id
        WHERE (%(status_filter)s::text IS NULL OR st.status = %(status_filter)s)
          AND (%(priority_filter)s::text IS NULL OR st.priority = %(priority_filter)s)
          AND (%(category_filter)s::text IS NULL OR st.category = %(category_filter)s)
        ORDER BY st.embedding <=> %(query_vector)s
        LIMIT %(result_limit)s;
    """

    params = {
        "query_vector": json.dumps(query_embedding),
        "status_filter": "resolved" if resolved_only else None,
        "priority_filter": priority_filter,
        "category_filter": category_filter,
        "result_limit": result_limit,
    }

    try:
        with psycopg.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc.name for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg.OperationalError as exc:
        return jsonify(
            {"error": f"Could not reach Postgres on port 5050: {exc}"}
        ), 503

    results = []
    for row in rows:
        distance = float(row["distance"])
        results.append(
            {
                "ticket_number": row["ticket_number"],
                "issue_description": row["issue_description"],
                "department": row["department"],
                "category": row["category"],
                "priority": row["priority"],
                "status": row["status"],
                "resolution_time_hours": row["resolution_time_hours"],
                "satisfaction_score": row["satisfaction_score"],
                "tags": row["tags"] or [],
                "resolution_steps": row["resolution_steps"] or [],
                "root_cause": row["root_cause"],
                "affected_users": row["affected_users"],
                "customer_name": row["customer_name"],
                "subscription_tier": row["subscription_tier"],
                "distance": round(distance, 4),
                "confidence": confidence_label(distance),
            }
        )

    best_distance = results[0]["distance"] if results else None
    has_confident_match = best_distance is not None and best_distance <= NO_CONFIDENT_MATCH

    ai_summary = None
    ai_summary_note = None
    if has_confident_match:
        ai_summary, ai_summary_note = generate_agent_summary(query_text, results)

    return jsonify(
        {
            "query": query_text,
            "results": results if has_confident_match else [],
            "weak_results": results if not has_confident_match else [],
            "has_confident_match": has_confident_match,
            "ai_summary": ai_summary,
            "ai_summary_note": ai_summary_note,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5200)

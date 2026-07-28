"""
verify_labs.py

A quick, run-anytime health check for the labs in this course -- distinct
from verify_setup.py, which only checks the *environment* (Python/DB/
Ollama reachability) before the course starts.

This script checks that the things the labs actually build exist and,
where it matters, actually work:

  1. Environment sanity (DB + Ollama reachable, pgvector extension present)
  2. Day 1 core tables: `items` (03/05), `docs` (04 - chunking)
  3. Day 2 capstone (09, non-python-starter track): `support_tickets`,
     `knowledge_base`, `customers` tables exist, ticket embeddings are
     populated, and -- most importantly -- a semantic sanity check that
     proves those embeddings are *real* (bge-m3, meaning-aware) rather
     than the old hashtext()-based placeholder. A hash-based embedding
     would show no reliable difference between a related and an
     unrelated query; a real one should.

Run it any time during the course to confirm a module's data is in a
good state before you rely on it for a demo.

Usage:
    python verify_labs.py
"""

import sys

import psycopg
import requests

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050",
}
OLLAMA_URL = "http://localhost:11434/api/embed"
OLLAMA_MODEL = "bge-m3"


def get_embedding(text: str) -> list[float]:
    response = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "input": text})
    response.raise_for_status()
    data = response.json()
    if not data.get("embeddings"):
        raise RuntimeError(f"No embedding returned for: {text[:50]}...")
    return data["embeddings"][0]


def parse_vector_literal(value) -> list[float]:
    """
    Parse a pgvector column value fetched via psycopg into a list of floats.

    psycopg doesn't know about the `vector` type unless you register
    pgvector's adapter (an extra dependency this course doesn't otherwise
    need), so a fetched embedding column comes back as the raw
    "[0.012,-0.045,...]" text representation rather than a Python list.
    Every other script in this course avoids this entirely by doing
    similarity comparisons inside SQL via `<=>` instead of pulling a
    vector back into Python -- this is the one place we need to parse it
    ourselves.
    """
    if isinstance(value, str):
        return [float(x) for x in value.strip("[]").split(",")]
    return list(value)  # already a sequence of floats


def cosine_distance(a: list[float], b: list[float]) -> float:
    """1 - cosine similarity, so smaller = more similar (matches pgvector's <=>)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1 - (dot / (norm_a * norm_b))


def table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s);",
        (table_name,),
    )
    return cur.fetchone()[0]


def check_environment() -> bool:
    print("--- 1. Environment ---")
    ok = True

    try:
        conn = psycopg.connect(**DB_CONFIG)
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');"
            )
            has_vector = cur.fetchone()[0]
        print("PASS: Connected to Postgres.")
        if has_vector:
            print("PASS: 'vector' extension is enabled.")
        else:
            print("FAIL: 'vector' extension is NOT enabled -- run CREATE EXTENSION vector;")
            ok = False
    except psycopg.OperationalError as e:
        print(f"FAIL: Could not connect to Postgres ({e}). Is `docker compose up -d` running?")
        return False

    try:
        get_embedding("test")
        print(f"PASS: Ollama is running and '{OLLAMA_MODEL}' responded.")
    except requests.exceptions.ConnectionError:
        print(f"FAIL: Could not reach Ollama at {OLLAMA_URL}.")
        ok = False
    except Exception as e:
        print(f"FAIL: Ollama call failed ({e}). Is the '{OLLAMA_MODEL}' model pulled?")
        ok = False

    return ok


def check_day1_tables(cur) -> None:
    print("\n--- 2. Day 1 tables (03/04/05) ---")
    for table in ("items", "docs"):
        if table_exists(cur, table):
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"PASS: '{table}' table exists ({count} row(s)).")
        else:
            print(f"INFO: '{table}' table not found yet -- fine if you haven't run that module's lab.")


def check_capstone(cur) -> None:
    print("\n--- 3. Day 2 capstone (09, non-python-starter) ---")

    required_tables = ["support_tickets", "knowledge_base", "customers"]
    missing = [t for t in required_tables if not table_exists(cur, t)]
    if missing:
        print(f"INFO: {', '.join(missing)} not found yet -- run Steps 1-2 of the workshop first.")
        return

    print("PASS: support_tickets, knowledge_base, and customers tables all exist.")

    cur.execute("SELECT COUNT(*) FROM support_tickets;")
    ticket_count = cur.fetchone()[0]
    if ticket_count == 0:
        print("INFO: support_tickets is empty -- run Step 2 (load sample data) first.")
        return
    print(f"PASS: support_tickets has {ticket_count} row(s).")

    cur.execute("SELECT COUNT(*) FROM support_tickets WHERE embedding IS NULL;")
    missing_embeddings = cur.fetchone()[0]
    if missing_embeddings > 0:
        print(
            f"INFO: {missing_embeddings} ticket(s) still missing an embedding -- "
            "run `python embed_text.py --bulk` in 09-final-lab/non-python-starter/."
        )
        return
    print("PASS: every ticket has an embedding.")

    # --- Semantic sanity check ---
    # This is the important one: it proves the embeddings are real (bge-m3)
    # rather than the old hashtext()-based placeholder. A hash-based
    # "embedding" has no notion of meaning, so an authentication-themed
    # query would be no closer to an authentication ticket than a totally
    # unrelated query would be. A real embedding should show a clear gap.
    print("\n--- 4. Semantic sanity check (real vs. fake embeddings) ---")
    cur.execute(
        "SELECT embedding FROM support_tickets "
        "WHERE issue_description ILIKE %s LIMIT 1;",
        ("%login%",),
    )
    row = cur.fetchone()
    if row is None:
        print("INFO: No login/authentication-themed ticket found to test against -- skipping.")
        return

    login_ticket_embedding = parse_vector_literal(row[0])

    related_query = "I can't log in, my password isn't being accepted"
    unrelated_query = "What's the best way to cook a three-course meal for a dinner party?"

    related_embedding = get_embedding(related_query)
    unrelated_embedding = get_embedding(unrelated_query)

    related_distance = cosine_distance(related_embedding, login_ticket_embedding)
    unrelated_distance = cosine_distance(unrelated_embedding, login_ticket_embedding)

    print(f'Distance from login-related ticket to "{related_query}": {related_distance:.4f}')
    print(f'Distance from login-related ticket to "{unrelated_query}": {unrelated_distance:.4f}')

    if related_distance < unrelated_distance:
        print("PASS: the related query is meaningfully closer -- embeddings are semantically real.")
    else:
        print(
            "FAIL: the unrelated query scored as close (or closer) than the related one. "
            "This would indicate the embeddings aren't semantically meaningful -- "
            "re-run `python embed_text.py --bulk` and check Ollama is using bge-m3."
        )


def main() -> None:
    print("Running lab verification...\n")

    if not check_environment():
        print("\nEnvironment isn't healthy -- fix the above before checking lab data.")
        sys.exit(1)

    conn = psycopg.connect(**DB_CONFIG)
    with conn, conn.cursor() as cur:
        check_day1_tables(cur)
        check_capstone(cur)

    print("\nDone.")


if __name__ == "__main__":
    main()

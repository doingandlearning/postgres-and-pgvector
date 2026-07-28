"""
embed_text.py

No-code helper for the Level 1 SQL Workshop capstone. Generates *real*
embeddings via Ollama's bge-m3 model -- the same model used everywhere
else in this course -- instead of the placeholder hash-based
generate_sample_embedding() SQL function.

Two modes:

  python embed_text.py --bulk
      Embeds every support_tickets.issue_description and every
      knowledge_base (article_title + article_content) row that doesn't
      have an embedding yet. Run this once, right after Step 2 (loading
      the sample data), in place of the old Step 3 SQL function.

  python embed_text.py "some new query text"
      Prints a ready-to-paste SQL vector literal, e.g.
          '[0.0123,-0.0456,...]'::vector(1024)
      Use this whenever a step asks you to search for new text that
      isn't already in the database (Steps 4, 5, 7, 9) -- paste the
      printed literal directly into the SQL in place of the old
      generate_sample_embedding('...') calls.
"""

import json
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


def get_embedding(text: str) -> list[float]:
    """Generate a real embedding for `text` using Ollama's bge-m3 model."""
    response = requests.post(OLLAMA_URL, json={"model": "bge-m3", "input": text})
    response.raise_for_status()
    data = response.json()
    if "embeddings" not in data or not data["embeddings"]:
        raise RuntimeError(f"No embedding returned for: {text[:50]}...")
    return data["embeddings"][0]


def format_as_vector_literal(embedding: list[float]) -> str:
    return "'[" + ",".join(str(x) for x in embedding) + "]'::vector(1024)"


def bulk_embed() -> None:
    """Embed every support_tickets / knowledge_base row missing an embedding."""
    conn = psycopg.connect(**DB_CONFIG)
    with conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, issue_description FROM support_tickets WHERE embedding IS NULL;"
        )
        tickets = cur.fetchall()
        print(f"Embedding {len(tickets)} support ticket(s)...")
        for ticket_id, issue_description in tickets:
            embedding = get_embedding(issue_description)
            cur.execute(
                "UPDATE support_tickets SET embedding = %s WHERE id = %s;",
                (json.dumps(embedding), ticket_id),
            )
            print(f"  done: ticket {ticket_id}")

        cur.execute(
            "SELECT id, article_title, article_content FROM knowledge_base WHERE embedding IS NULL;"
        )
        articles = cur.fetchall()
        print(f"Embedding {len(articles)} knowledge base article(s)...")
        for article_id, title, content in articles:
            embedding = get_embedding(f"{title} {content}")
            cur.execute(
                "UPDATE knowledge_base SET embedding = %s WHERE id = %s;",
                (json.dumps(embedding), article_id),
            )
            print(f"  done: article {article_id}")

    print("\nDone -- every row now has a real embedding.")


def print_query_embedding(text: str) -> None:
    embedding = get_embedding(text)
    print(f'\nReal embedding generated for: "{text}"')
    print("Paste this directly into your SQL wherever the workshop calls")
    print("generate_sample_embedding('...'):\n")
    print(format_as_vector_literal(embedding))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python embed_text.py --bulk        # embed all tickets/articles missing an embedding")
        print('  python embed_text.py "some text"   # get a pasteable vector for a new query')
        sys.exit(1)

    arg = sys.argv[1]
    if arg == "--bulk":
        bulk_embed()
    else:
        print_query_embedding(arg)

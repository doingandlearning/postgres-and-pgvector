import json
import psycopg
from step2 import get_embedding_ollama

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}

OLLAMA_URL = "http://localhost:11434/api/embed"



def search_similar_items(query_embedding, top_n=5):
    """Find similar items in PostgreSQL using vector search."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, embedding <=> %s AS similarity
    FROM items
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results


if __name__ == "__main__":
    # Example usage
    user_query = "Find books related to artificial intelligence"
    query_embedding = get_embedding_ollama(user_query)

    print(f"Generated embedding: {query_embedding[:5]}...")  # Show a preview
    # Perform search
    results = search_similar_items(query_embedding)
    print("\n🔹 Top Similar Books:")
    for name, similarity in results:
        print(f"{name} (Similarity: {similarity:.4f})")
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

def search_filtered_similar_items(query_embedding, genre, top_n=5):
    """Find similar items but filter by a specific genre."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, embedding <=> %s AS similarity
    FROM items
    WHERE item_data->>'subject' = %s
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), genre, json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

if __name__ == "__main__":
  # Example: Find books about 'artificial_intelligence' that are most relevant
  genre = "artificial_intelligence"
  user_query = "What are the best books on artificial intelligence?"
  query_embedding = get_embedding_ollama(user_query)
  filtered_results = search_filtered_similar_items(query_embedding, genre)

  print(f"\n🔹 Top AI Books:")
  for name, similarity in filtered_results:
      print(f"{name} (Similarity: {similarity:.4f})")
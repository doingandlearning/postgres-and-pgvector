import psycopg
import json


from step1 import get_embedding_ollama

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}


def search_filtered_books(query_embedding, subject, top_n=5):
    """Retrieve books related to a specific subject and order by vector similarity."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, item_data, embedding <=> %s AS similarity
    FROM items
    WHERE item_data->>'subject' = %s
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), subject, json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

if __name__ == "__main__":
  user_query = "What are the best books on artificial intelligence?"
  query_embedding = get_embedding_ollama(user_query)
  # Example: Find AI books with best recommendations
  filtered_books = search_filtered_books(query_embedding, "artificial_intelligence")
  print("\n🔹 AI-Specific Book Recommendations:")
  for name, metadata, similarity in filtered_books:
      print(f"{name} (Similarity: {similarity:.4f})")
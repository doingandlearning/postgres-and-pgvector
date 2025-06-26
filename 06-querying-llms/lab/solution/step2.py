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

def search_similar_books(query_embedding, top_n=5):
    """Retrieve books with the most similar vector embeddings."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, item_data, embedding <=> %s AS similarity
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
  # Retrieve relevant books
  user_query = "What are the best books on artificial intelligence?"
  query_embedding = get_embedding_ollama(user_query)
  books = search_similar_books(query_embedding)
  print("\n🔹 Top Recommended Books:")
  for name, metadata, similarity in books:
      print(f"{name} (Similarity: {similarity:.4f})")
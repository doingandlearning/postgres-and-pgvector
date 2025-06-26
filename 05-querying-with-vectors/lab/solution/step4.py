import json
import psycopg
from step3 import search_similar_items

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}

OLLAMA_URL = "http://localhost:11434/api/embed"

def get_random_book_embedding():
    """Retrieve a random book embedding from the database."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, embedding
    FROM items
    ORDER BY random()
    LIMIT 1;
    """

    cursor.execute(sql)
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if result:
        name, embedding = result
        print(f"\n📖 Using '{name}' for similarity search...")
        return name, json.loads(embedding)
    else:
        return None, None

if __name__ == "__main__":
    # Get random book embedding
    book_name, book_embedding = get_random_book_embedding()
    if book_embedding:
        similar_books = search_similar_items(book_embedding)
        print("\n🔹 Recommended Books Similar to", book_name)
        for name, similarity in similar_books:
            print(f"{name} (Similarity: {similarity:.4f})")
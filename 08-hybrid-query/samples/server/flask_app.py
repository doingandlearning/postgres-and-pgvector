from flask import Flask, jsonify, request
import psycopg
import os
import random

app = Flask(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pgvector")

def get_similar_books(query_embedding):
    """Find books similar to the provided embedding."""
    query = """
        SELECT name, embedding <=> %s AS similarity
        FROM items
        ORDER BY embedding <=> %s
        LIMIT 5;
    """
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (query_embedding, query_embedding))
            results = cur.fetchall()
    return [{"name": row[0], "similarity": row[1]} for row in results]

def get_book_embedding(book_title):
    """Retrieve the embedding for a specific book."""
    query = "SELECT embedding FROM items WHERE name = %s;"
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (book_title,))
            result = cur.fetchone()
    return result[0] if result else None

@app.route("/recommend/<book_title>", methods=["GET"])
def recommend_by_title(book_title):
    """Recommend books based on the title."""
    embedding = get_book_embedding(book_title)
    if not embedding:
        return jsonify({"error": "Book not found"}), 404
    recommendations = get_similar_books(embedding)
    return jsonify({"book": book_title, "recommendations": recommendations})

@app.route("/recommend/random", methods=["GET"])
def recommend_random():
    """Recommend books based on a random book."""
    query = "SELECT name, embedding FROM items ORDER BY random() LIMIT 1;"
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
    if not result:
        return jsonify({"error": "No books available"}), 404
    book_title, embedding = result
    recommendations = get_similar_books(embedding)
    return jsonify({"book": book_title, "recommendations": recommendations})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

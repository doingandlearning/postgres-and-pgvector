import ollama
import psycopg
import os
from time import sleep
import json
import requests
import traceback


def get_embedding(text: str):
    response = ollama.embed(model="bge-m3", input=text)
    return response["embeddings"][0]


def load_books_to_db():
    """Load books with embeddings into PostgreSQL."""

    # Wait for the database to be ready
    sleep(5)

    # Connect to the database
    conn = psycopg.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Fetch data from the Open Library
    books = [
        {
            "title": "The Great Gatsby",
            "authors": ["F. Scott Fitzgerald"],
            "fist_publish_year": 1925,
            "subject": "Fiction",
        }
    ]

    for book in books:
        description = (
            f"Book titled '{book['title']}' by {', '.join(book['authors'])}. "
            f"Published in {book['first_publish_year']}. "
            f"This is a book about {book['subject']}."
        )

        # Generate embedding
        # embedding = "[" + ",".join(["0"] * 1536) + "]"        # Placeholder embedding
        embedding = get_embedding(description)  # OpenAI
        cur.execute(
            """
            INSERT INTO items (name, item_data, embedding)
            VALUES (%s, %s, %s)
            """,
            (book["title"], json.dumps(book), embedding),
        )

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    try:
        load_books_to_db()
        print("Successfully loaded sample books!")

    except Exception as e:
        traceback.print_exc()
        print(f"Error loading books: {e}")

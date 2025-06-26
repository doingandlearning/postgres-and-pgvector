import ollama
import psycopg
import os
from time import sleep
import json
import requests
import traceback

def get_embedding(text: str):
  response = ollama.embed(
    model="bge-m3",
    input=text
  )
  return response["embeddings"][0]

def fetch_books():
    """Fetch books across various subjects from Open Library."""
    categories = [
        "programming",
        "web_development",
        "artificial_intelligence",
        "computer_science",
        "software_engineering",
    ]
    all_books = []

    for category in categories:
        url = f"https://openlibrary.org/subjects/{category}.json?limit=10"
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for a bad response

        data = response.json()
        books = data.get("works", [])

        # Format each book
        for book in books:
            book_data = {
                "title": book.get("title", "Untitled"),
                "authors": [
                    author.get("name", "Unknown Author")
                    for author in book.get("authors", [])
                ],
                "first_publish_year": book.get("first_publish_year", "Unknown"),
                "subject": category,
            }
            all_books.append(book_data)

        print(f"Successfully processed {len(books)} books for {category}")

    if not all_books:
        print("No books were fetched from any category.")

    return all_books


def load_books_to_db():
    """Load books with embeddings into PostgreSQL."""

    # Wait for the database to be ready
    sleep(5)

    # Connect to the database
    conn = psycopg.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Fetch data from the Open Library
    books = fetch_books()

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

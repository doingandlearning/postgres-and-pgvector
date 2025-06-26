import psycopg
import json
import requests
import traceback

OLLAMA_URL = "http://localhost:11434/api/embed"

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050",
}


def get_embedding(text: str):
    """Fetch embedding from the Ollama API."""
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"model": "bge-m3", "input": text}
        response = requests.post(OLLAMA_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["embeddings"][0]
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return None  # Return None if embedding fails


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
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            books = data.get("works", [])

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

            print(f"Fetched {len(books)} books from {category}")
        except requests.RequestException as e:
            print(f"Failed to fetch books for category {category}: {e}")

    return all_books


def load_books_to_db():
    """Load books with embeddings into PostgreSQL using batch execution."""
    books = fetch_books()
    if not books:
        print("No books to load.")
        return

    # Prepare data for batch insert
    records = []
    for book in books:
        description = (
            f"Book titled '{book['title']}' by {', '.join(book['authors'])}. "
            f"Published in {book['first_publish_year']}. "
            f"This is a book about {book['subject']}."
        )

        embedding = get_embedding(description) or [0] * 1024  # Fallback to zero vector
        records.append((book["title"], json.dumps(book), embedding))

    if not records:
        print("No records to insert.")
        return

    # Insert into the database
    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO items (name, item_data, embedding)
                    VALUES (%s, %s, %s)
                    """,
                    records,
                )
            conn.commit()
        print(f"Successfully inserted {len(records)} books into the database.")
    except Exception as e:
        print(f"Database error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        load_books_to_db()
    except Exception as e:
        traceback.print_exc()
        print(f"Error loading books: {e}")

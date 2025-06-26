import ollama
import psycopg
import os
from time import sleep
import json
import requests
import traceback
import csv

output_dir = os.getenv("OUTPUT_DIR", "/app/data")
output_file = os.path.join(output_dir, "books.csv")


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



def export_to_csv():
    """Export books with embeddings from PostgreSQL to a CSV file."""
    try:
        # Wait for the database to be ready
        sleep(5)

        # Connect to the database
        conn = psycopg.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        # Fetch all rows from the items table
        cur.execute("SELECT name, item_data, embedding FROM items")
        books = cur.fetchall()

        # Write data to a CSV file
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow(["Name", "Item Data", "Embedding"])
            
            # Write book data rows
            for book in books:
                writer.writerow([book[0], book[1], book[2]])

        print("Books exported successfully to books.csv")

    except Exception as e:
        traceback.print_exc()
        print(f"Error exporting books: {e}")

    finally:
        # Ensure the connection is closed
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    try:
        export_to_csv()
        print("Successfully loaded sample books!")

    except Exception as e:
        traceback.print_exc()
        print(f"Error loading books: {e}")

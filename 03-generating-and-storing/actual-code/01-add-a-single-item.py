import requests
import psycopg
import json
# pip install -r requirements.txt

DB_CONFIG = {
  "dbname": "pgvector",
  "user": "postgres",
  "password": "postgres",
  "host": "localhost",
  "port": "5050"
}



def get_embedding(text):
  data = {
    "model": "bge-m3",
    "input": text
  }

  response = requests.post("http://localhost:11434/api/embed",
                  json=data)
  response.raise_for_status()  # 200 is fine, 404, 500, ... 
  data = response.json()
  embedding = data['embeddings'][0]
  return embedding


def add_books_to_db():
  conn = psycopg.connect(**DB_CONFIG)
  cur = conn.cursor()

  books = [
    {"title": "The Lake of Darkness", "authors": ["Adam Roberts"], "first_publish_year": 2024, "subject": "fiction"}
  ]

  for book in books:
    description = f"Book titled {book["title"]} by {", ".join(book["authors"])} First published in {book["first_publish_year"]}. This is a book about {book["subject"]}"
    embedding = get_embedding(description)

    cur.execute(
      """
      INSERT INTO items (name, item_data, embedding) 
      VALUES (%s, %s, %s)
      """,
      (book["title"], 
      json.dumps(book),
      embedding)
    )
  conn.commit()
  cur.close()
  conn.close()

add_books_to_db()
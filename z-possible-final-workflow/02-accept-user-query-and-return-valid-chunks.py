import sys
from utils import get_db_connection, get_embedding

def get_user_input():
  return input("Enter your query: ")

def fetch_similar_chunks(user_embedding, top_k=5, threshold=0.6):
  # Query the docs table as per schema.sql
  query = """
    SELECT id, text, embedding <=> %s::vector AS distance, page
    FROM docs
    ORDER BY embedding <=> %s::vector
    LIMIT %s 
    WHERE metadata->chunk_length > 10
    AND distance < %s;
  """
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute(query, (user_embedding, user_embedding, top_k, threshold))
      results = cur.fetchall()
  return results

def main():
  user_query = get_user_input()
  user_embedding = get_embedding(user_query)
  similar_chunks = fetch_similar_chunks(user_embedding, 1)
  print("Most similar chunks:")
  for chunk in similar_chunks:
    print(f"ID: {chunk[0]}, Distance: {chunk[2]:.4f}\nContent: {chunk[1]}\n On page: {chunk[3]}")

if __name__ == "__main__":
  main()
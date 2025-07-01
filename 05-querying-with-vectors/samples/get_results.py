from utils import get_db_connection, get_embedding

# 1. Get a query from the user
query = input("Enter your query: ")

# 2. Get the embedding for the query
embedding = get_embedding(query)
if embedding is None:
    print("Error generating embedding for the query.")
    exit()

def find_similar_items(embedding):
    """
    Finds items in the database that are similar to the given embedding.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Use a simple cosine similarity query
            cur.execute(
                """
                SELECT name, embedding <=> %s::vector AS similarity
                FROM items
                ORDER BY embedding <=> %s::vector
                LIMIT 5;
                """,
                (embedding, embedding)
            )
            results = cur.fetchall()
            return results

for result in find_similar_items(embedding):
    name, similarity = result
    print(f"Item: {name}, Similarity: {similarity:.4f}")
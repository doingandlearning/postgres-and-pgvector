import psycopg
from utils import get_db_connection, get_embedding

# --- Main execution ---
query_text = "What is the name of Alice's sister?"

try:
    conn = get_db_connection()
except psycopg.OperationalError as e:
    print(f"Could not connect to the database: {e}")
    exit()

with conn, conn.cursor() as cur:
    # Generate an embedding for the query_text.
    query_embedding = get_embedding(query_text)
    
    # Find the most similar document chunk using L2 distance.
    cur.execute(
        "SELECT text, page FROM docs ORDER BY embedding <-> %s::vector LIMIT 1",
        (query_embedding,),
    )
    result = cur.fetchone()

    if result:
        text, page_num = result
        print("--- Most similar chunk ---")
        print(text)
        print(f"\n(found on page {page_num})")
    else:
        print("No result found.")

print("Done.") 
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
    # TODO: Generate an embedding for the query_text using get_embedding().
    query_embedding = [] # Replace this
    
    # TODO: Write a SQL query to find the most similar document chunk.
    # - Use the L2 distance operator (`<->`) for similarity.
    # - `ORDER BY` the distance and `LIMIT 1` to get the top result.
    # - `SELECT` the `text` and `page` of the most similar chunk.
    
    # cur.execute("YOUR SQL QUERY HERE", (query_embedding,))
    # result = cur.fetchone()

    # if result:
    #     text, page_num = result
    #     print("--- Most similar chunk ---")
    #     print(text)
    #     print(f"\n(found on page {page_num})")
    # else:
    #     print("No result found.")
    pass # Replace this

print("Done.") 
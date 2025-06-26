import psycopg
import requests
import json

# Database configuration
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",  # Change if using Docker, e.g., "db"
    "port": "5050"
}

# Ollama API for embeddings
OLLAMA_URL = "http://localhost:11434/api/embed"

def get_embedding_ollama(text):
    """Generate an embedding using Ollama's bge-m3 model."""
    payload = {"model": "bge-m3", "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data["embeddings"][0]
    else:
        raise Exception(f"Error fetching embedding: {response.text}")

def find_similar_tickets(user_issue, top_n=5):
    """Retrieve the most relevant past tickets using vector similarity search."""
    query_embedding = get_embedding_ollama(user_issue)

    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT id, issue_description, metadata->>'resolution_steps' AS resolution_steps
    FROM support_tickets
    ORDER BY embedding <=> %s  -- Cosine similarity
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        return "No relevant tickets found."

    tickets = [
        {
            "id": row[0],
            "issue_description": row[1],
            "resolution_steps": row[2] if row[2] else "No resolution provided."
        }
        for row in results
    ]

    return tickets

# Example user query
if __name__ == "__main__":
    user_query = "User cannot log in due to authentication failure."
    tickets = find_similar_tickets(user_query)
    print(json.dumps(tickets, indent=2))

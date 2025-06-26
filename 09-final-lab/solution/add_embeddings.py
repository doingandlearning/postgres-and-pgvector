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

# Ollama API Configuration
OLLAMA_URL = "http://localhost:11434/api/embed"

def get_embedding_ollama(text):
    """Generate an embedding using Ollama's bge-m3 model."""
    payload = {"model": "bge-m3", "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data["embeddings"][0]
    else:
        raise Exception(f"Error fetching embedding: {response.text}")

def generate_embeddings_for_tickets():
    """Fetch tickets without embeddings, generate embeddings, and update the database."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Fetch tickets missing embeddings
    cursor.execute("SELECT id, issue_description FROM support_tickets WHERE embedding IS NULL;")
    tickets = cursor.fetchall()

    if not tickets:
        print("✅ All tickets already have embeddings.")
        return

    print(f"🎯 Found {len(tickets)} tickets to process.")

    # Generate embeddings and update database
    update_sql = "UPDATE support_tickets SET embedding = %s WHERE id = %s;"

    for ticket_id, issue_description in tickets:
        try:
            embedding = get_embedding_ollama(issue_description)
            cursor.execute(update_sql, (json.dumps(embedding), ticket_id))
            print(f"✅ Updated ticket {ticket_id} with embedding.")
        except Exception as e:
            print(f"❌ Error processing ticket {ticket_id}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("🚀 Embeddings updated successfully!")

# Run the script
if __name__ == "__main__":
    generate_embeddings_for_tickets()
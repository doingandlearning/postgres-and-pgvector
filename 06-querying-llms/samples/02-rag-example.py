import requests
import psycopg2
from psycopg2.extras import Json
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection config
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050",  # Updated to match your exposed port
}

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

def query_items(user_query, top_n=5):
    """Retrieve the most relevant items using vector similarity from pgvector."""
    try:
        # Generate query embedding using Ollama
        query_embedding = get_embedding_ollama(user_query)
        print(query_embedding)
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # SQL Query: Find items using cosine similarity
        sql = """
        SELECT name, item_data
        FROM items
        ORDER BY embedding <=> %s  -- Cosine similarity search
        LIMIT %s;
        """

        cursor.execute(sql, (Json(query_embedding), top_n))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if not results:
            return "No relevant items found."

        items = [
            {
                "name": row[0],  # Item name
                "item_data": row[1]  # JSONB data
            }
            for row in results
        ]

        return items

    except Exception as e:
        return f"Database query failed: {str(e)}"



# OpenAI API Key (Replace with your actual key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI API Endpoint
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Headers for OpenAI API
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def enhance_with_openai(books):
    """Send retrieved book data to OpenAI LLM for enhancement."""
    
    if not books or isinstance(books, str):
        return f"LLM skipped: {books}"

    # Format book data as a readable list
    book_text = "\n".join(
        [
            f"- {book['name']} (Metadata: {json.dumps(book['item_data'], indent=2)})"
            for book in books
        ]
    )

    # OpenAI prompt
    prompt = f"""
    Here are some books on programming:
    {book_text}

    Summarize this list and recommend the best ones for a beginner, intermediate, and advanced programmer.
    """

    # Payload for OpenAI request
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are an expert in programming books."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    # Send request to OpenAI API
    response = requests.post(OPENAI_URL, headers=HEADERS, data=json.dumps(payload))

    # Parse response
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"

# Example user query
items = query_items("tell me about all the books on programming you have available")
print(items)

enhanced_response = enhance_with_openai(items)
print(enhanced_response)

import requests
import psycopg
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
        conn = psycopg.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # SQL Query: Find items using cosine similarity
        sql = """
        SELECT name, item_data
        FROM items
        ORDER BY embedding <=> %s::vector  -- Cosine similarity search
        LIMIT %s;
        """

        cursor.execute(sql, (query_embedding, top_n))
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

def enhance_with_openai(books, user_query=None):
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

    print(book_text)

    # OpenAI prompt - prompt engineering is a practice of crafting effective prompts
    # to get the best results from LLMs. Here we ask the model to summarize
    # the list of books and recommend the best ones for different skill levels.
    # This is a simple example of prompt engineering.
    # You can modify the prompt to suit your needs.
    prompt = f"""
    Here are some books on programming, do not suggest any books that are not in the list:
    <book-list>
    {book_text}
    </book-list>

    Based on the following user query: "{user_query if user_query else 'No specific query provided'}",
    please summarize the list of books and recommend the best ones for a beginner, intermediate, and
    advanced programmer. Provide a brief explanation for each recommendation.
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

def use_openai_to_decide_on_response_quality(response, user_query=None):
    """Use OpenAI to decide if the response is good enough."""
    # This function can be used to send the response to OpenAI and get feedback
    # on whether the response is good enough or not.
    # Generate the query embedding using openai
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are an expert in evaluating responses. You will determine if the response is good enough based on the user's query."},
            {"role": "user", "content": f"Is the following response good enough? {response} based on {user_query} Return with 'yes' or 'no' and nothing else."}
        ],
        "temperature": 0.5,
        "max_tokens": 50
    }

    response = requests.post(OPENAI_URL, headers=HEADERS, data=json.dumps(payload))
    if response.status_code == 200:
        return True if response.json()["choices"][0]["message"]["content"].strip().lower() == "yes" else False
    else:
        return f"Error: {response.status_code}, {response.text}"

# Example user query
user_query = input("Ask a question about programming books: ")
items = query_items(user_query)
print(items)

enhanced_response = enhance_with_openai(items, user_query)
if not use_openai_to_decide_on_response_quality(enhanced_response):
    print("The response is not good enough. Please try again.")
else:
    print(enhanced_response)

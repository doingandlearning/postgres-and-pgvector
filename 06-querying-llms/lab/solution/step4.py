import requests
import json
import os
from step1 import get_embedding_ollama
from step2 import search_similar_books
from step3 import format_books_for_prompt
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def query_llm(prompt):
    """Query OpenAI's LLM with retrieved book data."""
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are an AI assistant helping a user find books."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"


if __name__ == "__main__":
      # Retrieve relevant books
  user_query = "What are the best books on artificial intelligence?"
  query_embedding = get_embedding_ollama(user_query)
  books = search_similar_books(query_embedding)
  # Generate structured prompt
  structured_prompt = format_books_for_prompt(books)
  # Query LLM
  llm_response = query_llm(structured_prompt)
  print("\n🔹 LLM Response:")
  print(llm_response)
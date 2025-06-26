import requests
import json

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

if __name__ == "__main__":
  user_query = "What are the best books on artificial intelligence?"
  query_embedding = get_embedding_ollama(user_query)
  print(f"Generated embedding: {query_embedding[:5]}...")  # Preview
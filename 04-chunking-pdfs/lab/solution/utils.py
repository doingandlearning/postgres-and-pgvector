import psycopg
import requests

OLLAMA_URL = "http://localhost:11434/api/embed"
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5050,
}

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg.connect(**DB_CONFIG)

def get_embedding(text: str, model: str = "all-minilm") -> list[float]:
    """
    Generates an embedding for the given text using a local Ollama model.
    The default model is 'all-minilm' which has 384 dimensions.
    """
    try:
        response = requests.post(OLLAMA_URL, json={"model": "bge-m3", "input": text})

        response.raise_for_status()
        data = response.json()
        return data.get("embeddings")[0]
    except requests.exceptions.RequestException as e:
        print(f"Error getting embedding from Ollama: {e}")
        # Return a zero vector as a fallback
        return [0.0] * 1024
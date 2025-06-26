import nltk
import json
import requests
import psycopg
from nltk.tokenize import sent_tokenize

# Download NLTK tokenizer if not already present
nltk.download("punkt")

# Ollama API URL for embeddings
OLLAMA_URL = "http://localhost:11434/api/embed"

# PostgreSQL Configuration
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050",
}


def chunk_text(text, chunk_size=512, overlap=128):
    """
    Split text into overlapping chunks for embedding.
    Uses sentence tokenization and ensures overlap between chunks.
    """
    sentences = sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence.split())

        if current_length + sentence_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:]  # Retain overlap
            current_length = sum(len(sent.split()) for sent in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def get_embedding(text):
    """Generate an embedding using Ollama's bge-m3 model."""
    try:
        payload = {"model": "bge-m3", "input": text}
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("embeddings", [None])[0]
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return [0] * 1024  # Fallback zero vector


def store_chunks(doc_id, chunks, embeddings):
    """Insert chunked text and embeddings into PostgreSQL (pgvector)."""
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO documents (doc_id, chunk_id, content, embedding)
            VALUES (%s, %s, %s, %s);
            """

            records = [
                (doc_id, i, chunk, json.dumps(embedding))
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]

            cur.executemany(sql, records)
            conn.commit()

    print(f"✅ Stored {len(chunks)} chunks for document: {doc_id}")


if __name__ == "__main__":
    # Example Text (Replace with actual document text)
    text = """Deep Learning is a subfield of machine learning concerned with neural networks...
              The most popular architectures include Transformers, CNNs, and RNNs.
              These methods have transformed NLP, CV, and AI research."""

    # Step 1: Chunk Text
    chunks = chunk_text(text)
    print(f"✅ Generated {len(chunks)} chunks.")

    # Step 2: Generate Embeddings
    chunk_embeddings = [get_embedding(chunk) for chunk in chunks]
    print(f"✅ Generated {len(chunk_embeddings)} embeddings.")

    # Step 3: Store in PostgreSQL
    store_chunks("deep-learning-guide", chunks, chunk_embeddings)

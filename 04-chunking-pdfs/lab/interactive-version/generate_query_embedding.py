#!/usr/bin/env python3
"""
Helper script to generate embeddings for queries
Usage: python generate_query_embedding.py "Your question here"
"""

import sys
import json
import requests

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json not found!")
        sys.exit(1)

def get_embedding(text, embedding_config):
    """Generate embedding using Ollama"""
    try:
        payload = {"model": embedding_config['model'], "input": text}
        response = requests.post(embedding_config['ollama_url'], json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data["embeddings"][0]
        else:
            raise Exception(f"Ollama API error: {response.text}")
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        print("Make sure Ollama is running and the model is downloaded!")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_query_embedding.py \"Your question here\"")
        print("Example: python generate_query_embedding.py \"What is Alice's sister's name?\"")
        sys.exit(1)
    
    query_text = sys.argv[1]
    print(f"🔍 Generating embedding for: {query_text}")
    
    # Load configuration
    config = load_config()
    
    # Generate embedding
    embedding = get_embedding(query_text, config['embedding'])
    
    # Format for SQL
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    
    print("\n✅ Embedding generated!")
    print("📋 Copy this embedding for your SQL query:")
    print("=" * 50)
    print(embedding_str)
    print("=" * 50)
    
    print("\n📝 Complete SQL query template:")
    print("=" * 50)
    print("SELECT ")
    print("  text,")
    print("  page,")
    print(f"  embedding <=> '{embedding_str}' as similarity")
    print("FROM docs ")
    print(f"WHERE pdf_id = '{config['pdf_id']}'")
    print("ORDER BY similarity ASC ")
    print("LIMIT 3;")
    print("=" * 50)
    
    print("\nTo run this query:")
    print("1. Connect to your database:")
    print("   docker exec -it pgvector-db psql -U postgres -d pgvector")
    print("2. Copy and paste the SQL query above")

if __name__ == "__main__":
    main() 
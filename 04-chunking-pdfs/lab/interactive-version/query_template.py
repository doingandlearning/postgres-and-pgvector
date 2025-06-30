#!/usr/bin/env python3
"""
Template-based query script
Fill in the blanks marked with # TODO: FILL IN
"""

import psycopg
import requests
import json

# TODO: FILL IN - Database connection details
DB_CONFIG = {
    "host": "localhost",        # TODO: FILL IN - Database host
    "port": "5050",            # TODO: FILL IN - Database port  
    "dbname": "pgvector",      # TODO: FILL IN - Database name
    "user": "postgres",        # TODO: FILL IN - Database user
    "password": "postgres"     # TODO: FILL IN - Database password
}

# TODO: FILL IN - Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/embed"  # TODO: FILL IN - Ollama URL
EMBEDDING_MODEL = "bge-m3"                       # TODO: FILL IN - Model name

# TODO: FILL IN - Query parameters
QUERY_TEXT = "What is the name of Alice's sister?"  # TODO: FILL IN - Your question
PDF_ID = "alice_in_wonderland"                      # TODO: FILL IN - PDF ID to search
LIMIT = 3                                           # TODO: FILL IN - Number of results

def get_db_connection():
    """Create database connection"""
    return psycopg.connect(**DB_CONFIG)

def get_embedding(text):
    """Generate embedding using Ollama"""
    payload = {"model": EMBEDDING_MODEL, "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data["embeddings"][0]
    else:
        raise Exception(f"Embedding error: {response.text}")

def search_similar_text(query_text, pdf_id, limit=3):
    """Search for text similar to the query"""
    
    print(f"🔍 Searching for: {query_text}")
    
    # TODO: FILL IN - Generate embedding for the query
    query_embedding = get_embedding(query_text)
    print("✅ Query embedding generated")
    
    # Connect to database
    conn = get_db_connection()
    print("✅ Database connected")
    
    # TODO: FILL IN - Execute similarity search
    with conn.cursor() as cur:
        sql = """
        SELECT 
            text,
            page,
            embedding <=> %s as similarity
        FROM docs 
        WHERE pdf_id = %s
        ORDER BY similarity ASC 
        LIMIT %s;
        """
        
        cur.execute(sql, (query_embedding, pdf_id, limit))
        results = cur.fetchall()
    
    conn.close()
    return results

def display_results(results, query_text):
    """Display search results in a readable format"""
    
    print(f"\n📊 Search Results for: '{query_text}'")
    print("=" * 60)
    
    if not results:
        print("❌ No results found")
        return
    
    for i, (text, page, similarity) in enumerate(results, 1):
        print(f"\n🔍 Result {i} (Similarity: {similarity:.4f})")
        print(f"📄 Found on page: {page}")
        print(f"📝 Text: {text[:200]}...")  # Show first 200 characters
        print("-" * 40)
    
    # TODO: FILL IN - Analyze the best result
    best_result = results[0]
    best_text, best_page, best_similarity = best_result
    
    print(f"\n🎯 Best Match (Similarity: {best_similarity:.4f}):")
    print(f"📄 Page: {best_page}")
    print(f"📝 Full Text: {best_text}")

def main():
    print("🚀 Starting similarity search...")
    
    try:
        # TODO: FILL IN - Perform the search
        results = search_similar_text(QUERY_TEXT, PDF_ID, LIMIT)
        
        # TODO: FILL IN - Display the results
        display_results(results, QUERY_TEXT)
        
        print("\n✅ Search complete!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        print("Make sure:")
        print("- Docker containers are running")
        print("- Ollama model is downloaded")
        print("- PDF has been ingested into the database")

if __name__ == "__main__":
    main() 
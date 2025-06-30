#!/usr/bin/env python3
"""
Generate search embeddings and SQL queries
Usage: python generate_search_embedding.py "your search query here"
"""

import sys
import json
import requests

def load_config():
    """Load configuration from search_config.json"""
    try:
        with open('search_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Use default configuration
        return {
            "embedding": {
                "model": "bge-m3",
                "ollama_url": "http://localhost:11434/api/embed"
            }
        }

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

def format_embedding_for_sql(embedding):
    """Format embedding as SQL array literal"""
    return '[' + ','.join(map(str, embedding)) + ']'

def generate_sql_queries(query_text, embedding_str):
    """Generate various SQL queries for the search"""
    
    queries = {
        "basic_similarity": f"""
-- Basic similarity search for: "{query_text}"
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> '{embedding_str}')::numeric, 4) as similarity_score
FROM items
ORDER BY similarity_score ASC
LIMIT 5;""",

        "with_threshold": f"""
-- Similarity search with threshold for: "{query_text}"
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> '{embedding_str}')::numeric, 4) as similarity_score
FROM items
WHERE embedding <=> '{embedding_str}' < 0.7  -- Adjust threshold as needed
ORDER BY similarity_score ASC
LIMIT 10;""",

        "filtered_by_subject": f"""
-- Subject-filtered similarity search for: "{query_text}"
-- Replace 'SUBJECT_HERE' with your desired subject (ai, programming, web_development)
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> '{embedding_str}')::numeric, 4) as similarity_score
FROM items
WHERE item_data->>'subject' = 'SUBJECT_HERE'
ORDER BY similarity_score ASC
LIMIT 5;""",

        "compare_metrics": f"""
-- Compare different distance metrics for: "{query_text}"
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> '{embedding_str}')::numeric, 4) as cosine_similarity,
  ROUND((embedding <-> '{embedding_str}')::numeric, 4) as euclidean_distance,
  ROUND((embedding <#> '{embedding_str}')::numeric, 4) as inner_product
FROM items
ORDER BY cosine_similarity ASC
LIMIT 5;""",

        "hybrid_search": f"""
-- Hybrid search (text + vector) for: "{query_text}"
WITH text_matches AS (
  SELECT *, 2.0 as text_boost
  FROM items
  WHERE name ILIKE '%{query_text.split()[0] if query_text.split() else query_text}%'
),
vector_matches AS (
  SELECT 
    *,
    embedding <=> '{embedding_str}' as similarity,
    1.0 as vector_boost
  FROM items
  WHERE embedding <=> '{embedding_str}' < 0.8
)
SELECT 
  COALESCE(tm.name, vm.name) as name,
  COALESCE(tm.item_data->>'subject', vm.item_data->>'subject') as subject,
  COALESCE(tm.text_boost, 0) + COALESCE(vm.vector_boost, 0) as combined_score,
  vm.similarity
FROM text_matches tm
FULL OUTER JOIN vector_matches vm ON tm.name = vm.name
ORDER BY combined_score DESC, vm.similarity ASC
LIMIT 10;"""
    }
    
    return queries

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_search_embedding.py \"your search query here\"")
        print("Example: python generate_search_embedding.py \"artificial intelligence machine learning\"")
        sys.exit(1)
    
    query_text = sys.argv[1]
    print(f"🔍 Generating search embedding for: {query_text}")
    
    # Load configuration
    config = load_config()
    
    # Generate embedding
    embedding = get_embedding(query_text, config['embedding'])
    embedding_str = format_embedding_for_sql(embedding)
    
    print("✅ Embedding generated successfully!")
    print(f"📊 Embedding dimensions: {len(embedding)}")
    
    # Generate SQL queries
    queries = generate_sql_queries(query_text, embedding_str)
    
    print("\n" + "="*80)
    print("📝 READY-TO-USE SQL QUERIES")
    print("="*80)
    
    print("\n🔸 1. BASIC SIMILARITY SEARCH")
    print("-" * 40)
    print(queries["basic_similarity"])
    
    print("\n🔸 2. WITH SIMILARITY THRESHOLD")
    print("-" * 40)
    print(queries["with_threshold"])
    
    print("\n🔸 3. FILTERED BY SUBJECT")
    print("-" * 40)
    print(queries["filtered_by_subject"])
    
    print("\n🔸 4. COMPARE DISTANCE METRICS")
    print("-" * 40)
    print(queries["compare_metrics"])
    
    print("\n🔸 5. HYBRID SEARCH (TEXT + VECTOR)")
    print("-" * 40)
    print(queries["hybrid_search"])
    
    print("\n" + "="*80)
    print("🎯 HOW TO USE THESE QUERIES")
    print("="*80)
    print("1. Connect to your database:")
    print("   docker exec -it pgvector-db psql -U postgres -d pgvector")
    print("\n2. Copy and paste any of the queries above")
    print("\n3. For filtered searches, replace 'SUBJECT_HERE' with:")
    print("   - 'ai' for AI/ML books")
    print("   - 'programming' for programming books") 
    print("   - 'web_development' for web development books")
    print("\n4. Adjust similarity thresholds based on your needs:")
    print("   - Lower values (0.3-0.5): More strict, fewer results")
    print("   - Higher values (0.7-0.9): More permissive, more results")
    
    print(f"\n💾 Raw embedding (for advanced use):")
    print("=" * 50)
    print(embedding_str[:100] + "..." if len(embedding_str) > 100 else embedding_str)

if __name__ == "__main__":
    main() 
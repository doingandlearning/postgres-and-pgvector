# Lab: Querying with Vectors (Non-Python Starter)

## Objective
This lab focuses on understanding **vector similarity search concepts** without requiring extensive Python programming. You'll learn how to find similar content using different approaches and understand the core principles behind semantic search.

## Learning Goals
- Understand different similarity measures (cosine, euclidean, inner product)
- Learn how to perform vector searches with SQL
- Experiment with different search parameters and filters
- See how vector search compares to traditional text search
- Build intuition for when vector search works well vs poorly

## Prerequisites

Make sure you have data loaded in your database. If not, run one of these first:
```bash
# Option 1: From previous lab
cd ../../../03-generating-and-storing/lab/non-python-starter
python load_configured.py

# Option 2: Quick sample data
cd ../../../03-generating-and-storing/lab/non-python-starter  
python load_sample_data.py
```

## Approach Options

### Option A: SQL-Focused Exploration (Recommended for Non-Python Users)

Use SQL queries to understand vector similarity concepts directly.

#### Step 1: Basic Similarity Search
```sql
-- Connect to your database first
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- Find books similar to a specific book
SELECT 
  name,
  item_data->>'subject' as subject,
  embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE name LIKE '%Python%' 
    LIMIT 1
  ) as similarity_score
FROM items
ORDER BY similarity_score ASC
LIMIT 5;
```

#### Step 2: Compare Similarity Measures
```sql
-- Compare different distance metrics for the same query
WITH target_book AS (
  SELECT embedding FROM items WHERE name LIKE '%Machine Learning%' LIMIT 1
)
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (SELECT embedding FROM target_book))::numeric, 4) as cosine_similarity,
  ROUND((embedding <-> (SELECT embedding FROM target_book))::numeric, 4) as euclidean_distance,
  ROUND((embedding <#> (SELECT embedding FROM target_book))::numeric, 4) as inner_product
FROM items
ORDER BY cosine_similarity ASC
LIMIT 5;
```

### Option B: Interactive Query Builder

Use a helper script that generates embeddings and builds SQL queries for you.

#### Step 1: Generate Query Embeddings
```bash
python generate_search_embedding.py "artificial intelligence and machine learning"
```

This outputs a ready-to-use SQL query.

#### Step 2: Run Custom Searches
```bash
python search_assistant.py --query "web development frameworks" --limit 5 --subject programming
```

### Option C: Configuration-Based Search

Use JSON configuration to define different search scenarios.

#### Step 1: Configure Search Scenarios
**Edit `search_config.json`:**
```json
{
  "searches": [
    {
      "name": "AI Books Search",
      "query": "artificial intelligence and machine learning",
      "filter_subject": "ai",
      "limit": 5,
      "similarity_threshold": 0.7
    },
    {
      "name": "Programming Recommendations",
      "query": "python programming best practices",
      "filter_subject": null,
      "limit": 10,
      "similarity_threshold": 0.8
    }
  ]
}
```

#### Step 2: Run Configured Searches
```bash
python run_search_scenarios.py
```

## Learning Experiments

### Experiment 1: Understanding Similarity Scores
```sql
-- Find the range of similarity scores
SELECT 
  MIN(embedding <=> (SELECT embedding FROM items LIMIT 1)) as min_similarity,
  MAX(embedding <=> (SELECT embedding FROM items LIMIT 1)) as max_similarity,
  AVG(embedding <=> (SELECT embedding FROM items LIMIT 1)) as avg_similarity
FROM items;
```

**Question**: What do these scores tell you about your data distribution?

### Experiment 2: Subject-Based Clustering
```sql
-- See how well subjects cluster together
WITH ai_center AS (
  SELECT AVG(embedding) as center_embedding
  FROM items 
  WHERE item_data->>'subject' = 'ai'
)
SELECT 
  item_data->>'subject' as subject,
  AVG(embedding <=> (SELECT center_embedding FROM ai_center)) as avg_distance_to_ai_center,
  COUNT(*) as book_count
FROM items
GROUP BY item_data->>'subject'
ORDER BY avg_distance_to_ai_center ASC;
```

**Question**: Which subjects are most similar to AI? Does this make sense?

### Experiment 3: Query Refinement
Try these different queries and compare results:

1. **Broad query**: "programming"
2. **Specific query**: "python web development frameworks"
3. **Conceptual query**: "building scalable software applications"

```bash
# Use the helper script to test different queries
python search_assistant.py --query "programming" --limit 5
python search_assistant.py --query "python web development frameworks" --limit 5  
python search_assistant.py --query "building scalable software applications" --limit 5
```

**Question**: How do the results differ? Which approach gives better results for your needs?

### Experiment 4: Similarity Thresholds
```sql
-- Find books with different similarity thresholds
SELECT 
  'Very Similar (< 0.3)' as category,
  COUNT(*) as count
FROM items
WHERE embedding <=> (SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1) < 0.3

UNION ALL

SELECT 
  'Somewhat Similar (0.3-0.6)' as category,
  COUNT(*) as count
FROM items
WHERE embedding <=> (SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1) BETWEEN 0.3 AND 0.6

UNION ALL

SELECT 
  'Not Very Similar (> 0.6)' as category,
  COUNT(*) as count
FROM items
WHERE embedding <=> (SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1) > 0.6;
```

**Question**: What similarity threshold works best for your use case?

## Understanding Vector Search vs Traditional Search

### Traditional Text Search
```sql
-- Find books using traditional text matching
SELECT name, item_data->>'subject' as subject
FROM items
WHERE name ILIKE '%machine%' OR name ILIKE '%learning%'
ORDER BY name;
```

### Vector Semantic Search
```sql
-- Find books using semantic similarity (no exact word matches required)
SELECT 
  name,
  item_data->>'subject' as subject,
  embedding <=> (
    SELECT AVG(embedding) 
    FROM items 
    WHERE name ILIKE '%machine%' OR name ILIKE '%learning%'
  ) as similarity
FROM items
ORDER BY similarity ASC
LIMIT 10;
```

**Compare the results**: Which approach finds more relevant books? Which finds different types of relevant books?

## Advanced Concepts

### Hybrid Search (Combining Vector + Traditional)
```sql
-- Combine text matching with vector similarity
WITH text_matches AS (
  SELECT *, 1.0 as text_boost
  FROM items
  WHERE name ILIKE '%python%'
),
vector_matches AS (
  SELECT 
    *,
    embedding <=> (
      SELECT AVG(embedding) FROM text_matches
    ) as similarity,
    0.5 as vector_boost
  FROM items
  WHERE embedding <=> (
    SELECT AVG(embedding) FROM text_matches
  ) < 0.6
)
SELECT 
  i.name,
  i.item_data->>'subject' as subject,
  COALESCE(tm.text_boost, 0) + COALESCE(vm.vector_boost, 0) as combined_score,
  vm.similarity
FROM items i
LEFT JOIN text_matches tm ON i.name = tm.name
LEFT JOIN vector_matches vm ON i.name = vm.name
WHERE tm.name IS NOT NULL OR vm.name IS NOT NULL
ORDER BY combined_score DESC, vm.similarity ASC
LIMIT 10;
```

### Performance Analysis
```sql
-- Compare query performance
EXPLAIN ANALYZE
SELECT 
  name, 
  embedding <=> (SELECT embedding FROM items LIMIT 1) as similarity
FROM items
WHERE name != (SELECT name FROM items LIMIT 1)  -- Exclude the reference book
ORDER BY similarity
LIMIT 5; 
```

## Troubleshooting

### If you get no results:
```sql
-- Check if you have data
SELECT COUNT(*) FROM items;

-- Check if embeddings exist
SELECT COUNT(*) FROM items WHERE embedding IS NOT NULL;

-- Check data structure
SELECT name, item_data->>'subject' FROM items LIMIT 3;
```

### If similarity scores seem wrong:
```sql
-- Check embedding dimensions
SELECT vector_dims(embedding) FROM items LIMIT 1;

-- Check for null embeddings
SELECT COUNT(*) FROM items WHERE embedding IS NULL;
```

### If queries are slow:
```sql
-- Create vector index for better performance
CREATE INDEX IF NOT EXISTS embedding_cosine_idx 
ON items 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);
```

## Success Criteria

You've completed the lab when you can:
1. ✅ Understand how similarity scores relate to content relevance
2. ✅ Choose appropriate similarity measures for different use cases
3. ✅ Combine vector search with traditional filters
4. ✅ Explain when vector search works well vs poorly
5. ✅ Optimize search performance with indexing

## Real-World Applications

Think about how vector similarity search applies to your domain:

### E-commerce
- **Product recommendations**: "Customers who liked this also liked..."
- **Search refinement**: "Similar products" when exact matches aren't available
- **Category discovery**: Group products by semantic similarity

### Content Management
- **Document search**: Find documents by concept, not just keywords
- **Content recommendations**: Suggest related articles or resources
- **Duplicate detection**: Find semantically similar content

### Customer Support
- **Ticket routing**: Match new tickets to similar resolved cases
- **Knowledge base search**: Find relevant help articles
- **FAQ automation**: Match questions to existing answers

### Research & Development
- **Literature review**: Find related papers and research
- **Patent search**: Identify similar inventions or prior art
- **Trend analysis**: Group similar concepts and ideas

## Key Insights

After completing this lab, you should understand:

1. **Vector similarity captures semantic meaning** - not just word overlap
2. **Different distance metrics work better for different use cases**
3. **Similarity thresholds need to be tuned for your specific domain**
4. **Combining vector search with traditional filters is powerful**
5. **Performance optimization is crucial for production systems**
6. **Vector search complements, doesn't replace, traditional search**

## Next Steps

Once you understand these concepts:
1. Try with your own domain-specific data
2. Experiment with different embedding models
3. Build hybrid search systems combining multiple approaches
4. Move on to the RAG lab to see how to enhance results with LLMs

Remember: **These concepts transfer to any vector database or search system!** 

## Use any existing book's embedding as the query vector
SELECT 
  name, 
  embedding <=> (SELECT embedding FROM items LIMIT 1) as similarity
FROM items
WHERE name != (SELECT name FROM items LIMIT 1)  -- Exclude the reference book
ORDER BY similarity
LIMIT 5; 
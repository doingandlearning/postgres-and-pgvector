# SQL Exploration Guide - Vector Embeddings

This guide provides SQL queries and exercises to help you understand how vector embeddings work in PostgreSQL without requiring Python programming knowledge.

## Prerequisites

1. Load some data first using one of these methods:
   ```bash
   # Option 1: Load sample data (no API calls)
   python load_sample_data.py
   
   # Option 2: Load from Open Library
   python book_loader.py --source open_library --categories "ai,programming" --limit 5
   ```

2. Connect to your database:
   ```bash
   docker exec -it pgvector-db psql -U postgres -d pgvector
   ```

## Basic Data Exploration

### 1. Count Your Data
```sql
-- How many books do we have?
SELECT COUNT(*) as total_books FROM items;
```

### 2. Explore the Structure
```sql
-- What does our data look like?
SELECT 
  name,
  item_data->>'subject' as subject,
  item_data->>'authors' as authors,
  item_data->>'first_publish_year' as year
FROM items 
LIMIT 5;
```

### 3. Check Embedding Dimensions
```sql
-- How many dimensions do our embeddings have?
SELECT 
  name,
  array_length(embedding, 1) as embedding_dimensions
FROM items 
LIMIT 3;
```

### 4. View Raw Embedding Data
```sql
-- What do embeddings actually look like?
SELECT 
  name,
  embedding[1:10] as first_10_dimensions
FROM items 
LIMIT 2;
```

## Subject-Based Analysis

### 5. Count Books by Subject
```sql
-- How many books per subject?
SELECT 
  item_data->>'subject' as subject,
  COUNT(*) as book_count
FROM items 
GROUP BY item_data->>'subject'
ORDER BY book_count DESC;
```

### 6. Find Books by Subject
```sql
-- Show all AI books
SELECT 
  name,
  item_data->>'authors' as authors,
  item_data->>'first_publish_year' as year
FROM items 
WHERE item_data->>'subject' = 'ai'
ORDER BY name;
```

### 7. Publication Year Analysis
```sql
-- Books published after 2020
SELECT 
  name,
  item_data->>'first_publish_year' as year,
  item_data->>'subject' as subject
FROM items 
WHERE (item_data->>'first_publish_year')::int > 2020
ORDER BY (item_data->>'first_publish_year')::int DESC;
```

## Vector Similarity Basics

### 8. Your First Similarity Search
```sql
-- Find books similar to a specific book using cosine similarity
-- This finds books similar to the first programming book
SELECT 
  name,
  item_data->>'subject' as subject,
  embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE item_data->>'subject' = 'programming' 
    LIMIT 1
  ) as similarity_score
FROM items
ORDER BY similarity_score ASC  -- Lower scores = more similar
LIMIT 5;
```

### 9. Compare Different Similarity Operators

**Cosine Similarity (most common for text embeddings):**
```sql
SELECT 
  name,
  embedding <=> (SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1) as cosine_similarity
FROM items
ORDER BY cosine_similarity ASC
LIMIT 3;
```

**Euclidean Distance:**
```sql
SELECT 
  name,
  embedding <-> (SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1) as euclidean_distance
FROM items
ORDER BY euclidean_distance ASC
LIMIT 3;
```

**Inner Product:**
```sql
SELECT 
  name,
  embedding <#> (SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1) as inner_product
FROM items
ORDER BY inner_product ASC
LIMIT 3;
```

## Advanced Vector Queries

### 10. Cross-Subject Similarity
```sql
-- Find programming books most similar to AI books
WITH ai_average AS (
  SELECT AVG(embedding) as avg_embedding
  FROM items 
  WHERE item_data->>'subject' = 'ai'
)
SELECT 
  name,
  item_data->>'subject' as subject,
  embedding <=> (SELECT avg_embedding FROM ai_average) as similarity_to_ai
FROM items
WHERE item_data->>'subject' = 'programming'
ORDER BY similarity_to_ai ASC
LIMIT 5;
```

### 11. Multi-Subject Analysis
```sql
-- Compare how similar each book is to different subject averages
WITH subject_averages AS (
  SELECT 
    item_data->>'subject' as subject,
    AVG(embedding) as avg_embedding
  FROM items
  GROUP BY item_data->>'subject'
)
SELECT 
  i.name,
  i.item_data->>'subject' as actual_subject,
  (i.embedding <=> sa1.avg_embedding) as similarity_to_programming,
  (i.embedding <=> sa2.avg_embedding) as similarity_to_ai,
  (i.embedding <=> sa3.avg_embedding) as similarity_to_web_dev
FROM items i
CROSS JOIN (SELECT avg_embedding FROM subject_averages WHERE subject = 'programming') sa1
CROSS JOIN (SELECT avg_embedding FROM subject_averages WHERE subject = 'ai') sa2
CROSS JOIN (SELECT avg_embedding FROM subject_averages WHERE subject = 'web_development') sa3
LIMIT 5;
```

## Understanding Results

### 12. Similarity Score Interpretation
```sql
-- Show similarity scores with context
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (
    SELECT embedding FROM items WHERE name LIKE '%Machine Learning%' LIMIT 1
  ))::numeric, 4) as similarity,
  CASE 
    WHEN (embedding <=> (SELECT embedding FROM items WHERE name LIKE '%Machine Learning%' LIMIT 1)) < 0.3 
    THEN 'Very Similar'
    WHEN (embedding <=> (SELECT embedding FROM items WHERE name LIKE '%Machine Learning%' LIMIT 1)) < 0.6 
    THEN 'Somewhat Similar'
    ELSE 'Not Very Similar'
  END as similarity_category
FROM items
ORDER BY similarity ASC
LIMIT 10;
```

## Performance and Indexing

### 13. Query Performance (Before Index)
```sql
-- Time a similarity search (note the execution time)
EXPLAIN ANALYZE
SELECT name, embedding <=> (
  SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1
) as similarity
FROM items
ORDER BY similarity
LIMIT 5;
```

### 14. Create Vector Index
```sql
-- Create an index to speed up similarity searches
CREATE INDEX embedding_cosine_idx 
ON items 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);
```

### 15. Query Performance (After Index)
```sql
-- Time the same query after indexing
EXPLAIN ANALYZE
SELECT name, embedding <=> (
  SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1
) as similarity
FROM items
ORDER BY similarity
LIMIT 5;
```

## Practical Exercises

### Exercise 1: Find Your Domain
If you loaded books about your field of interest, find books most similar to a specific topic:

```sql
-- Replace 'YOUR_TOPIC' with something from your data
SELECT name, item_data->>'subject' as subject
FROM items
WHERE name ILIKE '%YOUR_TOPIC%'
LIMIT 3;

-- Then use one of those books to find similar ones
SELECT 
  name,
  embedding <=> (
    SELECT embedding FROM items WHERE name ILIKE '%YOUR_TOPIC%' LIMIT 1
  ) as similarity
FROM items
ORDER BY similarity ASC
LIMIT 5;
```

### Exercise 2: Embedding Arithmetic
```sql
-- Try "vector arithmetic" - find books similar to (AI + Programming)
WITH concept_vectors AS (
  SELECT 
    (SELECT AVG(embedding) FROM items WHERE item_data->>'subject' = 'ai') +
    (SELECT AVG(embedding) FROM items WHERE item_data->>'subject' = 'programming') as combined_vector
)
SELECT 
  name,
  item_data->>'subject' as subject,
  embedding <=> (SELECT combined_vector FROM concept_vectors) as similarity
FROM items
ORDER BY similarity ASC
LIMIT 5;
```

### Exercise 3: Outlier Detection
```sql
-- Find books that are least similar to their own subject
WITH subject_averages AS (
  SELECT 
    item_data->>'subject' as subject,
    AVG(embedding) as avg_embedding
  FROM items
  GROUP BY item_data->>'subject'
)
SELECT 
  i.name,
  i.item_data->>'subject' as subject,
  i.embedding <=> sa.avg_embedding as distance_from_subject_average
FROM items i
JOIN subject_averages sa ON i.item_data->>'subject' = sa.subject
ORDER BY distance_from_subject_average DESC
LIMIT 5;
```

## Key Learning Points

After running these queries, you should understand:

1. **Embeddings are just arrays of numbers** - but they capture semantic meaning
2. **Lower similarity scores mean more similar** (for cosine distance)
3. **Different subjects cluster together** in the vector space
4. **Vector arithmetic can work** - combining concepts mathematically
5. **Indexing is crucial** for performance with large datasets
6. **PostgreSQL + pgvector** makes vector operations accessible via SQL

## Next Steps

Once you're comfortable with these concepts:
1. Try loading your own domain-specific data
2. Experiment with different similarity thresholds
3. Combine vector similarity with traditional SQL filters
4. Move on to the next lab modules to learn about chunking and RAG

Remember: **These same concepts apply regardless of the programming language or platform you eventually use!** 
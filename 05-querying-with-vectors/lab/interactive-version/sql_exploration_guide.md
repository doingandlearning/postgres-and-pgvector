# SQL Exploration Guide: Vector Similarity Search

## Overview
This guide helps you understand vector similarity search using only SQL queries. Perfect for database professionals who want to understand the concepts without diving into Python programming.

## Prerequisites

1. **Connect to your database:**
   ```bash
   docker exec -it pgvector-db psql -U postgres -d pgvector
   ```

2. **Verify you have data:**
   ```sql
   SELECT COUNT(*) FROM items;
   SELECT COUNT(*) FROM items WHERE embedding IS NOT NULL;
   ```

If you need data, exit SQL and run:
```bash
cd ../../../03-generating-and-storing/lab/non-python-starter
python load_sample_data.py
```

## Part 1: Understanding Your Data

### 1.1 Explore the Data Structure
```sql
-- See what columns are available
\d items

-- Look at sample data
SELECT name, item_data->>'subject' as subject
FROM items 
LIMIT 5;

-- See all available subjects
SELECT 
  item_data->>'subject' as subject,
  COUNT(*) as book_count
FROM items
GROUP BY item_data->>'subject'
ORDER BY book_count DESC;
```

### 1.2 Understanding Embeddings
```sql
-- Check embedding dimensions
SELECT array_length(embedding, 1) as embedding_dimensions
FROM items 
WHERE embedding IS NOT NULL
LIMIT 1;

-- See a small sample of embedding values
SELECT 
  name,
  embedding[1:5] as first_5_dimensions
FROM items
LIMIT 3;
```

## Part 2: Basic Similarity Search

### 2.1 Find Similar Books to a Specific Book
```sql
-- Method 1: Find books similar to "Python"
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE name ILIKE '%Python%' 
    LIMIT 1
  ))::numeric, 4) as similarity_score
FROM items
WHERE name NOT ILIKE '%Python%'  -- Exclude the reference book itself
ORDER BY similarity_score ASC
LIMIT 5;
```

```sql
-- Method 2: Find books similar to "Machine Learning"
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE name ILIKE '%Machine Learning%' 
    LIMIT 1
  ))::numeric, 4) as similarity_score
FROM items
WHERE name NOT ILIKE '%Machine Learning%'
ORDER BY similarity_score ASC
LIMIT 5;
```

**🤔 Question**: Compare the results. Do the similar books make sense? What subjects appear most often?

### 2.2 Understanding Similarity Scores
```sql
-- Get the range of similarity scores for a reference book
WITH reference_book AS (
  SELECT embedding FROM items WHERE name ILIKE '%Python%' LIMIT 1
)
SELECT 
  MIN(embedding <=> (SELECT embedding FROM reference_book)) as min_similarity,
  MAX(embedding <=> (SELECT embedding FROM reference_book)) as max_similarity,
  AVG(embedding <=> (SELECT embedding FROM reference_book)) as avg_similarity,
  STDDEV(embedding <=> (SELECT embedding FROM reference_book)) as std_similarity
FROM items;
```

**🤔 Question**: What do these statistics tell you about how similar/different your books are?

## Part 3: Comparing Distance Metrics

### 3.1 Three Ways to Measure Distance
```sql
-- Compare all three distance metrics for the same query
WITH target_book AS (
  SELECT embedding FROM items WHERE name ILIKE '%JavaScript%' LIMIT 1
)
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (SELECT embedding FROM target_book))::numeric, 4) as cosine_similarity,
  ROUND((embedding <-> (SELECT embedding FROM target_book))::numeric, 4) as euclidean_distance,
  ROUND((embedding <#> (SELECT embedding FROM target_book))::numeric, 4) as inner_product
FROM items
WHERE name NOT ILIKE '%JavaScript%'
ORDER BY cosine_similarity ASC
LIMIT 5;
```

**🤔 Question**: Do the three metrics rank the books in the same order? Which one seems most intuitive?

### 3.2 Understanding the Differences
```sql
-- See how rankings differ between metrics
WITH target_book AS (
  SELECT embedding FROM items WHERE name ILIKE '%Data%' LIMIT 1
),
cosine_ranking AS (
  SELECT 
    name,
    ROW_NUMBER() OVER (ORDER BY embedding <=> (SELECT embedding FROM target_book)) as cosine_rank
  FROM items
  WHERE name NOT ILIKE '%Data%'
),
euclidean_ranking AS (
  SELECT 
    name,
    ROW_NUMBER() OVER (ORDER BY embedding <-> (SELECT embedding FROM target_book)) as euclidean_rank
  FROM items
  WHERE name NOT ILIKE '%Data%'
)
SELECT 
  cr.name,
  cr.cosine_rank,
  er.euclidean_rank,
  ABS(cr.cosine_rank - er.euclidean_rank) as rank_difference
FROM cosine_ranking cr
JOIN euclidean_ranking er ON cr.name = er.name
WHERE cr.cosine_rank <= 10 OR er.euclidean_rank <= 10
ORDER BY rank_difference DESC, cr.cosine_rank;
```

**🤔 Question**: Which books have the biggest ranking differences? What might this tell you?

## Part 4: Filtering and Thresholds

### 4.1 Using Similarity Thresholds
```sql
-- Find books with different levels of similarity
WITH reference_book AS (
  SELECT embedding FROM items WHERE name ILIKE '%Algorithm%' LIMIT 1
)
SELECT 
  CASE 
    WHEN embedding <=> (SELECT embedding FROM reference_book) < 0.3 THEN 'Very Similar'
    WHEN embedding <=> (SELECT embedding FROM reference_book) < 0.6 THEN 'Somewhat Similar'
    WHEN embedding <=> (SELECT embedding FROM reference_book) < 0.8 THEN 'Loosely Similar'
    ELSE 'Not Similar'
  END as similarity_category,
  COUNT(*) as book_count
FROM items
WHERE name NOT ILIKE '%Algorithm%'
GROUP BY 
  CASE 
    WHEN embedding <=> (SELECT embedding FROM reference_book) < 0.3 THEN 'Very Similar'
    WHEN embedding <=> (SELECT embedding FROM reference_book) < 0.6 THEN 'Somewhat Similar'
    WHEN embedding <=> (SELECT embedding FROM reference_book) < 0.8 THEN 'Loosely Similar'
    ELSE 'Not Similar'
  END
ORDER BY 
  CASE similarity_category
    WHEN 'Very Similar' THEN 1
    WHEN 'Somewhat Similar' THEN 2
    WHEN 'Loosely Similar' THEN 3
    ELSE 4
  END;
```

### 4.2 Subject-Filtered Similarity Search
```sql
-- Find similar books within the same subject
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE name ILIKE '%Web%' 
    LIMIT 1
  ))::numeric, 4) as similarity_score
FROM items
WHERE item_data->>'subject' = 'programming'  -- Only programming books
  AND name NOT ILIKE '%Web%'
ORDER BY similarity_score ASC
LIMIT 5;
```

```sql
-- Compare: Find similar books across ALL subjects
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE name ILIKE '%Web%' 
    LIMIT 1
  ))::numeric, 4) as similarity_score
FROM items
WHERE name NOT ILIKE '%Web%'
ORDER BY similarity_score ASC
LIMIT 5;
```

**🤔 Question**: How do the results differ when you filter by subject vs. search across all subjects?

## Part 5: Advanced Similarity Analysis

### 5.1 Subject Clustering Analysis
```sql
-- See how well different subjects cluster together
WITH ai_center AS (
  SELECT AVG(embedding) as center_embedding
  FROM items 
  WHERE item_data->>'subject' = 'ai'
),
programming_center AS (
  SELECT AVG(embedding) as center_embedding
  FROM items 
  WHERE item_data->>'subject' = 'programming'
)
SELECT 
  item_data->>'subject' as subject,
  ROUND(AVG(embedding <=> (SELECT center_embedding FROM ai_center))::numeric, 4) as avg_distance_to_ai,
  ROUND(AVG(embedding <=> (SELECT center_embedding FROM programming_center))::numeric, 4) as avg_distance_to_programming,
  COUNT(*) as book_count
FROM items
GROUP BY item_data->>'subject'
ORDER BY avg_distance_to_ai ASC;
```

**🤔 Question**: Which subjects are closest to AI? Which are closest to programming? Does this make intuitive sense?

### 5.2 Finding Outliers
```sql
-- Find books that are very different from others in their subject
WITH subject_centers AS (
  SELECT 
    item_data->>'subject' as subject,
    AVG(embedding) as center_embedding
  FROM items
  GROUP BY item_data->>'subject'
)
SELECT 
  i.name,
  i.item_data->>'subject' as subject,
  ROUND((i.embedding <=> sc.center_embedding)::numeric, 4) as distance_from_center
FROM items i
JOIN subject_centers sc ON i.item_data->>'subject' = sc.subject
ORDER BY distance_from_center DESC
LIMIT 10;
```

**🤔 Question**: Are these outliers actually different from their subject? Or do they represent edge cases?

## Part 6: Hybrid Search (Combining Text + Vector)

### 6.1 Traditional Text Search
```sql
-- Traditional text-based search
SELECT name, item_data->>'subject' as subject
FROM items
WHERE name ILIKE '%machine%' 
   OR name ILIKE '%learning%'
   OR name ILIKE '%algorithm%'
ORDER BY name;
```

### 6.2 Vector-Only Search
```sql
-- Vector search for the same concept
WITH ml_books AS (
  SELECT AVG(embedding) as concept_embedding
  FROM items 
  WHERE name ILIKE '%machine%' OR name ILIKE '%learning%'
)
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (SELECT concept_embedding FROM ml_books))::numeric, 4) as similarity
FROM items
WHERE NOT (name ILIKE '%machine%' OR name ILIKE '%learning%')
ORDER BY similarity ASC
LIMIT 10;
```

### 6.3 Hybrid Approach
```sql
-- Combine both approaches with scoring
WITH text_matches AS (
  SELECT *, 2.0 as text_boost  -- Higher weight for exact text matches
  FROM items
  WHERE name ILIKE '%python%'
),
vector_matches AS (
  SELECT 
    *,
    embedding <=> (
      SELECT AVG(embedding) FROM text_matches
    ) as similarity,
    1.0 as vector_boost
  FROM items
  WHERE embedding <=> (
    SELECT AVG(embedding) FROM text_matches
  ) < 0.7
)
SELECT 
  COALESCE(tm.name, vm.name) as name,
  COALESCE(tm.item_data->>'subject', vm.item_data->>'subject') as subject,
  COALESCE(tm.text_boost, 0) + COALESCE(vm.vector_boost, 0) as combined_score,
  vm.similarity
FROM text_matches tm
FULL OUTER JOIN vector_matches vm ON tm.name = vm.name
ORDER BY combined_score DESC, vm.similarity ASC
LIMIT 10;
```

**🤔 Question**: How do the three approaches (text-only, vector-only, hybrid) differ in their results?

## Part 7: Performance and Indexing

### 7.1 Query Performance Analysis
```sql
-- Measure query performance
EXPLAIN ANALYZE
SELECT name, embedding <=> '[0.1,0.2,0.3]'::vector as similarity
FROM items
ORDER BY similarity
LIMIT 5;
```

### 7.2 Create Vector Index for Better Performance
```sql
-- Create an index for cosine similarity searches
CREATE INDEX IF NOT EXISTS embedding_cosine_idx 
ON items 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);

-- Test performance improvement
EXPLAIN ANALYZE
SELECT name, embedding <=> '[0.1,0.2,0.3]'::vector as similarity
FROM items
ORDER BY similarity
LIMIT 5;
```

**🤔 Question**: How much did the index improve query performance?

### 7.3 Different Index Types
```sql
-- Create indexes for different distance metrics
CREATE INDEX IF NOT EXISTS embedding_euclidean_idx 
ON items 
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 10);

CREATE INDEX IF NOT EXISTS embedding_inner_product_idx 
ON items 
USING ivfflat (embedding vector_ip_ops)
WITH (lists = 10);
```

## Part 8: Practical Experiments

### 8.1 Recommendation Engine Simulation
```sql
-- Simulate "Users who liked this book also liked..."
WITH user_liked_book AS (
  SELECT embedding FROM items WHERE name ILIKE '%Django%' LIMIT 1
)
SELECT 
  'Customers who liked Django also liked:' as recommendation_type,
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (SELECT embedding FROM user_liked_book))::numeric, 4) as similarity
FROM items
WHERE name NOT ILIKE '%Django%'
  AND embedding <=> (SELECT embedding FROM user_liked_book) < 0.6
ORDER BY similarity ASC
LIMIT 5;
```

### 8.2 Content Discovery
```sql
-- Find "hidden gems" - books that are similar to popular topics but different
WITH popular_concept AS (
  SELECT AVG(embedding) as concept_embedding
  FROM items 
  WHERE item_data->>'subject' = 'ai'
)
SELECT 
  name,
  item_data->>'subject' as subject,
  ROUND((embedding <=> (SELECT concept_embedding FROM popular_concept))::numeric, 4) as similarity_to_ai
FROM items
WHERE item_data->>'subject' != 'ai'  -- Books NOT labeled as AI
  AND embedding <=> (SELECT concept_embedding FROM popular_concept) < 0.5  -- But similar to AI
ORDER BY similarity_to_ai ASC
LIMIT 5;
```

**🤔 Question**: Did you discover any surprising connections between different subjects?

## Part 9: Data Quality Assessment

### 9.1 Embedding Quality Check
```sql
-- Check for potential embedding issues
SELECT 
  'Null embeddings' as issue_type,
  COUNT(*) as count
FROM items 
WHERE embedding IS NULL

UNION ALL

SELECT 
  'Zero vectors' as issue_type,
  COUNT(*) as count
FROM items 
WHERE array_length(embedding, 1) > 0 
  AND embedding = array_fill(0.0, ARRAY[array_length(embedding, 1)])

UNION ALL

SELECT 
  'Dimension consistency' as issue_type,
  COUNT(DISTINCT array_length(embedding, 1)) as count
FROM items 
WHERE embedding IS NOT NULL;
```

### 9.2 Similarity Distribution Analysis
```sql
-- Understand the distribution of similarity scores
WITH similarity_stats AS (
  SELECT 
    i1.embedding <=> i2.embedding as similarity
  FROM items i1
  CROSS JOIN items i2
  WHERE i1.name != i2.name
  LIMIT 1000  -- Sample to avoid huge result set
)
SELECT 
  ROUND(MIN(similarity)::numeric, 4) as min_similarity,
  ROUND(MAX(similarity)::numeric, 4) as max_similarity,
  ROUND(AVG(similarity)::numeric, 4) as avg_similarity,
  ROUND(STDDEV(similarity)::numeric, 4) as std_similarity,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY similarity) as median_similarity
FROM similarity_stats;
```

## Part 10: Business Intelligence Queries

### 10.1 Subject Relationship Analysis
```sql
-- Create a subject similarity matrix
WITH subject_pairs AS (
  SELECT DISTINCT 
    i1.item_data->>'subject' as subject1,
    i2.item_data->>'subject' as subject2
  FROM items i1
  CROSS JOIN items i2
  WHERE i1.item_data->>'subject' != i2.item_data->>'subject'
    AND i1.item_data->>'subject' IS NOT NULL
    AND i2.item_data->>'subject' IS NOT NULL
)
SELECT 
  sp.subject1,
  sp.subject2,
  ROUND(AVG(i1.embedding <=> i2.embedding)::numeric, 4) as avg_similarity
FROM subject_pairs sp
JOIN items i1 ON i1.item_data->>'subject' = sp.subject1
JOIN items i2 ON i2.item_data->>'subject' = sp.subject2
GROUP BY sp.subject1, sp.subject2
ORDER BY avg_similarity ASC;
```

### 10.2 Content Gap Analysis
```sql
-- Find underrepresented topics (subjects with few similar books)
WITH subject_diversity AS (
  SELECT 
    i1.item_data->>'subject' as subject,
    AVG(i1.embedding <=> i2.embedding) as avg_internal_similarity,
    COUNT(*) as book_count
  FROM items i1
  JOIN items i2 ON i1.item_data->>'subject' = i2.item_data->>'subject'
    AND i1.name != i2.name
  GROUP BY i1.item_data->>'subject'
  HAVING COUNT(*) > 1
)
SELECT 
  subject,
  book_count,
  ROUND(avg_internal_similarity::numeric, 4) as diversity_score
FROM subject_diversity
ORDER BY diversity_score DESC;  -- Higher scores = more diverse content
```

**🤔 Question**: Which subjects have the most diverse content? Which are most homogeneous?

## Key Insights and Takeaways

After completing these exercises, you should understand:

1. **Vector similarity captures semantic relationships** beyond keyword matching
2. **Different distance metrics can produce different rankings** - choose based on your use case
3. **Similarity thresholds need tuning** for your specific domain and requirements
4. **Subject filtering can improve relevance** but may miss cross-domain insights
5. **Hybrid approaches** combining text and vector search often work best
6. **Performance optimization** with indexes is crucial for production systems
7. **Data quality** affects search quality - check for null/zero embeddings

## Real-World Applications

These SQL patterns can be adapted for:

- **E-commerce**: Product recommendations and similar item suggestions
- **Content Management**: Related article suggestions and content discovery
- **Customer Support**: Finding similar tickets and knowledge base articles
- **Research**: Literature review and finding related papers
- **HR**: Matching candidates to job descriptions
- **Marketing**: Audience segmentation and content personalization

## Next Steps

1. **Try with your own data** - adapt these queries to your domain
2. **Experiment with different embedding models** - see how results change
3. **Build hybrid search systems** - combine multiple approaches
4. **Move to the RAG lab** - see how to enhance results with LLMs
5. **Consider vector databases** - explore specialized solutions for production

Remember: **These concepts transfer to any vector search system!** Whether you use PostgreSQL, Elasticsearch, Pinecone, or Weaviate, the fundamental principles remain the same. 
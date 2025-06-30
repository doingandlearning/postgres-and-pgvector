# Lab: Hybrid Queries - Vector, Relational & JSONB Integration (Non-Python Starter)

## Objective
This lab focuses on mastering **hybrid queries** that combine vector embeddings, traditional relational data, and flexible JSONB metadata in PostgreSQL. You'll learn to build sophisticated search systems that leverage multiple data types for optimal results.

## Learning Goals
- Combine vector similarity search with relational filtering
- Integrate JSONB metadata queries with vector operations
- Optimize hybrid query performance with appropriate indexing
- Build real-world search applications using multiple data paradigms
- Understand trade-offs between different query approaches
- Master advanced PostgreSQL features for modern AI applications

## Prerequisites

Make sure you have:
1. PostgreSQL with pgvector extension running
2. Sample data loaded from previous labs
3. Ollama running for embedding generation

```bash
# Start the database (from the course root directory)
cd ../../environment
docker-compose up -d

# Verify Ollama is running
curl http://localhost:11434/api/tags

# Connect to the database
docker exec -it pgvector-db psql -U postgres -d pgvector
```

## Understanding Hybrid Queries

### What are Hybrid Queries?

Hybrid queries combine multiple data access patterns in a single query:

1. **Vector Similarity** - Semantic search using embeddings
2. **Relational Filtering** - Traditional WHERE clauses on structured data
3. **JSONB Operations** - Flexible metadata queries
4. **Full-Text Search** - Text-based search capabilities

### Why Use Hybrid Queries?

| Approach | Strength | Weakness |
|----------|----------|----------|
| **Vector Only** | Great semantic understanding | No business logic filtering |
| **Relational Only** | Fast, precise filtering | No semantic understanding |
| **JSONB Only** | Flexible schema | Can be slow without indexes |
| **Hybrid** | Best of all worlds | More complex to optimize |

### Real-World Use Cases

- **E-commerce**: "Find laptops similar to this one, under $1000, in stock"
- **Content Discovery**: "Articles like this, published recently, by verified authors"
- **Job Search**: "Jobs similar to my skills, remote, at startups"
- **Recipe Search**: "Recipes like this, vegetarian, under 30 minutes"

## Approach Options

### Option A: Interactive SQL Workshop (Recommended)

Learn through hands-on SQL exercises building a complete search system.

#### Step 1: Set Up the Enhanced Schema

First, let's enhance our existing `items` table to support hybrid queries:

```sql
-- Connect to PostgreSQL first
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- Add columns for hybrid queries
ALTER TABLE items ADD COLUMN IF NOT EXISTS subject TEXT;
ALTER TABLE items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE items ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Verify the schema
\d items
```

#### Step 2: Generate Sample Enhanced Data

Since we're avoiding Python, let's create enhanced data using SQL:

```sql
-- Update existing items with sample data
UPDATE items SET 
    subject = CASE 
        WHEN item_data::text ILIKE '%programming%' OR item_data::text ILIKE '%code%' THEN 'Programming'
        WHEN item_data::text ILIKE '%ai%' OR item_data::text ILIKE '%artificial%' OR item_data::text ILIKE '%machine%' THEN 'AI'
        WHEN item_data::text ILIKE '%data%' OR item_data::text ILIKE '%science%' THEN 'Data Science'
        WHEN item_data::text ILIKE '%web%' OR item_data::text ILIKE '%javascript%' OR item_data::text ILIKE '%html%' THEN 'Web Development'
        WHEN item_data::text ILIKE '%database%' OR item_data::text ILIKE '%sql%' THEN 'Database'
        ELSE 'General'
    END,
    created_at = NOW() - (random() * interval '365 days'),
    metadata = jsonb_build_object(
        'price', round((random() * 90 + 10)::numeric, 2),
        'stock', floor(random() * 500 + 5)::integer,
        'format', (ARRAY['ebook', 'paperback', 'hardcover'])[floor(random() * 3 + 1)],
        'rating', round((random() * 2 + 3)::numeric, 1),
        'pages', floor(random() * 400 + 100)::integer,
        'publisher', (ARRAY['Tech Books', 'O''Reilly', 'Manning', 'Packt', 'Apress'])[floor(random() * 5 + 1)],
        'language', 'English',
        'isbn', '978-' || floor(random() * 9000000000 + 1000000000)::text
    )
WHERE subject IS NULL;

-- Verify the data
SELECT name, subject, metadata->>'price' as price, metadata->>'format' as format
FROM items
LIMIT 5;
```

#### Step 3: Basic Hybrid Queries

Now let's explore different types of hybrid queries:

##### 3.1 Vector Search with Relational Filtering

```sql
-- Find books similar to a specific book, but only in the "Programming" category
WITH query_vector AS (
    SELECT embedding
    FROM items
    WHERE name ILIKE '%python%'
    LIMIT 1
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    items.embedding <=> (SELECT embedding FROM query_vector) as similarity
FROM items, query_vector
WHERE subject = 'Programming'
ORDER BY items.embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;
```

##### 3.2 Vector Search with JSONB Filtering

```sql
-- Find similar books under $50 and in stock
WITH query_vector AS (
    SELECT embedding
    FROM items
    WHERE name ILIKE '%database%'
    LIMIT 1
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'stock' as stock,
    items.embedding <=> (SELECT embedding FROM query_vector) as similarity
FROM items, query_vector
WHERE (metadata->>'price')::NUMERIC < 50
  AND (metadata->>'stock')::INTEGER > 20
ORDER BY items.embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;
```

##### 3.3 Multi-Criteria Hybrid Search

```sql
-- Complex search: AI books, ebook format, under $40, published recently
WITH query_vector AS (
    SELECT embedding
    FROM items
    WHERE name ILIKE '%artificial intelligence%'
    LIMIT 1
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'format' as format,
    created_at,
    items.embedding <=> (SELECT embedding FROM query_vector) as similarity
FROM items, query_vector
WHERE subject = 'AI'
  AND metadata->>'format' = 'ebook'
  AND (metadata->>'price')::NUMERIC < 40
  AND created_at > NOW() - INTERVAL '2 years'
ORDER BY items.embedding <=> (SELECT embedding FROM query_vector)
LIMIT 5;
```

#### Step 4: Advanced Hybrid Patterns

##### 4.1 Weighted Scoring

```sql
-- Combine similarity score with business metrics
WITH query_vector AS (
    SELECT embedding
    FROM items
    WHERE name ILIKE '%machine learning%'
    LIMIT 1
),
scored_results AS (
    SELECT 
        name,
        subject,
        metadata,
        items.embedding <=> (SELECT embedding FROM query_vector) as similarity,
        (metadata->>'rating')::NUMERIC as rating,
        CASE 
            WHEN (metadata->>'stock')::INTEGER > 100 THEN 1.0
            WHEN (metadata->>'stock')::INTEGER > 50 THEN 0.8
            WHEN (metadata->>'stock')::INTEGER > 10 THEN 0.6
            ELSE 0.3
        END as stock_score
    FROM items, query_vector
    WHERE subject IN ('AI', 'Data Science', 'Programming')
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    similarity,
    rating,
    stock_score,
    -- Composite score: similarity (40%) + rating (40%) + stock (20%)
    (similarity * 0.4 + (5 - rating) * 0.4 + (1 - stock_score) * 0.2) as composite_score
FROM scored_results
ORDER BY composite_score ASC
LIMIT 10;
```

##### 4.2 Category-Based Recommendations

```sql
-- Find books similar within category, then expand to related categories
WITH user_query AS (
    SELECT embedding, subject
    FROM items
    WHERE name ILIKE '%python programming%'
    LIMIT 1
),
same_category AS (
    SELECT 
        items.name, items.subject, items.metadata, 
        items.embedding <=> (SELECT embedding FROM user_query) as similarity,
        'same_category' as match_type
    FROM items, user_query
    WHERE items.subject = (SELECT subject FROM user_query)
    ORDER BY items.embedding <=> (SELECT embedding FROM user_query)
    LIMIT 5
),
related_categories AS (
    SELECT 
        items.name, items.subject, items.metadata,
        items.embedding <=> (SELECT embedding FROM user_query) as similarity,
        'related_category' as match_type
    FROM items, user_query
    WHERE items.subject IN ('Web Development', 'Data Science', 'Database')
      AND items.subject != (SELECT subject FROM user_query)
    ORDER BY items.embedding <=> (SELECT embedding FROM user_query)
    LIMIT 3
)
SELECT * FROM same_category
UNION ALL
SELECT * FROM related_categories
ORDER BY match_type, similarity;
```

#### Step 5: Performance Optimization

##### 5.1 Create Appropriate Indexes

```sql
-- Vector index for similarity search
CREATE INDEX IF NOT EXISTS items_embedding_cosine_idx 
ON items USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- JSONB index for metadata queries
CREATE INDEX IF NOT EXISTS items_metadata_gin_idx 
ON items USING GIN (metadata);

-- Relational indexes for common filters
CREATE INDEX IF NOT EXISTS items_subject_idx ON items (subject);
CREATE INDEX IF NOT EXISTS items_created_at_idx ON items (created_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS items_subject_price_idx 
ON items (subject, ((metadata->>'price')::NUMERIC));

-- Expression indexes for JSONB fields
CREATE INDEX IF NOT EXISTS items_price_idx 
ON items USING BTREE (((metadata->>'price')::NUMERIC));

CREATE INDEX IF NOT EXISTS items_stock_idx 
ON items USING BTREE (((metadata->>'stock')::INTEGER));

CREATE INDEX IF NOT EXISTS items_format_idx 
ON items USING BTREE ((metadata->>'format'));
```

##### 5.2 Query Performance Analysis

```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) 
WITH query_vector AS (
    SELECT embedding FROM items WHERE name ILIKE '%python%' LIMIT 1
)
SELECT name, subject, metadata->>'price' as price
FROM items, query_vector
WHERE subject = 'Programming'
  AND (metadata->>'price')::NUMERIC < 50
ORDER BY items.embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;
```

### Option B: Configuration-Based Search System

Build a flexible search system using configuration files and SQL templates.

#### Configuration File: `search_config.json`

```json
{
  "search_scenarios": [
    {
      "name": "budget_programming_books",
      "description": "Find affordable programming books",
      "base_query": "programming fundamentals",
      "filters": {
        "subject": "Programming",
        "max_price": 30,
        "format": "ebook",
        "min_stock": 10
      },
      "limit": 10,
      "sort_by": "similarity"
    },
    {
      "name": "premium_ai_books",
      "description": "Find high-quality AI books",
      "base_query": "artificial intelligence machine learning",
      "filters": {
        "subject": "AI",
        "min_rating": 4.0,
        "format": ["paperback", "hardcover"],
        "max_age_days": 730
      },
      "limit": 5,
      "sort_by": "composite"
    },
    {
      "name": "data_science_starter",
      "description": "Data science books for beginners",
      "base_query": "data science introduction",
      "filters": {
        "subject": ["Data Science", "Programming"],
        "max_price": 50,
        "max_pages": 400,
        "min_stock": 5
      },
      "limit": 8,
      "sort_by": "price_asc"
    }
  ],
  "database": {
    "host": "localhost",
    "port": 5050,
    "database": "pgvector",
    "user": "postgres",
    "password": "postgres"
  },
  "embedding": {
    "model": "bge-m3",
    "url": "http://localhost:11434/api/embed"
  }
}
```

### Option C: Real-World Application Patterns

#### E-commerce Book Search

```sql
-- Create a comprehensive book search function
CREATE OR REPLACE FUNCTION search_books(
    search_query TEXT,
    category_filter TEXT DEFAULT NULL,
    max_price NUMERIC DEFAULT NULL,
    format_filter TEXT DEFAULT NULL,
    min_rating NUMERIC DEFAULT NULL,
    in_stock_only BOOLEAN DEFAULT FALSE,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    book_name TEXT,
    category TEXT,
    price NUMERIC,
    format TEXT,
    rating NUMERIC,
    stock INTEGER,
    similarity_score NUMERIC,
    relevance_rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH query_embedding AS (
        -- In a real implementation, this would call an embedding service
        -- For demo purposes, we'll use an existing similar book's embedding
        SELECT embedding
        FROM items
        WHERE name ILIKE '%' || search_query || '%'
           OR item_data::text ILIKE '%' || search_query || '%'
        ORDER BY 
            CASE 
                WHEN name ILIKE '%' || search_query || '%' THEN 1
                ELSE 2
            END,
            random()
        LIMIT 1
    ),
    filtered_results AS (
        SELECT 
            i.name,
            i.subject,
            (i.metadata->>'price')::NUMERIC as book_price,
            i.metadata->>'format' as book_format,
            (i.metadata->>'rating')::NUMERIC as book_rating,
            (i.metadata->>'stock')::INTEGER as book_stock,
            i.embedding <=> (SELECT embedding FROM query_embedding) as similarity
        FROM items i, query_embedding
        WHERE (category_filter IS NULL OR i.subject = category_filter)
          AND (max_price IS NULL OR (i.metadata->>'price')::NUMERIC <= max_price)
          AND (format_filter IS NULL OR i.metadata->>'format' = format_filter)
          AND (min_rating IS NULL OR (i.metadata->>'rating')::NUMERIC >= min_rating)
          AND (NOT in_stock_only OR (i.metadata->>'stock')::INTEGER > 0)
    )
    SELECT 
        filtered_results.name,
        filtered_results.subject,
        filtered_results.book_price,
        filtered_results.book_format,
        filtered_results.book_rating,
        filtered_results.book_stock,
        filtered_results.similarity,
        ROW_NUMBER() OVER (ORDER BY filtered_results.similarity) as rank
    FROM filtered_results
    ORDER BY similarity
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Test the search function
SELECT * FROM search_books('machine learning', 'AI', 60.00, NULL, 3.5, TRUE, 5);
```

#### Content Recommendation System

```sql
-- Create a recommendation system based on user preferences
CREATE OR REPLACE FUNCTION recommend_books(
    user_liked_book TEXT,
    diversify_categories BOOLEAN DEFAULT TRUE,
    exclude_expensive BOOLEAN DEFAULT TRUE,
    max_results INTEGER DEFAULT 15
)
RETURNS TABLE(
    recommended_book TEXT,
    category TEXT,
    price TEXT,
    similarity_score NUMERIC,
    recommendation_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_preference AS (
        SELECT embedding, subject, metadata
        FROM items
        WHERE name ILIKE '%' || user_liked_book || '%'
        LIMIT 1
    ),
    similar_books AS (
        SELECT 
            i.name,
            i.subject,
            i.metadata->>'price' as price,
            i.embedding <=> (SELECT embedding FROM user_preference) as similarity,
            CASE 
                WHEN i.subject = (SELECT subject FROM user_preference) THEN 'Same category'
                WHEN i.embedding <=> (SELECT embedding FROM user_preference) < 0.3 THEN 'Highly similar content'
                WHEN (i.metadata->>'rating')::NUMERIC > 4.5 THEN 'Highly rated'
                ELSE 'Related content'
            END as reason
        FROM items i, user_preference
        WHERE i.name != user_liked_book
          AND (NOT exclude_expensive OR (i.metadata->>'price')::NUMERIC < 70)
    ),
    diversified_results AS (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY CASE WHEN diversify_categories THEN subject ELSE 1 END 
                ORDER BY similarity
            ) as category_rank
        FROM similar_books
    )
    SELECT 
        name,
        subject,
        price,
        similarity,
        reason
    FROM diversified_results
    WHERE category_rank <= CASE WHEN diversify_categories THEN 3 ELSE max_results END
    ORDER BY similarity
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Test the recommendation system
SELECT * FROM recommend_books('Python Programming', TRUE, TRUE, 10);
```

## Advanced Hybrid Query Patterns

### 1. Multi-Stage Filtering

```sql
-- Progressive filtering for better performance
WITH stage1_filter AS (
    -- Fast relational filter first
    SELECT id, name, subject, metadata, embedding
    FROM items
    WHERE subject IN ('Programming', 'AI', 'Data Science')
      AND created_at > NOW() - INTERVAL '3 years'
),
stage2_filter AS (
    -- JSONB filtering on reduced dataset
    SELECT *
    FROM stage1_filter
    WHERE (metadata->>'price')::NUMERIC BETWEEN 20 AND 80
      AND (metadata->>'stock')::INTEGER > 10
),
stage3_similarity AS (
    -- Vector similarity on final filtered set
    SELECT *,
        embedding <=> (
            SELECT embedding FROM items 
            WHERE name ILIKE '%deep learning%' 
            LIMIT 1
        ) as similarity
    FROM stage2_filter
)
SELECT name, subject, metadata->>'price' as price, similarity
FROM stage3_similarity
ORDER BY similarity
LIMIT 10;
```

### 2. Faceted Search

```sql
-- Build faceted search results
WITH search_base AS (
    SELECT *,
        embedding <=> (
            SELECT embedding FROM items 
            WHERE name ILIKE '%web development%' 
            LIMIT 1
        ) as similarity
    FROM items
    WHERE subject IN ('Web Development', 'Programming')
),
facet_counts AS (
    SELECT 
        'format' as facet_type,
        metadata->>'format' as facet_value,
        COUNT(*) as count
    FROM search_base
    WHERE similarity < 0.5
    GROUP BY metadata->>'format'
    
    UNION ALL
    
    SELECT 
        'price_range' as facet_type,
        CASE 
            WHEN (metadata->>'price')::NUMERIC < 30 THEN 'Under $30'
            WHEN (metadata->>'price')::NUMERIC < 50 THEN '$30-$50'
            WHEN (metadata->>'price')::NUMERIC < 80 THEN '$50-$80'
            ELSE 'Over $80'
        END as facet_value,
        COUNT(*) as count
    FROM search_base
    WHERE similarity < 0.5
    GROUP BY 
        CASE 
            WHEN (metadata->>'price')::NUMERIC < 30 THEN 'Under $30'
            WHEN (metadata->>'price')::NUMERIC < 50 THEN '$30-$50'
            WHEN (metadata->>'price')::NUMERIC < 80 THEN '$50-$80'
            ELSE 'Over $80'
        END
    
    UNION ALL
    
    SELECT 
        'publisher' as facet_type,
        metadata->>'publisher' as facet_value,
        COUNT(*) as count
    FROM search_base
    WHERE similarity < 0.5
    GROUP BY metadata->>'publisher'
)
SELECT facet_type, facet_value, count
FROM facet_counts
WHERE count > 0
ORDER BY facet_type, count DESC;
```

### 3. Personalized Ranking

```sql
-- Personalized ranking based on user behavior
CREATE TEMP TABLE user_interactions AS
SELECT * FROM (VALUES
    ('Python Crash Course', 'view', 5),
    ('Clean Code', 'purchase', 10),
    ('JavaScript: The Good Parts', 'view', 3),
    ('Design Patterns', 'bookmark', 7)
) AS t(book_name, interaction_type, weight);

WITH user_profile AS (
    SELECT 
        AVG(CASE WHEN ui.interaction_type = 'purchase' THEN 1.0 ELSE 0.5 END) as engagement_score,
        string_agg(DISTINCT i.subject, ',') as preferred_subjects,
        AVG((i.metadata->>'price')::NUMERIC) as avg_price_preference
    FROM user_interactions ui
    JOIN items i ON i.name ILIKE '%' || ui.book_name || '%'
),
personalized_search AS (
    SELECT 
        i.name,
        i.subject,
        i.metadata,
        embedding <=> (
            SELECT embedding FROM items 
            WHERE name ILIKE '%software engineering%' 
            LIMIT 1
        ) as base_similarity,
        CASE 
            WHEN i.subject = ANY(string_to_array((SELECT preferred_subjects FROM user_profile), ','))
            THEN 0.9 -- Boost preferred subjects
            ELSE 1.0
        END as subject_boost,
        CASE 
            WHEN ABS((i.metadata->>'price')::NUMERIC - (SELECT avg_price_preference FROM user_profile)) < 10
            THEN 0.95 -- Boost similar price range
            ELSE 1.0
        END as price_boost
    FROM items i, user_profile
    WHERE i.subject IN ('Programming', 'Web Development', 'Database')
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    base_similarity,
    subject_boost,
    price_boost,
    (base_similarity * subject_boost * price_boost) as personalized_score
FROM personalized_search
ORDER BY personalized_score
LIMIT 10;
```

## Performance Optimization Strategies

### 1. Index Strategy Planning

```sql
-- Analyze query patterns to plan indexes
CREATE OR REPLACE FUNCTION analyze_query_patterns()
RETURNS TABLE(
    pattern_type TEXT,
    frequency INTEGER,
    avg_execution_time NUMERIC,
    recommended_index TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Vector Similarity' as pattern_type,
        100 as frequency,
        1.5 as avg_execution_time,
        'CREATE INDEX items_embedding_ivfflat ON items USING ivfflat (embedding vector_cosine_ops)' as recommended_index
    
    UNION ALL
    
    SELECT 
        'Subject Filter',
        85,
        0.2,
        'CREATE INDEX items_subject_btree ON items (subject)'
    
    UNION ALL
    
    SELECT 
        'Price Range',
        60,
        0.8,
        'CREATE INDEX items_price_btree ON items (((metadata->>''price'')::NUMERIC))'
    
    UNION ALL
    
    SELECT 
        'Format Filter',
        45,
        0.3,
        'CREATE INDEX items_format_btree ON items ((metadata->>''format''))'
    
    UNION ALL
    
    SELECT 
        'Stock Check',
        70,
        0.4,
        'CREATE INDEX items_stock_btree ON items (((metadata->>''stock'')::INTEGER))'
    
    UNION ALL
    
    SELECT 
        'Recent Items',
        30,
        0.6,
        'CREATE INDEX items_created_at_btree ON items (created_at)'
    
    ORDER BY frequency DESC;
END;
$$ LANGUAGE plpgsql;

SELECT * FROM analyze_query_patterns();
```

### 2. Query Optimization Techniques

```sql
-- Optimized hybrid query template
CREATE OR REPLACE FUNCTION optimized_hybrid_search(
    search_term TEXT,
    filters JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE(
    name TEXT,
    subject TEXT,
    price NUMERIC,
    similarity NUMERIC
) AS $$
DECLARE
    query_text TEXT;
    filter_conditions TEXT := '';
BEGIN
    -- Build dynamic filter conditions
    IF filters ? 'subject' THEN
        filter_conditions := filter_conditions || ' AND subject = ' || quote_literal(filters->>'subject');
    END IF;
    
    IF filters ? 'max_price' THEN
        filter_conditions := filter_conditions || ' AND (metadata->>''price'')::NUMERIC <= ' || (filters->>'max_price')::NUMERIC;
    END IF;
    
    IF filters ? 'format' THEN
        filter_conditions := filter_conditions || ' AND metadata->>''format'' = ' || quote_literal(filters->>'format');
    END IF;
    
    IF filters ? 'min_stock' THEN
        filter_conditions := filter_conditions || ' AND (metadata->>''stock'')::INTEGER >= ' || (filters->>'min_stock')::INTEGER;
    END IF;
    
    -- Build optimized query
    query_text := '
        WITH query_vector AS (
            SELECT embedding
            FROM items
            WHERE name ILIKE ' || quote_literal('%' || search_term || '%') || '
            LIMIT 1
        )
        SELECT 
            i.name,
            i.subject,
            (i.metadata->>''price'')::NUMERIC,
            i.embedding <=> (SELECT embedding FROM query_vector)
        FROM items i, query_vector
        WHERE 1=1 ' || filter_conditions || '
        ORDER BY i.embedding <=> (SELECT embedding FROM query_vector)
        LIMIT 20';
    
    RETURN QUERY EXECUTE query_text;
END;
$$ LANGUAGE plpgsql;

-- Test the optimized search
SELECT * FROM optimized_hybrid_search(
    'machine learning',
    '{"subject": "AI", "max_price": 60, "format": "ebook"}'::JSONB
);
```

## Real-World Implementation Examples

### 1. E-commerce Product Search

```sql
-- Complete e-commerce search system
CREATE SCHEMA IF NOT EXISTS ecommerce;

CREATE TABLE ecommerce.search_analytics (
    id SERIAL PRIMARY KEY,
    search_query TEXT,
    filters_applied JSONB,
    results_count INTEGER,
    click_through_rate NUMERIC,
    conversion_rate NUMERIC,
    search_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION ecommerce.product_search(
    user_query TEXT,
    category TEXT DEFAULT NULL,
    price_min NUMERIC DEFAULT NULL,
    price_max NUMERIC DEFAULT NULL,
    format_pref TEXT DEFAULT NULL,
    sort_by TEXT DEFAULT 'relevance'
)
RETURNS TABLE(
    product_id INTEGER,
    product_name TEXT,
    category TEXT,
    price NUMERIC,
    format TEXT,
    stock INTEGER,
    rating NUMERIC,
    relevance_score NUMERIC,
    rank INTEGER
) AS $$
DECLARE
    results_count INTEGER;
BEGIN
    RETURN QUERY
    WITH search_results AS (
        SELECT 
            i.id,
            i.name,
            i.subject,
            (i.metadata->>'price')::NUMERIC as prod_price,
            i.metadata->>'format' as prod_format,
            (i.metadata->>'stock')::INTEGER as prod_stock,
            (i.metadata->>'rating')::NUMERIC as prod_rating,
            CASE 
                WHEN sort_by = 'relevance' THEN
                    i.embedding <=> (
                        SELECT embedding FROM items 
                        WHERE name ILIKE '%' || user_query || '%' 
                        LIMIT 1
                    )
                ELSE 1.0
            END as relevance
        FROM items i
        WHERE (category IS NULL OR i.subject = category)
          AND (price_min IS NULL OR (i.metadata->>'price')::NUMERIC >= price_min)
          AND (price_max IS NULL OR (i.metadata->>'price')::NUMERIC <= price_max)
          AND (format_pref IS NULL OR i.metadata->>'format' = format_pref)
          AND (i.metadata->>'stock')::INTEGER > 0
    )
    SELECT 
        sr.id,
        sr.name,
        sr.subject,
        sr.prod_price,
        sr.prod_format,
        sr.prod_stock,
        sr.prod_rating,
        sr.relevance,
        ROW_NUMBER() OVER (
            ORDER BY 
                CASE sort_by
                    WHEN 'relevance' THEN sr.relevance
                    WHEN 'price_asc' THEN sr.prod_price
                    WHEN 'price_desc' THEN -sr.prod_price
                    WHEN 'rating' THEN -sr.prod_rating
                    ELSE sr.relevance
                END
        )
    FROM search_results sr
    ORDER BY 
        CASE sort_by
            WHEN 'relevance' THEN sr.relevance
            WHEN 'price_asc' THEN sr.prod_price
            WHEN 'price_desc' THEN -sr.prod_price
            WHEN 'rating' THEN -sr.prod_rating
            ELSE sr.relevance
        END
    LIMIT 50;
    
    -- Log search analytics
    GET DIAGNOSTICS results_count = ROW_COUNT;
    INSERT INTO ecommerce.search_analytics (search_query, filters_applied, results_count)
    VALUES (user_query, jsonb_build_object(
        'category', category,
        'price_min', price_min,
        'price_max', price_max,
        'format', format_pref,
        'sort_by', sort_by
    ), results_count);
END;
$$ LANGUAGE plpgsql;
```

### 2. Content Discovery Platform

```sql
-- Content recommendation engine
CREATE OR REPLACE FUNCTION discover_content(
    user_id INTEGER,
    content_type TEXT DEFAULT NULL,
    discovery_mode TEXT DEFAULT 'balanced' -- 'popular', 'similar', 'diverse', 'balanced'
)
RETURNS TABLE(
    content_id INTEGER,
    title TEXT,
    category TEXT,
    discovery_reason TEXT,
    confidence_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH user_history AS (
        -- Simulate user interaction history
        SELECT embedding, subject
        FROM items
        WHERE (metadata->>'rating')::NUMERIC > 4.0
        ORDER BY random()
        LIMIT 3
    ),
    content_scores AS (
        SELECT 
            i.id,
            i.name,
            i.subject,
            CASE discovery_mode
                WHEN 'popular' THEN (i.metadata->>'rating')::NUMERIC / 5.0
                WHEN 'similar' THEN 1.0 - AVG(i.embedding <=> uh.embedding)
                WHEN 'diverse' THEN 
                    CASE WHEN i.subject NOT IN (SELECT DISTINCT subject FROM user_history) 
                    THEN 0.8 ELSE 0.3 END
                ELSE -- balanced
                    ((i.metadata->>'rating')::NUMERIC / 5.0 * 0.3) +
                    ((1.0 - AVG(i.embedding <=> uh.embedding)) * 0.5) +
                    (CASE WHEN i.subject NOT IN (SELECT DISTINCT subject FROM user_history) 
                     THEN 0.2 ELSE 0.1 END)
            END as score,
            CASE discovery_mode
                WHEN 'popular' THEN 'Highly rated content'
                WHEN 'similar' THEN 'Similar to your interests'
                WHEN 'diverse' THEN 'Explore new topics'
                ELSE 'Recommended for you'
            END as reason
        FROM items i
        CROSS JOIN user_history uh
        WHERE (content_type IS NULL OR i.subject = content_type)
          AND (i.metadata->>'stock')::INTEGER > 0
        GROUP BY i.id, i.name, i.subject, i.metadata
    )
    SELECT 
        cs.id,
        cs.name,
        cs.subject,
        cs.reason,
        cs.score
    FROM content_scores cs
    ORDER BY cs.score DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- Test content discovery
SELECT * FROM discover_content(1, NULL, 'balanced');
```

## Troubleshooting and Optimization

### Common Performance Issues

```sql
-- Identify slow queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
WHERE query ILIKE '%embedding%'
   OR query ILIKE '%metadata%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'items'
ORDER BY idx_scan DESC;

-- Analyze table statistics
ANALYZE items;

-- Check for missing indexes
SELECT 
    'Missing index on subject' as recommendation
WHERE NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE tablename = 'items' AND indexdef ILIKE '%subject%'
)
UNION ALL
SELECT 
    'Missing JSONB index on metadata' as recommendation
WHERE NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE tablename = 'items' AND indexdef ILIKE '%gin%metadata%'
);
```

### Query Optimization Checklist

1. **Index Strategy**
   - ✅ Vector index for similarity searches
   - ✅ JSONB GIN index for metadata queries
   - ✅ B-tree indexes for exact matches
   - ✅ Composite indexes for common filter combinations

2. **Query Structure**
   - ✅ Filter early with fast conditions
   - ✅ Use CTEs for complex multi-stage queries
   - ✅ Limit result sets appropriately
   - ✅ Avoid unnecessary JSONB operations

3. **Data Organization**
   - ✅ Normalize frequently-queried JSONB fields
   - ✅ Use appropriate data types
   - ✅ Regular VACUUM and ANALYZE
   - ✅ Monitor table bloat

## Success Criteria

You've completed the lab when you can:

1. ✅ **Combine Multiple Data Types** - Write queries that integrate vector, relational, and JSONB data
2. ✅ **Optimize Query Performance** - Create appropriate indexes and structure queries efficiently
3. ✅ **Build Real-World Applications** - Implement search systems that solve practical problems
4. ✅ **Handle Complex Filtering** - Apply multiple criteria across different data types
5. ✅ **Understand Trade-offs** - Choose the right approach for different use cases
6. ✅ **Debug Performance Issues** - Identify and resolve slow query problems

## Next Steps

Once you master hybrid queries:

1. **Advanced Vector Operations** - Explore more sophisticated embedding techniques
2. **Real-time Search** - Build responsive search interfaces
3. **Machine Learning Integration** - Incorporate ML models for ranking and personalization
4. **Distributed Search** - Scale across multiple databases
5. **Search Analytics** - Build comprehensive search analytics systems

## Key Insights

After completing this lab, you should understand:

1. **Hybrid queries unlock powerful search capabilities** by combining the strengths of different data paradigms
2. **Index strategy is critical** for performance - each data type requires different indexing approaches
3. **Query structure matters** - filtering early and using appropriate operators can dramatically improve performance
4. **Real-world applications require flexibility** - configuration-driven approaches enable rapid iteration
5. **Performance monitoring is essential** - complex queries need ongoing optimization

Remember: **The best search experience combines semantic understanding with business logic and user preferences!** 
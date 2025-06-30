-- ============================================================================
-- Hybrid Query Workshop: Vector + Relational + JSONB Integration
-- Master advanced PostgreSQL queries combining multiple data paradigms
-- ============================================================================

-- Connect to your PostgreSQL database first:
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- ============================================================================
-- SECTION 1: SETUP AND SCHEMA ENHANCEMENT
-- ============================================================================

-- Enhance the existing items table for hybrid queries
ALTER TABLE items ADD COLUMN IF NOT EXISTS subject TEXT;
ALTER TABLE items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE items ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Verify the enhanced schema
\d items

-- ============================================================================
-- SECTION 2: GENERATE ENHANCED SAMPLE DATA
-- ============================================================================

-- Update existing items with categorized data and metadata
UPDATE items SET 
    subject = CASE 
        WHEN item_data::text ILIKE '%programming%' OR item_data::text ILIKE '%code%' THEN 'Programming'
        WHEN item_data::text ILIKE '%ai%' OR item_data::text ILIKE '%artificial%' OR item_data::text ILIKE '%machine%' THEN 'AI'
        WHEN item_data::text ILIKE '%data%' OR item_data::text ILIKE '%science%' THEN 'Data Science'
        WHEN item_data::text ILIKE '%web%' OR item_data::text ILIKE '%javascript%' OR item_data::text ILIKE '%html%' THEN 'Web Development'
        WHEN item_data::text ILIKE '%database%' OR item_data::text ILIKE '%sql%' THEN 'Database'
        WHEN item_data::text ILIKE '%design%' OR item_data::text ILIKE '%ui%' OR item_data::text ILIKE '%ux%' THEN 'Design'
        WHEN item_data::text ILIKE '%business%' OR item_data::text ILIKE '%management%' THEN 'Business'
        ELSE 'General'
    END,
    created_at = NOW() - (random() * interval '365 days'),
    metadata = jsonb_build_object(
        'price', round((random() * 90 + 10)::numeric, 2),
        'stock', floor(random() * 500 + 5)::integer,
        'format', (ARRAY['ebook', 'paperback', 'hardcover'])[floor(random() * 3 + 1)],
        'rating', round((random() * 2 + 3)::numeric, 1),
        'pages', floor(random() * 400 + 100)::integer,
        'publisher', (ARRAY['Tech Books', 'O''Reilly', 'Manning', 'Packt', 'Apress', 'MIT Press'])[floor(random() * 6 + 1)],
        'language', 'English',
        'isbn', '978-' || floor(random() * 9000000000 + 1000000000)::text,
        'difficulty', (ARRAY['Beginner', 'Intermediate', 'Advanced'])[floor(random() * 3 + 1)],
        'tags', CASE floor(random() * 4)
            WHEN 0 THEN '["bestseller"]'::jsonb
            WHEN 1 THEN '["new-release"]'::jsonb
            WHEN 2 THEN '["bestseller", "award-winner"]'::jsonb
            ELSE '["recommended"]'::jsonb
        END
    )
WHERE subject IS NULL OR metadata IS NULL;

-- Verify the enhanced data
SELECT 
    name, 
    subject, 
    metadata->>'price' as price, 
    metadata->>'format' as format,
    metadata->>'rating' as rating,
    created_at::date as created_date
FROM items
LIMIT 10;

-- Show data distribution by subject
SELECT subject, COUNT(*) as count
FROM items
GROUP BY subject
ORDER BY count DESC;

-- ============================================================================
-- SECTION 3: BASIC HYBRID QUERIES
-- ============================================================================

-- Exercise 3.1: Vector Search with Relational Filtering
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
    metadata->>'format' as format,
    embedding <=> (SELECT embedding FROM query_vector) as similarity
FROM items, query_vector
WHERE subject = 'Programming'
ORDER BY embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;

-- Exercise 3.2: Vector Search with JSONB Filtering
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
    embedding <=> (SELECT embedding FROM query_vector) as similarity
FROM items, query_vector
WHERE (metadata->>'price')::NUMERIC < 50
  AND (metadata->>'stock')::INTEGER > 20
ORDER BY embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;

-- Exercise 3.3: Multi-Criteria Hybrid Search
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
    created_at::date as created_date,
    embedding <=> (SELECT embedding FROM query_vector) as similarity
FROM items, query_vector
WHERE subject = 'AI'
  AND metadata->>'format' = 'ebook'
  AND (metadata->>'price')::NUMERIC < 40
  AND created_at > NOW() - INTERVAL '2 years'
ORDER BY embedding <=> (SELECT embedding FROM query_vector)
LIMIT 5;

-- Exercise 3.4: Format-Based Search
-- Find all paperback books in specific categories
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'publisher' as publisher,
    metadata->>'pages' as pages
FROM items
WHERE metadata->>'format' = 'paperback'
  AND subject IN ('Programming', 'Data Science', 'AI')
  AND (metadata->>'stock')::INTEGER > 0
ORDER BY (metadata->>'rating')::NUMERIC DESC
LIMIT 15;

-- ============================================================================
-- SECTION 4: ADVANCED HYBRID PATTERNS
-- ============================================================================

-- Exercise 4.1: Weighted Scoring
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
        embedding <=> (SELECT embedding FROM query_vector) as similarity,
        (metadata->>'rating')::NUMERIC as rating,
        CASE 
            WHEN (metadata->>'stock')::INTEGER > 100 THEN 1.0
            WHEN (metadata->>'stock')::INTEGER > 50 THEN 0.8
            WHEN (metadata->>'stock')::INTEGER > 10 THEN 0.6
            ELSE 0.3
        END as stock_score,
        CASE metadata->>'difficulty'
            WHEN 'Beginner' THEN 0.9
            WHEN 'Intermediate' THEN 1.0
            WHEN 'Advanced' THEN 0.8
        END as difficulty_score
    FROM items, query_vector
    WHERE subject IN ('AI', 'Data Science', 'Programming')
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'difficulty' as difficulty,
    similarity,
    rating,
    stock_score,
    difficulty_score,
    -- Composite score: similarity (30%) + rating (30%) + stock (20%) + difficulty (20%)
    (similarity * 0.3 + (5 - rating) * 0.3 + (1 - stock_score) * 0.2 + (1 - difficulty_score) * 0.2) as composite_score
FROM scored_results
ORDER BY composite_score ASC
LIMIT 10;

-- Exercise 4.2: Category-Based Recommendations
-- Find books similar within category, then expand to related categories
WITH user_query AS (
    SELECT embedding, subject
    FROM items
    WHERE name ILIKE '%python programming%'
    LIMIT 1
),
same_category AS (
    SELECT 
        name, subject, metadata, 
        embedding <=> (SELECT embedding FROM user_query) as similarity,
        'same_category' as match_type,
        1 as priority
    FROM items, user_query
    WHERE subject = (SELECT subject FROM user_query)
    ORDER BY embedding <=> (SELECT embedding FROM user_query)
    LIMIT 5
),
related_categories AS (
    SELECT 
        name, subject, metadata,
        embedding <=> (SELECT embedding FROM user_query) as similarity,
        'related_category' as match_type,
        2 as priority
    FROM items, user_query
    WHERE subject IN ('Web Development', 'Data Science', 'Database')
      AND subject != (SELECT subject FROM user_query)
    ORDER BY embedding <=> (SELECT embedding FROM user_query)
    LIMIT 3
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'rating' as rating,
    similarity,
    match_type
FROM same_category
UNION ALL
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'rating' as rating,
    similarity,
    match_type
FROM related_categories
ORDER BY priority, similarity;

-- Exercise 4.3: Tag-Based Discovery
-- Find books with specific tags and similar content
WITH tagged_books AS (
    SELECT 
        name,
        subject,
        metadata,
        embedding,
        CASE 
            WHEN metadata->'tags' @> '["bestseller"]' THEN 'bestseller'
            WHEN metadata->'tags' @> '["new-release"]' THEN 'new-release'
            WHEN metadata->'tags' @> '["award-winner"]' THEN 'award-winner'
            ELSE 'standard'
        END as tag_category
    FROM items
    WHERE metadata ? 'tags'
),
query_embedding AS (
    SELECT embedding
    FROM items
    WHERE name ILIKE '%web development%'
    LIMIT 1
)
SELECT 
    tb.name,
    tb.subject,
    tb.metadata->>'price' as price,
    tb.tag_category,
    tb.embedding <=> (SELECT embedding FROM query_embedding) as similarity
FROM tagged_books tb, query_embedding
WHERE tb.tag_category IN ('bestseller', 'award-winner')
ORDER BY tb.embedding <=> (SELECT embedding FROM query_embedding)
LIMIT 12;

-- ============================================================================
-- SECTION 5: PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Create comprehensive indexes for hybrid queries
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

CREATE INDEX IF NOT EXISTS items_rating_idx 
ON items USING BTREE (((metadata->>'rating')::NUMERIC));

-- Partial indexes for common scenarios
CREATE INDEX IF NOT EXISTS items_in_stock_idx 
ON items (subject, ((metadata->>'price')::NUMERIC))
WHERE (metadata->>'stock')::INTEGER > 0;

CREATE INDEX IF NOT EXISTS items_high_rated_idx 
ON items USING GIN (metadata)
WHERE (metadata->>'rating')::NUMERIC >= 4.0;

-- Show all indexes on items table
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'items'
ORDER BY indexname;

-- ============================================================================
-- SECTION 6: QUERY PERFORMANCE ANALYSIS
-- ============================================================================

-- Analyze query performance with EXPLAIN
EXPLAIN (ANALYZE, BUFFERS) 
WITH query_vector AS (
    SELECT embedding FROM items WHERE name ILIKE '%python%' LIMIT 1
)
SELECT name, subject, metadata->>'price' as price
FROM items, query_vector
WHERE subject = 'Programming'
  AND (metadata->>'price')::NUMERIC < 50
ORDER BY embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;

-- Compare different query approaches
-- Approach 1: Filter first, then similarity
EXPLAIN (ANALYZE, BUFFERS)
WITH filtered_items AS (
    SELECT * FROM items
    WHERE subject = 'Programming'
      AND (metadata->>'price')::NUMERIC < 50
      AND (metadata->>'stock')::INTEGER > 10
),
query_vector AS (
    SELECT embedding FROM items WHERE name ILIKE '%python%' LIMIT 1
)
SELECT fi.name, fi.subject, fi.metadata->>'price'
FROM filtered_items fi, query_vector
ORDER BY fi.embedding <=> (SELECT embedding FROM query_vector)
LIMIT 10;

-- Approach 2: Similarity first, then filter
EXPLAIN (ANALYZE, BUFFERS)
WITH query_vector AS (
    SELECT embedding FROM items WHERE name ILIKE '%python%' LIMIT 1
),
similar_items AS (
    SELECT *
    FROM items, query_vector
    ORDER BY embedding <=> (SELECT embedding FROM query_vector)
    LIMIT 100
)
SELECT si.name, si.subject, si.metadata->>'price'
FROM similar_items si
WHERE si.subject = 'Programming'
  AND (si.metadata->>'price')::NUMERIC < 50
  AND (si.metadata->>'stock')::INTEGER > 10
LIMIT 10;

-- ============================================================================
-- SECTION 7: REAL-WORLD APPLICATION FUNCTIONS
-- ============================================================================

-- Create a comprehensive book search function
CREATE OR REPLACE FUNCTION search_books(
    search_query TEXT,
    category_filter TEXT DEFAULT NULL,
    max_price NUMERIC DEFAULT NULL,
    format_filter TEXT DEFAULT NULL,
    min_rating NUMERIC DEFAULT NULL,
    difficulty_level TEXT DEFAULT NULL,
    in_stock_only BOOLEAN DEFAULT FALSE,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    book_name TEXT,
    category TEXT,
    price NUMERIC,
    format TEXT,
    rating NUMERIC,
    difficulty TEXT,
    stock INTEGER,
    similarity_score NUMERIC,
    relevance_rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH query_embedding AS (
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
            i.metadata->>'difficulty' as book_difficulty,
            (i.metadata->>'stock')::INTEGER as book_stock,
            i.embedding <=> (SELECT embedding FROM query_embedding) as similarity
        FROM items i, query_embedding
        WHERE (category_filter IS NULL OR i.subject = category_filter)
          AND (max_price IS NULL OR (i.metadata->>'price')::NUMERIC <= max_price)
          AND (format_filter IS NULL OR i.metadata->>'format' = format_filter)
          AND (min_rating IS NULL OR (i.metadata->>'rating')::NUMERIC >= min_rating)
          AND (difficulty_level IS NULL OR i.metadata->>'difficulty' = difficulty_level)
          AND (NOT in_stock_only OR (i.metadata->>'stock')::INTEGER > 0)
    )
    SELECT 
        filtered_results.name,
        filtered_results.subject,
        filtered_results.book_price,
        filtered_results.book_format,
        filtered_results.book_rating,
        filtered_results.book_difficulty,
        filtered_results.book_stock,
        filtered_results.similarity,
        ROW_NUMBER() OVER (ORDER BY filtered_results.similarity) as rank
    FROM filtered_results
    ORDER BY similarity
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Test the search function
SELECT * FROM search_books('machine learning', 'AI', 60.00, NULL, 3.5, NULL, TRUE, 5);

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
    rating NUMERIC,
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
            (i.metadata->>'rating')::NUMERIC as rating,
            i.embedding <=> (SELECT embedding FROM user_preference) as similarity,
            CASE 
                WHEN i.subject = (SELECT subject FROM user_preference) THEN 'Same category'
                WHEN i.embedding <=> (SELECT embedding FROM user_preference) < 0.3 THEN 'Highly similar content'
                WHEN (i.metadata->>'rating')::NUMERIC > 4.5 THEN 'Highly rated'
                WHEN i.metadata->'tags' @> '["bestseller"]' THEN 'Bestseller'
                ELSE 'Related content'
            END as reason
        FROM items i, user_preference
        WHERE i.name != user_liked_book
          AND (NOT exclude_expensive OR (i.metadata->>'price')::NUMERIC < 70)
          AND (i.metadata->>'stock')::INTEGER > 0
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
        rating,
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

-- ============================================================================
-- SECTION 8: ADVANCED ANALYTICS QUERIES
-- ============================================================================

-- Multi-Stage Filtering for Better Performance
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
SELECT 
    name, 
    subject, 
    metadata->>'price' as price, 
    metadata->>'rating' as rating,
    similarity
FROM stage3_similarity
ORDER BY similarity
LIMIT 10;

-- Faceted Search Results
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
        'difficulty' as facet_type,
        metadata->>'difficulty' as facet_value,
        COUNT(*) as count
    FROM search_base
    WHERE similarity < 0.5
    GROUP BY metadata->>'difficulty'
    
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

-- ============================================================================
-- SECTION 9: PERSONALIZED RANKING
-- ============================================================================

-- Simulate user interaction data
CREATE TEMP TABLE user_interactions AS
SELECT * FROM (VALUES
    ('Python Crash Course', 'view', 5),
    ('Clean Code', 'purchase', 10),
    ('JavaScript: The Good Parts', 'view', 3),
    ('Design Patterns', 'bookmark', 7),
    ('Machine Learning Yearning', 'purchase', 10),
    ('Deep Learning', 'view', 8)
) AS t(book_name, interaction_type, weight);

-- Personalized search based on user behavior
WITH user_profile AS (
    SELECT 
        AVG(CASE WHEN ui.interaction_type = 'purchase' THEN 1.0 ELSE 0.5 END) as engagement_score,
        string_agg(DISTINCT i.subject, ',') as preferred_subjects,
        AVG((i.metadata->>'price')::NUMERIC) as avg_price_preference,
        AVG((i.metadata->>'rating')::NUMERIC) as avg_rating_preference
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
        END as price_boost,
        CASE 
            WHEN (i.metadata->>'rating')::NUMERIC >= (SELECT avg_rating_preference FROM user_profile)
            THEN 0.9 -- Boost high-rated books
            ELSE 1.0
        END as rating_boost
    FROM items i, user_profile
    WHERE i.subject IN ('Programming', 'Web Development', 'Database', 'AI')
      AND (i.metadata->>'stock')::INTEGER > 0
)
SELECT 
    name,
    subject,
    metadata->>'price' as price,
    metadata->>'rating' as rating,
    base_similarity,
    subject_boost,
    price_boost,
    rating_boost,
    (base_similarity * subject_boost * price_boost * rating_boost) as personalized_score
FROM personalized_search
ORDER BY personalized_score
LIMIT 15;

-- ============================================================================
-- SECTION 10: PERFORMANCE MONITORING AND OPTIMIZATION
-- ============================================================================

-- Function to analyze query patterns
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
        'Stock Check',
        70,
        0.4,
        'CREATE INDEX items_stock_btree ON items (((metadata->>''stock'')::INTEGER))'
    
    UNION ALL
    
    SELECT 
        'Format Filter',
        45,
        0.3,
        'CREATE INDEX items_format_btree ON items ((metadata->>''format''))'
    
    UNION ALL
    
    SELECT 
        'Rating Filter',
        55,
        0.5,
        'CREATE INDEX items_rating_btree ON items (((metadata->>''rating'')::NUMERIC))'
    
    ORDER BY frequency DESC;
END;
$$ LANGUAGE plpgsql;

-- Analyze current query patterns
SELECT * FROM analyze_query_patterns();

-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'items'
ORDER BY idx_scan DESC;

-- Identify potential missing indexes
SELECT 
    'Consider adding composite index on (subject, price)' as recommendation
WHERE NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE tablename = 'items' 
    AND indexdef ILIKE '%subject%' 
    AND indexdef ILIKE '%price%'
)
UNION ALL
SELECT 
    'Consider adding partial index for in-stock items' as recommendation
WHERE NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE tablename = 'items' 
    AND indexdef ILIKE '%stock%'
    AND indexdef ILIKE '%WHERE%'
);

-- ============================================================================
-- SECTION 11: CLEANUP AND SUMMARY
-- ============================================================================

-- Clean up temporary tables
DROP TABLE IF EXISTS user_interactions;

-- Summary statistics
SELECT 
    'Hybrid Query Workshop Summary' as section,
    jsonb_build_object(
        'total_items', COUNT(*),
        'categories', COUNT(DISTINCT subject),
        'avg_price', ROUND(AVG((metadata->>'price')::NUMERIC), 2),
        'formats_available', COUNT(DISTINCT metadata->>'format'),
        'price_range', jsonb_build_object(
            'min', MIN((metadata->>'price')::NUMERIC),
            'max', MAX((metadata->>'price')::NUMERIC)
        ),
        'rating_distribution', jsonb_build_object(
            'avg', ROUND(AVG((metadata->>'rating')::NUMERIC), 2),
            'high_rated_count', COUNT(*) FILTER (WHERE (metadata->>'rating')::NUMERIC >= 4.0)
        )
    ) as statistics
FROM items;

-- Show sample hybrid query for reference
SELECT 
    '-- Sample Hybrid Query Template' as query_template
UNION ALL
SELECT 
    'WITH query_vector AS ('
UNION ALL
SELECT 
    '    SELECT embedding FROM items WHERE name ILIKE ''%your_search%'' LIMIT 1'
UNION ALL
SELECT 
    ')'
UNION ALL
SELECT 
    'SELECT name, subject, metadata->>''price'' as price,'
UNION ALL
SELECT 
    '       embedding <=> (SELECT embedding FROM query_vector) as similarity'
UNION ALL
SELECT 
    'FROM items, query_vector'
UNION ALL
SELECT 
    'WHERE subject = ''YourCategory'''
UNION ALL
SELECT 
    '  AND (metadata->>''price'')::NUMERIC < 50'
UNION ALL
SELECT 
    '  AND (metadata->>''stock'')::INTEGER > 0'
UNION ALL
SELECT 
    'ORDER BY embedding <=> (SELECT embedding FROM query_vector)'
UNION ALL
SELECT 
    'LIMIT 10;';

-- ============================================================================
-- WORKSHOP COMPLETE!
-- ============================================================================

-- Congratulations! You've completed the Hybrid Query workshop.
--
-- Key concepts covered:
-- 1. ✅ Vector similarity search with relational filtering
-- 2. ✅ JSONB metadata integration with vector operations
-- 3. ✅ Advanced scoring and ranking algorithms
-- 4. ✅ Performance optimization with appropriate indexing
-- 5. ✅ Real-world application patterns and functions
-- 6. ✅ Personalized search and recommendation systems
-- 7. ✅ Query performance analysis and optimization
--
-- Skills you've mastered:
-- - Combining multiple data paradigms in single queries
-- - Building sophisticated search and recommendation systems
-- - Optimizing complex hybrid queries for performance
-- - Creating reusable search functions for applications
-- - Understanding trade-offs between different query approaches
--
-- Next steps:
-- 1. Experiment with your own data and search scenarios
-- 2. Build a complete search API using these patterns
-- 3. Explore advanced vector operations and embedding techniques
-- 4. Implement real-time search with caching strategies
-- 5. Scale these patterns for production workloads 
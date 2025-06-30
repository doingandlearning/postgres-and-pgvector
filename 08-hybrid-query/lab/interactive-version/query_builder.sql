-- ============================================================================
-- Hybrid Query Builder
-- Interactive tool for constructing complex hybrid queries step by step
-- ============================================================================

-- Connect to your PostgreSQL database first:
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- ============================================================================
-- QUERY BUILDER FUNCTIONS
-- ============================================================================

-- Function to build dynamic hybrid queries
CREATE OR REPLACE FUNCTION build_hybrid_query(
    search_term TEXT DEFAULT NULL,
    similarity_threshold NUMERIC DEFAULT 1.0,
    category_filter TEXT DEFAULT NULL,
    price_min NUMERIC DEFAULT NULL,
    price_max NUMERIC DEFAULT NULL,
    format_filter TEXT DEFAULT NULL,
    rating_min NUMERIC DEFAULT NULL,
    stock_min INTEGER DEFAULT NULL,
    difficulty_filter TEXT DEFAULT NULL,
    publisher_filter TEXT DEFAULT NULL,
    max_age_days INTEGER DEFAULT NULL,
    sort_by TEXT DEFAULT 'similarity',
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    query_description TEXT,
    book_title TEXT,
    category TEXT,
    price NUMERIC,
    format TEXT,
    rating NUMERIC,
    stock INTEGER,
    difficulty TEXT,
    publisher TEXT,
    age_days INTEGER,
    similarity_score NUMERIC
) AS $$
DECLARE
    base_query TEXT;
    where_conditions TEXT[] := '{}';
    order_clause TEXT;
    final_query TEXT;
BEGIN
    -- Build WHERE conditions dynamically
    IF category_filter IS NOT NULL THEN
        where_conditions := array_append(where_conditions, 'i.subject = ' || quote_literal(category_filter));
    END IF;
    
    IF price_min IS NOT NULL THEN
        where_conditions := array_append(where_conditions, '(i.metadata->>''price'')::NUMERIC >= ' || price_min);
    END IF;
    
    IF price_max IS NOT NULL THEN
        where_conditions := array_append(where_conditions, '(i.metadata->>''price'')::NUMERIC <= ' || price_max);
    END IF;
    
    IF format_filter IS NOT NULL THEN
        where_conditions := array_append(where_conditions, 'i.metadata->>''format'' = ' || quote_literal(format_filter));
    END IF;
    
    IF rating_min IS NOT NULL THEN
        where_conditions := array_append(where_conditions, '(i.metadata->>''rating'')::NUMERIC >= ' || rating_min);
    END IF;
    
    IF stock_min IS NOT NULL THEN
        where_conditions := array_append(where_conditions, '(i.metadata->>''stock'')::INTEGER >= ' || stock_min);
    END IF;
    
    IF difficulty_filter IS NOT NULL THEN
        where_conditions := array_append(where_conditions, 'i.metadata->>''difficulty'' = ' || quote_literal(difficulty_filter));
    END IF;
    
    IF publisher_filter IS NOT NULL THEN
        where_conditions := array_append(where_conditions, 'i.metadata->>''publisher'' = ' || quote_literal(publisher_filter));
    END IF;
    
    IF max_age_days IS NOT NULL THEN
        where_conditions := array_append(where_conditions, 'i.created_at > NOW() - INTERVAL ''' || max_age_days || ' days''');
    END IF;
    
    -- Build ORDER BY clause
    CASE sort_by
        WHEN 'similarity' THEN order_clause := 'similarity_score';
        WHEN 'price_asc' THEN order_clause := 'price ASC';
        WHEN 'price_desc' THEN order_clause := 'price DESC';
        WHEN 'rating' THEN order_clause := 'rating DESC';
        WHEN 'newest' THEN order_clause := 'age_days ASC';
        WHEN 'oldest' THEN order_clause := 'age_days DESC';
        ELSE order_clause := 'similarity_score';
    END CASE;
    
    -- Construct the final query
    base_query := '
        WITH query_vector AS (
            SELECT embedding
            FROM items
            WHERE ' || CASE 
                WHEN search_term IS NOT NULL THEN 'name ILIKE ' || quote_literal('%' || search_term || '%')
                ELSE 'TRUE'
            END || '
            ORDER BY random()
            LIMIT 1
        )
        SELECT 
            ''Hybrid Search Results'' as query_description,
            i.name as book_title,
            i.subject as category,
            (i.metadata->>''price'')::NUMERIC as price,
            i.metadata->>''format'' as format,
            (i.metadata->>''rating'')::NUMERIC as rating,
            (i.metadata->>''stock'')::INTEGER as stock,
            i.metadata->>''difficulty'' as difficulty,
            i.metadata->>''publisher'' as publisher,
            EXTRACT(DAYS FROM NOW() - i.created_at)::INTEGER as age_days,
            ' || CASE 
                WHEN search_term IS NOT NULL THEN 'i.embedding <=> (SELECT embedding FROM query_vector)'
                ELSE '0.5'
            END || ' as similarity_score
        FROM items i' || 
        CASE WHEN search_term IS NOT NULL THEN ', query_vector' ELSE '' END || '
        WHERE ' || CASE 
            WHEN search_term IS NOT NULL THEN 'i.embedding <=> (SELECT embedding FROM query_vector) <= ' || similarity_threshold
            ELSE 'TRUE'
        END;
    
    -- Add WHERE conditions
    IF array_length(where_conditions, 1) > 0 THEN
        base_query := base_query || ' AND ' || array_to_string(where_conditions, ' AND ');
    END IF;
    
    -- Add ORDER BY and LIMIT
    final_query := base_query || ' ORDER BY ' || order_clause || ' LIMIT ' || result_limit;
    
    -- Execute and return results
    RETURN QUERY EXECUTE final_query;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- QUERY TEMPLATES
-- ============================================================================

-- Template 1: Basic Similarity Search
SELECT 
    'Template 1: Basic Similarity Search' as template_name,
    'Find books similar to a search term' as description,
    'SELECT * FROM build_hybrid_query(search_term := ''python programming'');' as example_usage;

-- Template 2: Category-Focused Search
SELECT 
    'Template 2: Category-Focused Search' as template_name,
    'Search within specific categories with filters' as description,
    'SELECT * FROM build_hybrid_query(
        search_term := ''machine learning'',
        category_filter := ''AI'',
        rating_min := 4.0,
        result_limit := 5
    );' as example_usage;

-- Template 3: Budget-Conscious Search
SELECT 
    'Template 3: Budget-Conscious Search' as template_name,
    'Find affordable books with good value' as description,
    'SELECT * FROM build_hybrid_query(
        category_filter := ''Programming'',
        price_max := 40,
        rating_min := 3.5,
        sort_by := ''price_asc'',
        result_limit := 8
    );' as example_usage;

-- Template 4: Premium Quality Search
SELECT 
    'Template 4: Premium Quality Search' as template_name,
    'Find high-quality, recent publications' as description,
    'SELECT * FROM build_hybrid_query(
        rating_min := 4.5,
        max_age_days := 365,
        difficulty_filter := ''Advanced'',
        sort_by := ''rating'',
        result_limit := 6
    );' as example_usage;

-- ============================================================================
-- INTERACTIVE QUERY EXAMPLES
-- ============================================================================

-- Example 1: E-commerce Search
SELECT * FROM build_hybrid_query(
    search_term := 'web development',
    category_filter := 'Web Development',
    price_max := 50,
    format_filter := 'ebook',
    rating_min := 3.8,
    stock_min := 1,
    sort_by := 'rating',
    result_limit := 8
);

-- Example 2: Academic Research
SELECT * FROM build_hybrid_query(
    search_term := 'artificial intelligence',
    category_filter := 'AI',
    difficulty_filter := 'Advanced',
    publisher_filter := 'O''Reilly',
    max_age_days := 730,
    sort_by := 'newest',
    result_limit := 5
);

-- Example 3: Student Budget Search
SELECT * FROM build_hybrid_query(
    category_filter := 'Programming',
    price_max := 30,
    difficulty_filter := 'Beginner',
    format_filter := 'paperback',
    rating_min := 3.5,
    sort_by := 'price_asc',
    result_limit := 10
);

-- Example 4: Professional Development
SELECT * FROM build_hybrid_query(
    search_term := 'software architecture',
    difficulty_filter := 'Advanced',
    rating_min := 4.0,
    max_age_days := 1095,
    sort_by := 'rating',
    result_limit := 7
);

-- ============================================================================
-- ADVANCED QUERY PATTERNS
-- ============================================================================

-- Pattern 1: Multi-Category Exploration
WITH category_search AS (
    SELECT * FROM build_hybrid_query(
        search_term := 'data analysis',
        category_filter := 'Data Science',
        rating_min := 4.0,
        result_limit := 3
    )
    UNION ALL
    SELECT * FROM build_hybrid_query(
        search_term := 'data analysis',
        category_filter := 'Programming',
        rating_min := 4.0,
        result_limit := 3
    )
    UNION ALL
    SELECT * FROM build_hybrid_query(
        search_term := 'data analysis',
        category_filter := 'AI',
        rating_min := 4.0,
        result_limit := 3
    )
)
SELECT 
    'Multi-Category Exploration: Data Analysis Books' as search_type,
    category,
    book_title,
    price,
    rating,
    similarity_score
FROM category_search
ORDER BY category, similarity_score;

-- Pattern 2: Price Range Analysis
WITH price_tiers AS (
    SELECT 'Budget (Under $30)' as tier, * FROM build_hybrid_query(
        search_term := 'javascript',
        price_max := 30,
        rating_min := 3.5,
        result_limit := 3
    )
    UNION ALL
    SELECT 'Mid-Range ($30-$60)' as tier, * FROM build_hybrid_query(
        search_term := 'javascript',
        price_min := 30,
        price_max := 60,
        rating_min := 3.5,
        result_limit := 3
    )
    UNION ALL
    SELECT 'Premium ($60+)' as tier, * FROM build_hybrid_query(
        search_term := 'javascript',
        price_min := 60,
        rating_min := 3.5,
        result_limit := 3
    )
)
SELECT 
    'Price Tier Analysis: JavaScript Books' as analysis_type,
    tier as price_tier,
    book_title,
    price,
    format,
    rating
FROM price_tiers
ORDER BY 
    CASE tier
        WHEN 'Budget (Under $30)' THEN 1
        WHEN 'Mid-Range ($30-$60)' THEN 2
        WHEN 'Premium ($60+)' THEN 3
    END,
    price;

-- Pattern 3: Difficulty Progression
WITH learning_path AS (
    SELECT 'Beginner' as level, * FROM build_hybrid_query(
        search_term := 'python',
        difficulty_filter := 'Beginner',
        rating_min := 4.0,
        result_limit := 2
    )
    UNION ALL
    SELECT 'Intermediate' as level, * FROM build_hybrid_query(
        search_term := 'python',
        difficulty_filter := 'Intermediate',
        rating_min := 4.0,
        result_limit := 2
    )
    UNION ALL
    SELECT 'Advanced' as level, * FROM build_hybrid_query(
        search_term := 'python',
        difficulty_filter := 'Advanced',
        rating_min := 4.0,
        result_limit := 2
    )
)
SELECT 
    'Learning Path: Python Programming' as path_type,
    level as difficulty_level,
    book_title,
    price,
    rating,
    publisher,
    CASE level
        WHEN 'Beginner' THEN 'Start here for fundamentals'
        WHEN 'Intermediate' THEN 'Build practical skills'
        WHEN 'Advanced' THEN 'Master advanced concepts'
    END as learning_objective
FROM learning_path
ORDER BY 
    CASE level
        WHEN 'Beginner' THEN 1
        WHEN 'Intermediate' THEN 2
        WHEN 'Advanced' THEN 3
    END,
    rating DESC;

-- ============================================================================
-- CUSTOM QUERY BUILDER HELPERS
-- ============================================================================

-- Function to get available filter values
CREATE OR REPLACE FUNCTION get_filter_options()
RETURNS TABLE(
    filter_type TEXT,
    available_values TEXT[],
    value_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'subjects' as filter_type,
        array_agg(DISTINCT subject ORDER BY subject) as available_values,
        COUNT(DISTINCT subject)::INTEGER as value_count
    FROM items
    WHERE subject IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'formats',
        array_agg(DISTINCT metadata->>'format' ORDER BY metadata->>'format'),
        COUNT(DISTINCT metadata->>'format')::INTEGER
    FROM items
    WHERE metadata->>'format' IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'difficulties',
        array_agg(DISTINCT metadata->>'difficulty' ORDER BY metadata->>'difficulty'),
        COUNT(DISTINCT metadata->>'difficulty')::INTEGER
    FROM items
    WHERE metadata->>'difficulty' IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'publishers',
        array_agg(DISTINCT metadata->>'publisher' ORDER BY metadata->>'publisher'),
        COUNT(DISTINCT metadata->>'publisher')::INTEGER
    FROM items
    WHERE metadata->>'publisher' IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Show available filter options
SELECT 
    'Available Filter Options' as info_type,
    filter_type,
    value_count,
    available_values
FROM get_filter_options()
ORDER BY filter_type;

-- Function to get price and rating ranges
CREATE OR REPLACE FUNCTION get_numeric_ranges()
RETURNS TABLE(
    metric_type TEXT,
    min_value NUMERIC,
    max_value NUMERIC,
    avg_value NUMERIC,
    suggested_ranges TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'price' as metric_type,
        MIN((metadata->>'price')::NUMERIC) as min_value,
        MAX((metadata->>'price')::NUMERIC) as max_value,
        ROUND(AVG((metadata->>'price')::NUMERIC), 2) as avg_value,
        ARRAY['Under $30', '$30-$50', '$50-$80', 'Over $80'] as suggested_ranges
    FROM items
    WHERE metadata->>'price' IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'rating',
        MIN((metadata->>'rating')::NUMERIC),
        MAX((metadata->>'rating')::NUMERIC),
        ROUND(AVG((metadata->>'rating')::NUMERIC), 2),
        ARRAY['3.0+', '3.5+', '4.0+', '4.5+']
    FROM items
    WHERE metadata->>'rating' IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'stock',
        MIN((metadata->>'stock')::INTEGER)::NUMERIC,
        MAX((metadata->>'stock')::INTEGER)::NUMERIC,
        ROUND(AVG((metadata->>'stock')::INTEGER), 0),
        ARRAY['1+', '10+', '50+', '100+']
    FROM items
    WHERE metadata->>'stock' IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Show numeric ranges for filters
SELECT 
    'Numeric Filter Ranges' as info_type,
    metric_type,
    min_value,
    max_value,
    avg_value,
    suggested_ranges
FROM get_numeric_ranges()
ORDER BY metric_type;

-- ============================================================================
-- QUERY PERFORMANCE ANALYZER
-- ============================================================================

-- Function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_query_performance(
    test_search_term TEXT DEFAULT 'programming',
    test_category TEXT DEFAULT 'Programming'
)
RETURNS TABLE(
    query_type TEXT,
    execution_time_ms NUMERIC,
    rows_returned INTEGER,
    performance_notes TEXT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    row_count INTEGER;
BEGIN
    -- Test 1: Simple similarity search
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM build_hybrid_query(search_term := test_search_term, result_limit := 10);
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'Simple Similarity Search',
        EXTRACT(MILLISECONDS FROM (end_time - start_time)),
        row_count,
        'Basic vector similarity with text search';
    
    -- Test 2: Category filtered search
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM build_hybrid_query(
        search_term := test_search_term,
        category_filter := test_category,
        result_limit := 10
    );
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'Category Filtered Search',
        EXTRACT(MILLISECONDS FROM (end_time - start_time)),
        row_count,
        'Vector similarity + relational filter';
    
    -- Test 3: Complex multi-filter search
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM build_hybrid_query(
        search_term := test_search_term,
        category_filter := test_category,
        price_max := 60,
        rating_min := 3.5,
        stock_min := 1,
        result_limit := 10
    );
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'Complex Multi-Filter Search',
        EXTRACT(MILLISECONDS FROM (end_time - start_time)),
        row_count,
        'Vector + relational + JSONB filters';
    
    -- Test 4: No similarity search (filters only)
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO row_count FROM build_hybrid_query(
        category_filter := test_category,
        price_max := 60,
        rating_min := 3.5,
        result_limit := 10
    );
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'Filters Only (No Vector)',
        EXTRACT(MILLISECONDS FROM (end_time - start_time)),
        row_count,
        'Relational + JSONB filters only';
END;
$$ LANGUAGE plpgsql;

-- Run performance analysis
SELECT * FROM analyze_query_performance('machine learning', 'AI');

-- ============================================================================
-- QUERY BUILDER USAGE EXAMPLES
-- ============================================================================

-- Example usage scenarios with explanations
SELECT 
    'Query Builder Usage Examples' as section_title,
    'Use these examples as starting points for your own queries' as description;

-- Scenario 1: Find similar books to one you liked
SELECT 
    '1. Find Similar Books' as scenario,
    'build_hybrid_query(search_term := ''Clean Code'', rating_min := 4.0, result_limit := 5)' as query_example,
    'Finds books similar to "Clean Code" with good ratings' as explanation;

-- Scenario 2: Budget shopping for students
SELECT 
    '2. Budget Shopping' as scenario,
    'build_hybrid_query(category_filter := ''Programming'', price_max := 35, difficulty_filter := ''Beginner'', sort_by := ''price_asc'')' as query_example,
    'Finds affordable beginner programming books sorted by price' as explanation;

-- Scenario 3: Latest trends in AI
SELECT 
    '3. Latest AI Trends' as scenario,
    'build_hybrid_query(category_filter := ''AI'', max_age_days := 365, rating_min := 4.0, sort_by := ''newest'')' as query_example,
    'Finds recent, well-rated AI books published in the last year' as explanation;

-- Scenario 4: Premium quality search
SELECT 
    '4. Premium Quality' as scenario,
    'build_hybrid_query(rating_min := 4.5, difficulty_filter := ''Advanced'', publisher_filter := ''O''''Reilly'', sort_by := ''rating'')' as query_example,
    'Finds top-rated advanced books from O''Reilly' as explanation;

-- Scenario 5: Format-specific search
SELECT 
    '5. Format Preference' as scenario,
    'build_hybrid_query(search_term := ''web development'', format_filter := ''ebook'', stock_min := 1, sort_by := ''similarity'')' as query_example,
    'Finds available ebooks about web development' as explanation;

-- ============================================================================
-- CLEANUP AND SUMMARY
-- ============================================================================

-- Summary of query builder capabilities
SELECT 
    'Query Builder Summary' as summary_type,
    jsonb_build_object(
        'available_parameters', jsonb_build_array(
            'search_term', 'similarity_threshold', 'category_filter',
            'price_min', 'price_max', 'format_filter', 'rating_min',
            'stock_min', 'difficulty_filter', 'publisher_filter',
            'max_age_days', 'sort_by', 'result_limit'
        ),
        'sort_options', jsonb_build_array(
            'similarity', 'price_asc', 'price_desc', 'rating', 'newest', 'oldest'
        ),
        'helper_functions', jsonb_build_array(
            'get_filter_options()', 'get_numeric_ranges()', 'analyze_query_performance()'
        ),
        'query_patterns', jsonb_build_array(
            'Basic similarity search', 'Category-focused search',
            'Budget-conscious search', 'Premium quality search',
            'Multi-category exploration', 'Price range analysis',
            'Difficulty progression'
        )
    ) as capabilities;

-- Final example: Build your own query
SELECT 
    'Build Your Own Query!' as call_to_action,
    'Use the build_hybrid_query() function with your own parameters' as instruction,
    'Example: SELECT * FROM build_hybrid_query(search_term := ''your_topic'', category_filter := ''your_category'');' as template;

-- ============================================================================
-- QUERY BUILDER COMPLETE!
-- ============================================================================

-- Congratulations! You now have a powerful query builder for hybrid searches.
--
-- Key features:
-- ✅ Dynamic query construction with 13 parameters
-- ✅ Multiple sorting options for different use cases
-- ✅ Helper functions to explore available filter values
-- ✅ Performance analysis tools
-- ✅ Pre-built templates for common scenarios
-- ✅ Advanced patterns for complex searches
--
-- Next steps:
-- 1. Experiment with different parameter combinations
-- 2. Create your own query templates for specific use cases
-- 3. Use the helper functions to understand your data
-- 4. Monitor performance with the analyzer function
-- 5. Build applications using these query patterns 
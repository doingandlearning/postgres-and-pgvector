-- ============================================================================
-- Hybrid Query Search Scenarios
-- Real-world search patterns combining vector, relational, and JSONB data
-- ============================================================================

-- Connect to your PostgreSQL database first:
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- ============================================================================
-- SCENARIO 1: E-COMMERCE BOOK SEARCH
-- ============================================================================

-- Scenario: Customer searches for "machine learning" books
-- Requirements: Under $60, in stock, good ratings, prefer ebooks

SELECT 
    'E-Commerce Search: Machine Learning Books' as scenario_name,
    name as book_title,
    subject as category,
    metadata->>'price' as price,
    metadata->>'format' as format,
    metadata->>'rating' as rating,
    metadata->>'stock' as stock,
    CASE 
        WHEN (metadata->>'rating')::NUMERIC >= 4.5 THEN 'Excellent'
        WHEN (metadata->>'rating')::NUMERIC >= 4.0 THEN 'Very Good'
        WHEN (metadata->>'rating')::NUMERIC >= 3.5 THEN 'Good'
        ELSE 'Average'
    END as quality_rating
FROM items
WHERE item_data::text ILIKE '%machine%' OR item_data::text ILIKE '%learning%'
  AND (metadata->>'price')::NUMERIC <= 60
  AND (metadata->>'stock')::INTEGER > 0
  AND (metadata->>'rating')::NUMERIC >= 3.5
ORDER BY 
    CASE WHEN metadata->>'format' = 'ebook' THEN 1 ELSE 2 END,
    (metadata->>'rating')::NUMERIC DESC,
    (metadata->>'price')::NUMERIC ASC
LIMIT 10;

-- ============================================================================
-- SCENARIO 2: ACADEMIC RESEARCH ASSISTANCE
-- ============================================================================

-- Scenario: Researcher looking for comprehensive AI textbooks
-- Requirements: Advanced level, recent publications, academic publishers

WITH academic_publishers AS (
    SELECT unnest(ARRAY['MIT Press', 'O''Reilly', 'Manning']) as publisher
),
recent_ai_books AS (
    SELECT 
        name,
        subject,
        metadata,
        created_at,
        CASE 
            WHEN metadata->>'publisher' IN (SELECT publisher FROM academic_publishers) THEN 'Academic'
            ELSE 'Commercial'
        END as publisher_type
    FROM items
    WHERE subject IN ('AI', 'Data Science')
      AND metadata->>'difficulty' = 'Advanced'
      AND created_at > NOW() - INTERVAL '18 months'
      AND (metadata->>'pages')::INTEGER > 300
)
SELECT 
    'Academic Research: Advanced AI Textbooks' as scenario_name,
    name as book_title,
    metadata->>'publisher' as publisher,
    publisher_type,
    metadata->>'pages' as pages,
    metadata->>'price' as price,
    created_at::date as publication_date,
    ROUND(EXTRACT(DAYS FROM NOW() - created_at) / 30) as months_old
FROM recent_ai_books
ORDER BY 
    CASE WHEN publisher_type = 'Academic' THEN 1 ELSE 2 END,
    created_at DESC,
    (metadata->>'rating')::NUMERIC DESC
LIMIT 8;

-- ============================================================================
-- SCENARIO 3: BUDGET-CONSCIOUS STUDENT
-- ============================================================================

-- Scenario: Student needs programming books under $30
-- Requirements: Beginner-friendly, good value, prefer paperback for notes

WITH budget_books AS (
    SELECT 
        name,
        subject,
        metadata,
        (metadata->>'price')::NUMERIC as price,
        (metadata->>'pages')::INTEGER as pages,
        ROUND((metadata->>'price')::NUMERIC / (metadata->>'pages')::INTEGER * 100, 3) as price_per_page
    FROM items
    WHERE subject IN ('Programming', 'Web Development', 'Database')
      AND (metadata->>'price')::NUMERIC <= 30
      AND metadata->>'difficulty' IN ('Beginner', 'Intermediate')
      AND (metadata->>'stock')::INTEGER > 0
)
SELECT 
    'Student Budget Search: Affordable Programming Books' as scenario_name,
    name as book_title,
    subject as category,
    price as price,
    pages,
    price_per_page as value_ratio,
    metadata->>'format' as format,
    metadata->>'difficulty' as level,
    CASE 
        WHEN price_per_page < 0.1 THEN 'Excellent Value'
        WHEN price_per_page < 0.15 THEN 'Good Value'
        WHEN price_per_page < 0.2 THEN 'Fair Value'
        ELSE 'Premium Pricing'
    END as value_assessment
FROM budget_books
ORDER BY 
    CASE WHEN metadata->>'format' = 'paperback' THEN 1 ELSE 2 END,
    price_per_page ASC,
    (metadata->>'rating')::NUMERIC DESC
LIMIT 12;

-- ============================================================================
-- SCENARIO 4: PROFESSIONAL DEVELOPMENT
-- ============================================================================

-- Scenario: Senior developer looking for advanced topics
-- Requirements: Latest trends, expert-level content, willing to pay premium

WITH professional_books AS (
    SELECT 
        name,
        subject,
        metadata,
        created_at,
        CASE 
            WHEN item_data::text ILIKE '%advanced%' OR metadata->>'difficulty' = 'Advanced' THEN 3
            WHEN item_data::text ILIKE '%expert%' OR item_data::text ILIKE '%professional%' THEN 3
            WHEN metadata->>'difficulty' = 'Intermediate' THEN 2
            ELSE 1
        END as expertise_score,
        CASE 
            WHEN created_at > NOW() - INTERVAL '6 months' THEN 3
            WHEN created_at > NOW() - INTERVAL '12 months' THEN 2
            ELSE 1
        END as recency_score
    FROM items
    WHERE subject IN ('Programming', 'AI', 'Data Science', 'Web Development')
      AND (metadata->>'rating')::NUMERIC >= 4.0
      AND (metadata->>'stock')::INTEGER > 0
),
scored_books AS (
    SELECT 
        *,
        (expertise_score + recency_score + (metadata->>'rating')::NUMERIC) as total_score
    FROM professional_books
)
SELECT 
    'Professional Development: Advanced Technical Books' as scenario_name,
    name as book_title,
    subject as category,
    metadata->>'difficulty' as difficulty,
    metadata->>'price' as price,
    metadata->>'rating' as rating,
    created_at::date as published_date,
    expertise_score,
    recency_score,
    total_score,
    CASE 
        WHEN total_score >= 8 THEN 'Highly Recommended'
        WHEN total_score >= 6 THEN 'Recommended'
        ELSE 'Consider'
    END as recommendation
FROM scored_books
ORDER BY total_score DESC, (metadata->>'price')::NUMERIC DESC
LIMIT 10;

-- ============================================================================
-- SCENARIO 5: TEAM LEAD BUILDING LIBRARY
-- ============================================================================

-- Scenario: Tech lead curating books for team learning
-- Requirements: Variety of levels, different formats, bulk purchase considerations

WITH team_library AS (
    SELECT 
        name,
        subject,
        metadata,
        CASE metadata->>'difficulty'
            WHEN 'Beginner' THEN 1
            WHEN 'Intermediate' THEN 2
            WHEN 'Advanced' THEN 3
        END as difficulty_level,
        CASE metadata->>'format'
            WHEN 'ebook' THEN 'Digital'
            ELSE 'Physical'
        END as format_type
    FROM items
    WHERE subject IN ('Programming', 'Web Development', 'Database', 'Design')
      AND (metadata->>'rating')::NUMERIC >= 3.8
      AND (metadata->>'stock')::INTEGER >= 5  -- Bulk availability
),
balanced_selection AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY subject, difficulty_level 
            ORDER BY (metadata->>'rating')::NUMERIC DESC
        ) as rank_in_category
    FROM team_library
)
SELECT 
    'Team Library Curation: Balanced Learning Collection' as scenario_name,
    name as book_title,
    subject as category,
    metadata->>'difficulty' as difficulty,
    metadata->>'format' as format,
    metadata->>'price' as individual_price,
    ROUND((metadata->>'price')::NUMERIC * 0.85, 2) as bulk_price_estimate,
    metadata->>'rating' as rating,
    metadata->>'stock' as available_copies,
    CASE 
        WHEN difficulty_level = 1 THEN 'Onboarding'
        WHEN difficulty_level = 2 THEN 'Skill Building'
        WHEN difficulty_level = 3 THEN 'Expert Development'
    END as learning_purpose
FROM balanced_selection
WHERE rank_in_category <= 2  -- Top 2 in each category/difficulty
ORDER BY subject, difficulty_level, (metadata->>'rating')::NUMERIC DESC
LIMIT 20;

-- ============================================================================
-- SCENARIO 6: GIFT RECOMMENDATION ENGINE
-- ============================================================================

-- Scenario: Recommending books as gifts based on recipient interests
-- Requirements: Popular titles, gift-worthy presentation, broad appeal

CREATE TEMP TABLE gift_recipients AS
SELECT * FROM (VALUES
    ('junior_developer', ARRAY['Programming', 'Web Development'], 'Beginner', 50),
    ('data_scientist', ARRAY['AI', 'Data Science'], 'Advanced', 80),
    ('tech_manager', ARRAY['Business', 'Programming'], 'Intermediate', 60),
    ('design_student', ARRAY['Design', 'Web Development'], 'Beginner', 40)
) AS t(recipient_type, interests, level, budget);

WITH gift_recommendations AS (
    SELECT 
        gr.recipient_type,
        i.name,
        i.subject,
        i.metadata,
        CASE 
            WHEN i.metadata->'tags' @> '["bestseller"]' THEN 2
            WHEN (i.metadata->>'rating')::NUMERIC >= 4.5 THEN 1.5
            ELSE 1
        END as popularity_boost,
        CASE 
            WHEN i.metadata->>'format' = 'hardcover' THEN 1.5
            WHEN i.metadata->>'format' = 'paperback' THEN 1.2
            ELSE 1
        END as gift_presentation_score
    FROM gift_recipients gr
    JOIN items i ON i.subject = ANY(gr.interests)
    WHERE i.metadata->>'difficulty' = gr.level
      AND (i.metadata->>'price')::NUMERIC <= gr.budget
      AND (i.metadata->>'rating')::NUMERIC >= 4.0
      AND (i.metadata->>'stock')::INTEGER > 0
),
scored_gifts AS (
    SELECT 
        *,
        (popularity_boost * gift_presentation_score * (metadata->>'rating')::NUMERIC) as gift_score
    FROM gift_recommendations
)
SELECT 
    'Gift Recommendations: Perfect Books for Tech Professionals' as scenario_name,
    recipient_type as for_recipient,
    name as book_title,
    subject as category,
    metadata->>'difficulty' as level,
    metadata->>'price' as price,
    metadata->>'format' as format,
    metadata->>'rating' as rating,
    ROUND(gift_score, 2) as gift_suitability_score,
    CASE 
        WHEN metadata->'tags' @> '["bestseller"]' THEN 'Bestseller ⭐'
        WHEN (metadata->>'rating')::NUMERIC >= 4.7 THEN 'Highly Rated 📚'
        WHEN metadata->>'format' = 'hardcover' THEN 'Premium Edition 🎁'
        ELSE 'Great Choice ✨'
    END as gift_appeal
FROM scored_gifts
ORDER BY recipient_type, gift_score DESC;

-- Cleanup
DROP TABLE gift_recipients;

-- ============================================================================
-- SCENARIO 7: SEASONAL LEARNING CAMPAIGN
-- ============================================================================

-- Scenario: Bookstore promoting seasonal learning themes
-- Requirements: Thematic groupings, special offers, inventory management

WITH seasonal_themes AS (
    SELECT * FROM (VALUES
        ('New Year Skill Boost', ARRAY['Programming', 'Web Development'], 'Learn new skills for career growth'),
        ('AI Summer', ARRAY['AI', 'Data Science'], 'Dive deep into artificial intelligence'),
        ('Back to Basics', ARRAY['Programming', 'Database'], 'Strengthen your fundamentals'),
        ('Design Thinking', ARRAY['Design', 'Business'], 'Creative problem solving')
    ) AS t(campaign_name, categories, description)
),
campaign_books AS (
    SELECT 
        st.campaign_name,
        st.description as campaign_description,
        i.name,
        i.subject,
        i.metadata,
        CASE 
            WHEN (i.metadata->>'stock')::INTEGER > 100 THEN 'High Stock'
            WHEN (i.metadata->>'stock')::INTEGER > 50 THEN 'Medium Stock'
            WHEN (i.metadata->>'stock')::INTEGER > 10 THEN 'Low Stock'
            ELSE 'Very Low Stock'
        END as inventory_status,
        CASE 
            WHEN (i.metadata->>'rating')::NUMERIC >= 4.5 AND (i.metadata->>'stock')::INTEGER > 50 THEN 20
            WHEN (i.metadata->>'rating')::NUMERIC >= 4.0 AND (i.metadata->>'stock')::INTEGER > 20 THEN 15
            WHEN (i.metadata->>'stock')::INTEGER > 100 THEN 10
            ELSE 5
        END as suggested_discount_percent
    FROM seasonal_themes st
    JOIN items i ON i.subject = ANY(st.categories)
    WHERE (i.metadata->>'rating')::NUMERIC >= 3.5
      AND (i.metadata->>'stock')::INTEGER > 5
)
SELECT 
    'Seasonal Campaign: Thematic Book Promotions' as scenario_name,
    campaign_name,
    campaign_description,
    name as book_title,
    subject as category,
    metadata->>'price' as original_price,
    ROUND(
        (metadata->>'price')::NUMERIC * (1 - suggested_discount_percent::NUMERIC / 100), 
        2
    ) as sale_price,
    suggested_discount_percent || '%' as discount,
    metadata->>'rating' as rating,
    inventory_status,
    CASE 
        WHEN suggested_discount_percent >= 20 THEN 'Featured Deal 🔥'
        WHEN suggested_discount_percent >= 15 THEN 'Great Offer 💫'
        WHEN suggested_discount_percent >= 10 THEN 'Good Deal 👍'
        ELSE 'Regular Price 📖'
    END as promotion_level
FROM campaign_books
ORDER BY campaign_name, suggested_discount_percent DESC, (metadata->>'rating')::NUMERIC DESC
LIMIT 25;

-- ============================================================================
-- SCENARIO 8: COMPETITIVE ANALYSIS
-- ============================================================================

-- Scenario: Analyzing market positioning and pricing strategy
-- Requirements: Publisher comparison, price analysis, market gaps

WITH market_analysis AS (
    SELECT 
        metadata->>'publisher' as publisher,
        subject,
        COUNT(*) as book_count,
        ROUND(AVG((metadata->>'price')::NUMERIC), 2) as avg_price,
        ROUND(AVG((metadata->>'rating')::NUMERIC), 2) as avg_rating,
        MIN((metadata->>'price')::NUMERIC) as min_price,
        MAX((metadata->>'price')::NUMERIC) as max_price,
        SUM((metadata->>'stock')::INTEGER) as total_inventory
    FROM items
    WHERE metadata->>'publisher' IS NOT NULL
      AND subject IN ('Programming', 'AI', 'Data Science', 'Web Development')
    GROUP BY metadata->>'publisher', subject
),
publisher_rankings AS (
    SELECT 
        *,
        RANK() OVER (PARTITION BY subject ORDER BY book_count DESC) as market_share_rank,
        RANK() OVER (PARTITION BY subject ORDER BY avg_rating DESC) as quality_rank,
        CASE 
            WHEN avg_price < 35 THEN 'Budget'
            WHEN avg_price < 55 THEN 'Mid-Range'
            ELSE 'Premium'
        END as price_tier
    FROM market_analysis
)
SELECT 
    'Market Analysis: Publisher Competitive Landscape' as scenario_name,
    publisher,
    subject as category,
    book_count as titles_available,
    avg_price as average_price,
    price_tier,
    avg_rating as average_rating,
    market_share_rank as market_position,
    quality_rank as quality_position,
    total_inventory,
    CASE 
        WHEN market_share_rank <= 2 AND quality_rank <= 2 THEN 'Market Leader'
        WHEN market_share_rank <= 3 THEN 'Strong Player'
        WHEN quality_rank <= 2 THEN 'Quality Specialist'
        ELSE 'Niche Player'
    END as market_position_analysis
FROM publisher_rankings
WHERE book_count >= 2  -- Publishers with meaningful presence
ORDER BY subject, market_share_rank, quality_rank
LIMIT 30;

-- ============================================================================
-- SCENARIO 9: INVENTORY OPTIMIZATION
-- ============================================================================

-- Scenario: Optimizing inventory based on demand patterns
-- Requirements: Stock analysis, reorder recommendations, slow-moving identification

WITH inventory_analysis AS (
    SELECT 
        name,
        subject,
        metadata,
        (metadata->>'stock')::INTEGER as current_stock,
        (metadata->>'rating')::NUMERIC as rating,
        CASE 
            WHEN (metadata->>'rating')::NUMERIC >= 4.5 THEN 'High Demand'
            WHEN (metadata->>'rating')::NUMERIC >= 4.0 THEN 'Medium Demand'
            WHEN (metadata->>'rating')::NUMERIC >= 3.5 THEN 'Low Demand'
            ELSE 'Very Low Demand'
        END as demand_category,
        CASE 
            WHEN (metadata->>'stock')::INTEGER < 10 THEN 'Critical'
            WHEN (metadata->>'stock')::INTEGER < 25 THEN 'Low'
            WHEN (metadata->>'stock')::INTEGER < 100 THEN 'Adequate'
            ELSE 'High'
        END as stock_level,
        EXTRACT(DAYS FROM NOW() - created_at) as days_since_publication
    FROM items
    WHERE metadata IS NOT NULL
),
reorder_recommendations AS (
    SELECT 
        *,
        CASE 
            WHEN demand_category = 'High Demand' AND stock_level IN ('Critical', 'Low') THEN 'Urgent Reorder'
            WHEN demand_category = 'Medium Demand' AND stock_level = 'Critical' THEN 'Reorder Soon'
            WHEN demand_category IN ('Low Demand', 'Very Low Demand') AND stock_level = 'High' AND days_since_publication > 365 THEN 'Consider Clearance'
            WHEN stock_level = 'Adequate' THEN 'Monitor'
            ELSE 'No Action'
        END as recommendation,
        CASE 
            WHEN demand_category = 'High Demand' AND stock_level = 'Critical' THEN current_stock * 5
            WHEN demand_category = 'High Demand' AND stock_level = 'Low' THEN current_stock * 3
            WHEN demand_category = 'Medium Demand' AND stock_level = 'Critical' THEN current_stock * 3
            ELSE current_stock
        END as suggested_reorder_quantity
    FROM inventory_analysis
)
SELECT 
    'Inventory Optimization: Stock Management Recommendations' as scenario_name,
    name as book_title,
    subject as category,
    current_stock,
    stock_level,
    demand_category,
    rating,
    ROUND(days_since_publication) as days_old,
    recommendation,
    CASE 
        WHEN recommendation = 'Urgent Reorder' THEN suggested_reorder_quantity
        WHEN recommendation = 'Reorder Soon' THEN suggested_reorder_quantity
        ELSE NULL
    END as reorder_quantity,
    metadata->>'price' as unit_price,
    CASE 
        WHEN recommendation LIKE '%Reorder%' THEN 
            ROUND((suggested_reorder_quantity * (metadata->>'price')::NUMERIC), 2)
        ELSE NULL
    END as estimated_reorder_cost
FROM reorder_recommendations
WHERE recommendation != 'No Action'
ORDER BY 
    CASE recommendation
        WHEN 'Urgent Reorder' THEN 1
        WHEN 'Reorder Soon' THEN 2
        WHEN 'Consider Clearance' THEN 3
        ELSE 4
    END,
    rating DESC
LIMIT 25;

-- ============================================================================
-- SCENARIO SUMMARY
-- ============================================================================

-- Summary of all scenarios covered
SELECT 
    'Hybrid Query Scenarios Summary' as summary_title,
    jsonb_build_object(
        'total_scenarios', 9,
        'use_cases', jsonb_build_array(
            'E-commerce Search',
            'Academic Research',
            'Budget Shopping',
            'Professional Development',
            'Team Library Curation',
            'Gift Recommendations',
            'Seasonal Campaigns',
            'Market Analysis',
            'Inventory Optimization'
        ),
        'key_patterns', jsonb_build_array(
            'Vector similarity with filters',
            'Multi-criteria scoring',
            'Personalized recommendations',
            'Business intelligence queries',
            'Inventory management',
            'Competitive analysis'
        ),
        'data_types_combined', jsonb_build_array(
            'Vector embeddings',
            'Relational columns',
            'JSONB metadata',
            'Temporal data',
            'Categorical data'
        )
    ) as scenario_overview;

-- Performance tip: Sample query with all patterns combined
SELECT 
    '-- Complete Hybrid Query Pattern Example' as example_title
UNION ALL
SELECT 
    'WITH query_context AS ('
UNION ALL
SELECT 
    '  SELECT embedding, subject FROM items WHERE name ILIKE ''%search_term%'' LIMIT 1'
UNION ALL
SELECT 
    '),'
UNION ALL
SELECT 
    'filtered_results AS ('
UNION ALL
SELECT 
    '  SELECT i.*, i.embedding <=> qc.embedding as similarity'
UNION ALL
SELECT 
    '  FROM items i, query_context qc'
UNION ALL
SELECT 
    '  WHERE i.subject = qc.subject'
UNION ALL
SELECT 
    '    AND (i.metadata->>''price'')::NUMERIC BETWEEN 20 AND 80'
UNION ALL
SELECT 
    '    AND (i.metadata->>''stock'')::INTEGER > 0'
UNION ALL
SELECT 
    '    AND i.created_at > NOW() - INTERVAL ''2 years'''
UNION ALL
SELECT 
    ')'
UNION ALL
SELECT 
    'SELECT name, subject, metadata->>''price'', similarity'
UNION ALL
SELECT 
    'FROM filtered_results'
UNION ALL
SELECT 
    'ORDER BY similarity, (metadata->>''rating'')::NUMERIC DESC'
UNION ALL
SELECT 
    'LIMIT 10;';

-- ============================================================================
-- SCENARIOS COMPLETE!
-- ============================================================================

-- You've explored 9 comprehensive search scenarios that demonstrate:
-- ✅ E-commerce product search with multiple filters
-- ✅ Academic research with authority and recency factors
-- ✅ Budget-conscious shopping with value analysis
-- ✅ Professional development with expertise scoring
-- ✅ Team library curation with balanced selection
-- ✅ Gift recommendation with appeal factors
-- ✅ Seasonal marketing with thematic grouping
-- ✅ Competitive market analysis with publisher insights
-- ✅ Inventory optimization with demand-based recommendations
--
-- These scenarios showcase how hybrid queries can solve real business problems
-- by combining vector similarity, relational filtering, and JSONB flexibility. 
-- ============================================================================
-- Interactive JSONB Exercises
-- Progressive challenges to master PostgreSQL's JSON capabilities
-- ============================================================================

-- Instructions:
-- 1. Connect to PostgreSQL: docker exec -it pgvector-db psql -U postgres -d pgvector
-- 2. Run each section step by step
-- 3. Try to solve the challenges before looking at the solutions
-- 4. Experiment with variations of each query

-- ============================================================================
-- SETUP: Create sample data for exercises
-- ============================================================================

DROP TABLE IF EXISTS library_books, user_profiles, product_reviews, config_settings CASCADE;

-- Library management system
CREATE TABLE library_books (
    id SERIAL PRIMARY KEY,
    isbn TEXT UNIQUE,
    title TEXT NOT NULL,
    details JSONB
);

INSERT INTO library_books (isbn, title, details) VALUES
('978-0-123456-78-9', 'Advanced PostgreSQL', '{
    "author": "Jane Database",
    "publisher": "Tech Publications",
    "year": 2023,
    "pages": 450,
    "subjects": ["databases", "postgresql", "sql"],
    "availability": {
        "total_copies": 5,
        "available": 3,
        "reserved": 1,
        "checked_out": 1
    },
    "ratings": {
        "average": 4.7,
        "count": 23,
        "distribution": {
            "5": 15,
            "4": 6,
            "3": 2,
            "2": 0,
            "1": 0
        }
    },
    "metadata": {
        "isbn_13": "978-0-123456-78-9",
        "language": "English",
        "format": "paperback",
        "weight": "1.2kg"
    }
}'),
('978-0-987654-32-1', 'JavaScript Fundamentals', '{
    "author": "John Coder",
    "publisher": "Web Press",
    "year": 2022,
    "pages": 320,
    "subjects": ["javascript", "web development", "programming"],
    "availability": {
        "total_copies": 8,
        "available": 5,
        "reserved": 2,
        "checked_out": 1
    },
    "ratings": {
        "average": 4.2,
        "count": 18,
        "distribution": {
            "5": 8,
            "4": 7,
            "3": 2,
            "2": 1,
            "1": 0
        }
    },
    "metadata": {
        "isbn_13": "978-0-987654-32-1",
        "language": "English",
        "format": "hardcover",
        "weight": "1.5kg"
    }
}'),
('978-0-555666-77-8', 'Data Science with Python', '{
    "author": "Sarah Analytics",
    "publisher": "Data Books Ltd",
    "year": 2024,
    "pages": 520,
    "subjects": ["python", "data science", "machine learning", "statistics"],
    "availability": {
        "total_copies": 3,
        "available": 0,
        "reserved": 2,
        "checked_out": 1
    },
    "ratings": {
        "average": 4.9,
        "count": 31,
        "distribution": {
            "5": 25,
            "4": 5,
            "3": 1,
            "2": 0,
            "1": 0
        }
    },
    "metadata": {
        "isbn_13": "978-0-555666-77-8",
        "language": "English",
        "format": "paperback",
        "weight": "1.8kg"
    }
}');

-- User profiles with flexible settings
CREATE TABLE user_profiles (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    profile_data JSONB
);

INSERT INTO user_profiles (username, profile_data) VALUES
('alice_reader', '{
    "personal": {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "age": 28,
        "location": "San Francisco, CA"
    },
    "preferences": {
        "genres": ["technology", "science fiction", "non-fiction"],
        "reading_goal": 24,
        "notification_settings": {
            "email_reminders": true,
            "due_date_alerts": true,
            "new_book_notifications": false
        }
    },
    "reading_history": {
        "books_read_this_year": 18,
        "favorite_authors": ["Isaac Asimov", "Jane Database", "Douglas Adams"],
        "reading_streak_days": 45
    },
    "library_settings": {
        "max_checkout_duration": 14,
        "auto_renew": true,
        "hold_expiry_days": 7
    }
}'),
('bob_student', '{
    "personal": {
        "first_name": "Bob",
        "last_name": "Johnson",
        "email": "bob.student@university.edu",
        "age": 22,
        "location": "Boston, MA"
    },
    "preferences": {
        "genres": ["programming", "computer science", "mathematics"],
        "reading_goal": 12,
        "notification_settings": {
            "email_reminders": false,
            "due_date_alerts": true,
            "new_book_notifications": true
        }
    },
    "reading_history": {
        "books_read_this_year": 8,
        "favorite_authors": ["Donald Knuth", "John Coder"],
        "reading_streak_days": 12
    },
    "library_settings": {
        "max_checkout_duration": 21,
        "auto_renew": false,
        "hold_expiry_days": 3
    }
}');

-- Product reviews with varying structures
CREATE TABLE product_reviews (
    review_id SERIAL PRIMARY KEY,
    product_sku TEXT,
    reviewer_name TEXT,
    review_data JSONB
);

INSERT INTO product_reviews (product_sku, reviewer_name, review_data) VALUES
('LAPTOP-001', 'TechReviewer99', '{
    "rating": 5,
    "title": "Excellent laptop for development",
    "content": "Great performance, excellent build quality",
    "date": "2024-01-15",
    "verified_purchase": true,
    "helpful_votes": 23,
    "categories": {
        "performance": 5,
        "build_quality": 5,
        "value": 4,
        "design": 5
    },
    "pros": ["Fast processor", "Great display", "Solid build"],
    "cons": ["Expensive", "Heavy"],
    "would_recommend": true
}'),
('LAPTOP-001', 'CasualUser', '{
    "rating": 3,
    "title": "Good but overpriced",
    "content": "Works well but too expensive for what you get",
    "date": "2024-01-20",
    "verified_purchase": true,
    "helpful_votes": 8,
    "categories": {
        "performance": 4,
        "build_quality": 4,
        "value": 2,
        "design": 3
    },
    "pros": ["Reliable"],
    "cons": ["Overpriced", "Battery life could be better"],
    "would_recommend": false
}'),
('PHONE-002', 'MobileExpert', '{
    "rating": 4,
    "title": "Great phone with minor issues",
    "content": "Excellent camera and performance, but battery drains quickly",
    "date": "2024-01-18",
    "verified_purchase": true,
    "helpful_votes": 15,
    "categories": {
        "camera": 5,
        "performance": 4,
        "battery": 2,
        "design": 4
    },
    "pros": ["Amazing camera", "Fast performance", "Beautiful design"],
    "cons": ["Poor battery life"],
    "would_recommend": true,
    "additional_notes": "Perfect for photography enthusiasts"
}');

-- ============================================================================
-- BEGINNER EXERCISES
-- ============================================================================

-- EXERCISE 1: Basic Field Extraction
-- Challenge: Extract author names from all books
-- Your solution here:


-- Solution:
SELECT title, details->>'author' AS author
FROM library_books;

-- EXERCISE 2: Nested Field Access
-- Challenge: Get the available copies for each book
-- Your solution here:


-- Solution:
SELECT title, details->'availability'->>'available' AS available_copies
FROM library_books;

-- EXERCISE 3: Array Access
-- Challenge: Get the first subject for each book
-- Your solution here:


-- Solution:
SELECT title, details->'subjects'->>0 AS first_subject
FROM library_books;

-- EXERCISE 4: Numeric Comparisons
-- Challenge: Find books with rating above 4.5
-- Your solution here:


-- Solution:
SELECT title, (details->'ratings'->>'average')::NUMERIC AS rating
FROM library_books
WHERE (details->'ratings'->>'average')::NUMERIC > 4.5;

-- ============================================================================
-- INTERMEDIATE EXERCISES
-- ============================================================================

-- EXERCISE 5: Key Existence
-- Challenge: Find books that have availability information
-- Your solution here:


-- Solution:
SELECT title
FROM library_books
WHERE details ? 'availability';

-- EXERCISE 6: Containment Queries
-- Challenge: Find books published by "Tech Publications"
-- Your solution here:


-- Solution:
SELECT title
FROM library_books
WHERE details @> '{"publisher": "Tech Publications"}';

-- EXERCISE 7: Array Containment
-- Challenge: Find books that cover "postgresql" as a subject
-- Your solution here:


-- Solution:
SELECT title
FROM library_books
WHERE details->'subjects' @> '["postgresql"]';

-- EXERCISE 8: Complex Filtering
-- Challenge: Find books with more than 400 pages AND rating above 4.0
-- Your solution here:


-- Solution:
SELECT title, 
       (details->>'pages')::INTEGER AS pages,
       (details->'ratings'->>'average')::NUMERIC AS rating
FROM library_books
WHERE (details->>'pages')::INTEGER > 400
  AND (details->'ratings'->>'average')::NUMERIC > 4.0;

-- ============================================================================
-- ADVANCED EXERCISES
-- ============================================================================

-- EXERCISE 9: Working with Arrays
-- Challenge: List all unique subjects across all books
-- Your solution here:


-- Solution:
SELECT DISTINCT subject
FROM library_books,
LATERAL jsonb_array_elements_text(details->'subjects') AS subject
ORDER BY subject;

-- EXERCISE 10: Aggregation with JSONB
-- Challenge: Calculate average rating by publisher
-- Your solution here:


-- Solution:
SELECT 
    details->>'publisher' AS publisher,
    AVG((details->'ratings'->>'average')::NUMERIC) AS avg_rating,
    COUNT(*) AS book_count
FROM library_books
GROUP BY details->>'publisher'
ORDER BY avg_rating DESC;

-- EXERCISE 11: Complex Nested Queries
-- Challenge: Find users who have read more than 15 books this year AND prefer technology books
-- Your solution here:


-- Solution:
SELECT username,
       profile_data->'reading_history'->>'books_read_this_year' AS books_read,
       profile_data->'preferences'->'genres' AS preferred_genres
FROM user_profiles
WHERE (profile_data->'reading_history'->>'books_read_this_year')::INTEGER > 15
  AND profile_data->'preferences'->'genres' @> '["technology"]';

-- EXERCISE 12: JSON Object Construction
-- Challenge: Create a summary object for each book with title, author, and availability
-- Your solution here:


-- Solution:
SELECT jsonb_build_object(
    'title', title,
    'author', details->>'author',
    'available', details->'availability'->>'available',
    'total', details->'availability'->>'total_copies'
) AS book_summary
FROM library_books;

-- ============================================================================
-- EXPERT EXERCISES
-- ============================================================================

-- EXERCISE 13: Dynamic Updates
-- Challenge: Add a "featured" flag to all books with rating above 4.5
-- Your solution here:


-- Solution:
UPDATE library_books
SET details = jsonb_set(details, '{featured}', 'true'::jsonb)
WHERE (details->'ratings'->>'average')::NUMERIC > 4.5;

-- Verify the update:
SELECT title, details ? 'featured' AS is_featured
FROM library_books;

-- EXERCISE 14: Array Manipulation
-- Challenge: Add "bestseller" to the subjects array for highly rated books
-- Your solution here:


-- Solution:
UPDATE library_books
SET details = jsonb_set(
    details,
    '{subjects}',
    (details->'subjects') || '["bestseller"]'::jsonb
)
WHERE (details->'ratings'->>'average')::NUMERIC > 4.5;

-- EXERCISE 15: Complex Analysis
-- Challenge: Find the distribution of ratings for each product in reviews
-- Your solution here:


-- Solution:
SELECT 
    product_sku,
    jsonb_object_agg(
        rating_value,
        rating_count
    ) AS rating_distribution
FROM (
    SELECT 
        product_sku,
        (review_data->>'rating')::TEXT AS rating_value,
        COUNT(*) AS rating_count
    FROM product_reviews
    GROUP BY product_sku, review_data->>'rating'
) rating_stats
GROUP BY product_sku;

-- EXERCISE 16: Advanced Filtering with Multiple Conditions
-- Challenge: Find books that:
-- 1. Have "programming" or "databases" in subjects
-- 2. Are available (available > 0)
-- 3. Have at least 20 ratings
-- 4. Published after 2020
-- Your solution here:


-- Solution:
SELECT 
    title,
    details->>'author' AS author,
    details->>'year' AS publication_year,
    details->'availability'->>'available' AS available_copies,
    details->'ratings'->>'count' AS rating_count
FROM library_books
WHERE (details->'subjects' @> '["programming"]' OR details->'subjects' @> '["databases"]')
  AND (details->'availability'->>'available')::INTEGER > 0
  AND (details->'ratings'->>'count')::INTEGER >= 20
  AND (details->>'year')::INTEGER > 2020;

-- ============================================================================
-- PERFORMANCE EXERCISES
-- ============================================================================

-- EXERCISE 17: Index Creation and Testing
-- Challenge: Create appropriate indexes and test their performance

-- Create indexes
CREATE INDEX idx_books_details_gin ON library_books USING GIN (details);
CREATE INDEX idx_books_rating ON library_books USING BTREE (((details->'ratings'->>'average')::NUMERIC));
CREATE INDEX idx_books_publisher ON library_books USING BTREE ((details->>'publisher'));

-- Test index usage
EXPLAIN (ANALYZE, BUFFERS)
SELECT title FROM library_books 
WHERE details @> '{"publisher": "Tech Publications"}';

EXPLAIN (ANALYZE, BUFFERS)
SELECT title FROM library_books 
WHERE (details->'ratings'->>'average')::NUMERIC > 4.0;

-- EXERCISE 18: Performance Comparison
-- Challenge: Compare performance of different query approaches

-- Approach 1: Using containment operator
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM library_books 
WHERE details @> '{"subjects": ["postgresql"]}';

-- Approach 2: Using array containment
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM library_books 
WHERE details->'subjects' @> '["postgresql"]';

-- Approach 3: Using text search
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM library_books 
WHERE details::text ILIKE '%postgresql%';

-- ============================================================================
-- REAL-WORLD SCENARIOS
-- ============================================================================

-- EXERCISE 19: Library Management Dashboard
-- Challenge: Create a comprehensive library status report

SELECT 
    'Library Overview' AS report_section,
    jsonb_build_object(
        'total_books', COUNT(*),
        'total_copies', SUM((details->'availability'->>'total_copies')::INTEGER),
        'available_copies', SUM((details->'availability'->>'available')::INTEGER),
        'checked_out_copies', SUM((details->'availability'->>'checked_out')::INTEGER),
        'average_rating', ROUND(AVG((details->'ratings'->>'average')::NUMERIC), 2),
        'most_popular_subject', (
            SELECT subject
            FROM (
                SELECT subject, COUNT(*) as count
                FROM library_books,
                LATERAL jsonb_array_elements_text(details->'subjects') AS subject
                GROUP BY subject
                ORDER BY count DESC
                LIMIT 1
            ) popular_subjects
        )
    ) AS statistics
FROM library_books;

-- EXERCISE 20: User Recommendation System
-- Challenge: Recommend books to users based on their preferences

WITH user_preferences AS (
    SELECT 
        username,
        profile_data->'preferences'->'genres' AS preferred_genres
    FROM user_profiles
    WHERE username = 'alice_reader'
),
matching_books AS (
    SELECT 
        lb.title,
        lb.details->>'author' AS author,
        (lb.details->'ratings'->>'average')::NUMERIC AS rating,
        lb.details->'subjects' AS book_subjects
    FROM library_books lb, user_preferences up
    WHERE lb.details->'subjects' ?| ARRAY(
        SELECT jsonb_array_elements_text(up.preferred_genres)
    )
    AND (lb.details->'availability'->>'available')::INTEGER > 0
    ORDER BY (lb.details->'ratings'->>'average')::NUMERIC DESC
)
SELECT 
    title,
    author,
    rating,
    book_subjects
FROM matching_books
LIMIT 3;

-- ============================================================================
-- BONUS CHALLENGES
-- ============================================================================

-- BONUS 1: Data Migration
-- Challenge: Restructure the book data to separate availability into a new JSON structure

UPDATE library_books
SET details = details || jsonb_build_object(
    'circulation', jsonb_build_object(
        'status', CASE 
            WHEN (details->'availability'->>'available')::INTEGER > 0 THEN 'available'
            WHEN (details->'availability'->>'reserved')::INTEGER > 0 THEN 'reserved_only'
            ELSE 'unavailable'
        END,
        'last_updated', NOW()::TEXT
    )
);

-- BONUS 2: Complex Validation
-- Challenge: Create a function to validate book data structure

CREATE OR REPLACE FUNCTION validate_book_data(book_details JSONB)
RETURNS TABLE(is_valid BOOLEAN, errors TEXT[]) AS $$
DECLARE
    error_list TEXT[] := '{}';
BEGIN
    -- Check required fields
    IF NOT (book_details ? 'author' AND book_details ? 'publisher' AND book_details ? 'year') THEN
        error_list := array_append(error_list, 'Missing required fields: author, publisher, or year');
    END IF;
    
    -- Validate year
    IF book_details ? 'year' AND (book_details->>'year')::INTEGER < 1900 THEN
        error_list := array_append(error_list, 'Invalid year: must be after 1900');
    END IF;
    
    -- Validate rating structure
    IF book_details ? 'ratings' THEN
        IF NOT (book_details->'ratings' ? 'average' AND book_details->'ratings' ? 'count') THEN
            error_list := array_append(error_list, 'Invalid ratings structure');
        END IF;
    END IF;
    
    -- Validate availability structure
    IF book_details ? 'availability' THEN
        IF NOT (book_details->'availability' ? 'total_copies' AND 
                book_details->'availability' ? 'available') THEN
            error_list := array_append(error_list, 'Invalid availability structure');
        END IF;
    END IF;
    
    RETURN QUERY SELECT (array_length(error_list, 1) IS NULL), error_list;
END;
$$ LANGUAGE plpgsql;

-- Test the validation function
SELECT title, (validate_book_data(details)).*
FROM library_books;

-- BONUS 3: Advanced Analytics
-- Challenge: Create a comprehensive analytics query

WITH book_analytics AS (
    SELECT 
        details->>'publisher' AS publisher,
        (details->>'year')::INTEGER AS year,
        (details->'ratings'->>'average')::NUMERIC AS rating,
        (details->'ratings'->>'count')::INTEGER AS rating_count,
        (details->>'pages')::INTEGER AS pages,
        jsonb_array_length(details->'subjects') AS subject_count
    FROM library_books
),
publisher_stats AS (
    SELECT 
        publisher,
        COUNT(*) AS total_books,
        AVG(rating) AS avg_rating,
        AVG(pages) AS avg_pages,
        SUM(rating_count) AS total_ratings,
        MIN(year) AS earliest_year,
        MAX(year) AS latest_year
    FROM book_analytics
    GROUP BY publisher
)
SELECT 
    publisher,
    jsonb_build_object(
        'books', jsonb_build_object(
            'count', total_books,
            'avg_pages', ROUND(avg_pages, 0),
            'publication_span', jsonb_build_object(
                'from', earliest_year,
                'to', latest_year,
                'years_active', latest_year - earliest_year + 1
            )
        ),
        'ratings', jsonb_build_object(
            'average', ROUND(avg_rating, 2),
            'total_reviews', total_ratings,
            'quality_score', CASE 
                WHEN avg_rating >= 4.5 THEN 'excellent'
                WHEN avg_rating >= 4.0 THEN 'very_good'
                WHEN avg_rating >= 3.5 THEN 'good'
                ELSE 'average'
            END
        )
    ) AS publisher_analytics
FROM publisher_stats
ORDER BY avg_rating DESC;

-- ============================================================================
-- EXERCISE COMPLETE!
-- ============================================================================

-- Congratulations! You've completed the interactive JSONB exercises.
--
-- Skills you've practiced:
-- ✅ Basic field extraction and nested access
-- ✅ Array operations and containment queries
-- ✅ Complex filtering and aggregation
-- ✅ Data updates and manipulation
-- ✅ Performance optimization with indexes
-- ✅ Real-world application patterns
-- ✅ Data validation and migration
--
-- Next steps:
-- 1. Try creating your own JSONB exercises with different data
-- 2. Experiment with PostgreSQL's full-text search on JSONB
-- 3. Explore JSONB with time-series data
-- 4. Practice with larger datasets to understand performance implications 
-- ============================================================================
-- JSON and JSONB SQL Workshop
-- Complete hands-on exercises for mastering PostgreSQL's JSON capabilities
-- ============================================================================

-- Connect to your PostgreSQL database first:
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- ============================================================================
-- SECTION 1: SETUP AND BASIC TABLES
-- ============================================================================

-- Clean up any existing tables (optional)
DROP TABLE IF EXISTS products, user_preferences, events, catalog_products, user_analytics CASCADE;

-- Create a products table for our experiments
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create a user preferences table
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    settings JSONB,
    profile JSONB
);

-- Create an events table for analytics
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_type TEXT,
    user_id INTEGER,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- SECTION 2: INSERT SAMPLE DATA
-- ============================================================================

-- Insert product data with flexible metadata
INSERT INTO products (name, price, metadata) VALUES
('Gaming Laptop', 1299.99, '{
    "brand": "TechCorp",
    "specs": {
        "ram": "16GB",
        "storage": "1TB SSD",
        "gpu": "RTX 4060",
        "cpu": "Intel i7"
    },
    "features": ["RGB Keyboard", "144Hz Display", "WiFi 6"],
    "warranty": "2 years",
    "ratings": {
        "average": 4.5,
        "count": 127
    }
}'),
('Smartphone Pro', 899.50, '{
    "brand": "SmartTech",
    "specs": {
        "storage": "256GB",
        "ram": "12GB",
        "battery": "4500mAh",
        "camera": "108MP"
    },
    "features": ["5G", "Wireless Charging", "Face ID"],
    "colors": ["Black", "Silver", "Blue"],
    "ratings": {
        "average": 4.2,
        "count": 89
    }
}'),
('Tablet Ultra', 649.99, '{
    "brand": "TabWorld",
    "specs": {
        "screen": "12.9 inches",
        "storage": "128GB",
        "battery": "10000mAh"
    },
    "features": ["Apple Pencil Support", "Magic Keyboard"],
    "accessories": {
        "included": ["Charger", "Cable"],
        "optional": ["Keyboard", "Pencil"]
    },
    "ratings": {
        "average": 4.7,
        "count": 203
    }
}');

-- Insert user preferences
INSERT INTO user_preferences (user_id, username, settings, profile) VALUES
(1, 'alice_dev', '{
    "theme": "dark",
    "notifications": {
        "email": true,
        "push": false,
        "sms": false
    },
    "privacy": {
        "profile_visible": true,
        "activity_tracking": false
    },
    "preferences": {
        "language": "en",
        "timezone": "UTC-5",
        "currency": "USD"
    }
}', '{
    "bio": "Full-stack developer",
    "location": "San Francisco",
    "skills": ["JavaScript", "Python", "PostgreSQL"],
    "experience": 5,
    "social": {
        "github": "alice_dev",
        "linkedin": "alice-developer"
    }
}'),
(2, 'bob_designer', '{
    "theme": "light",
    "notifications": {
        "email": true,
        "push": true,
        "sms": false
    },
    "privacy": {
        "profile_visible": false,
        "activity_tracking": true
    },
    "preferences": {
        "language": "en",
        "timezone": "UTC-8",
        "currency": "USD"
    }
}', '{
    "bio": "UI/UX Designer",
    "location": "Los Angeles",
    "skills": ["Figma", "Sketch", "Adobe Creative Suite"],
    "experience": 3,
    "portfolio": "https://bobdesigns.com"
}');

-- Insert event data
INSERT INTO events (event_type, user_id, event_data) VALUES
('page_view', 1, '{"page": "/dashboard", "duration": 45, "source": "direct"}'),
('button_click', 1, '{"button": "save_profile", "page": "/settings", "timestamp": "2024-01-15T10:30:00Z"}'),
('purchase', 2, '{"product_id": 1, "amount": 1299.99, "payment_method": "credit_card", "shipping": {"address": "123 Main St", "city": "LA", "state": "CA"}}'),
('search', 2, '{"query": "gaming laptop", "results_count": 15, "filters": {"price_max": 1500, "brand": "TechCorp"}}');

-- ============================================================================
-- SECTION 3: BASIC JSONB QUERYING EXERCISES
-- ============================================================================

-- Exercise 3.1: Extract top-level fields
SELECT name, price, metadata->>'brand' AS brand
FROM products;

-- Exercise 3.2: Extract nested fields
SELECT 
    name,
    metadata->'specs'->>'ram' AS ram,
    metadata->'specs'->>'storage' AS storage
FROM products;

-- Exercise 3.3: Extract array elements
SELECT 
    name,
    metadata->'features' AS all_features,
    metadata->'features'->>0 AS first_feature
FROM products;

-- Exercise 3.4: Work with numeric data in JSON
SELECT 
    name,
    metadata->'ratings'->>'average' AS rating_text,
    (metadata->'ratings'->>'average')::NUMERIC AS rating_number
FROM products
WHERE (metadata->'ratings'->>'average')::NUMERIC > 4.5;

-- ============================================================================
-- SECTION 4: ADVANCED JSONB OPERATORS
-- ============================================================================

-- Exercise 4.1: Check if a key exists (?)
SELECT name, metadata ? 'warranty' AS has_warranty
FROM products;

-- Exercise 4.2: Check if any of multiple keys exist (?|)
SELECT name, metadata ?| array['warranty', 'guarantee'] AS has_warranty_info
FROM products;

-- Exercise 4.3: Check if all keys exist (?&)
SELECT name, metadata ?& array['brand', 'specs'] AS has_basic_info
FROM products;

-- Exercise 4.4: Containment operator (@>)
SELECT name
FROM products
WHERE metadata @> '{"brand": "TechCorp"}';

-- Exercise 4.5: More complex containment
SELECT name
FROM products
WHERE metadata @> '{"specs": {"ram": "16GB"}}';

-- Exercise 4.6: Path exists operator (@?) - PostgreSQL 12+
-- SELECT name
-- FROM products
-- WHERE metadata @? '$.specs.gpu';

-- ============================================================================
-- SECTION 5: JSONB FUNCTIONS AND MANIPULATION
-- ============================================================================

-- Exercise 5.1: Get all keys at the top level
SELECT name, jsonb_object_keys(metadata) AS top_level_keys
FROM products;

-- Exercise 5.2: Get the type of a JSON value
SELECT 
    name,
    jsonb_typeof(metadata->'features') AS features_type,
    jsonb_typeof(metadata->'specs') AS specs_type
FROM products;

-- Exercise 5.3: Get array length
SELECT 
    name,
    jsonb_array_length(metadata->'features') AS feature_count
FROM products
WHERE metadata ? 'features';

-- Exercise 5.4: Convert JSONB to text for searching
SELECT name
FROM products
WHERE metadata::text ILIKE '%wireless%';

-- Exercise 5.5: Pretty print JSON
SELECT name, jsonb_pretty(metadata)
FROM products
LIMIT 1;

-- ============================================================================
-- SECTION 6: UPDATING JSONB DATA
-- ============================================================================

-- Exercise 6.1: Add a new top-level field
UPDATE products
SET metadata = jsonb_set(metadata, '{discount}', '10'::jsonb)
WHERE name = 'Gaming Laptop';

-- Exercise 6.2: Update a nested field
UPDATE products
SET metadata = jsonb_set(metadata, '{specs, ram}', '"32GB"'::jsonb)
WHERE name = 'Gaming Laptop';

-- Exercise 6.3: Add to an array
UPDATE products
SET metadata = jsonb_set(
    metadata, 
    '{features}', 
    (metadata->'features') || '["Thunderbolt 4"]'::jsonb
)
WHERE name = 'Gaming Laptop';

-- Exercise 6.4: Remove a field
UPDATE products
SET metadata = metadata - 'discount'
WHERE name = 'Gaming Laptop';

-- Exercise 6.5: Remove nested field
UPDATE products
SET metadata = metadata #- '{specs,gpu}'
WHERE name = 'Gaming Laptop';

-- Exercise 6.6: Merge JSON objects
UPDATE user_preferences
SET settings = settings || '{"new_feature": true}'::jsonb
WHERE user_id = 1;

-- ============================================================================
-- SECTION 7: PERFORMANCE AND INDEXING
-- ============================================================================

-- Exercise 7.1: Create a GIN index for general JSONB operations
CREATE INDEX idx_products_metadata_gin ON products USING GIN (metadata);

-- Exercise 7.2: Test the index with containment queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT name FROM products 
WHERE metadata @> '{"brand": "TechCorp"}';

-- Exercise 7.3: Create expression indexes for specific paths
CREATE INDEX idx_products_brand ON products USING BTREE ((metadata->>'brand'));
CREATE INDEX idx_products_rating ON products USING BTREE (((metadata->'ratings'->>'average')::NUMERIC));

-- Exercise 7.4: Test the expression indexes
EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM products 
WHERE metadata->>'brand' = 'TechCorp';

EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM products 
WHERE (metadata->'ratings'->>'average')::NUMERIC > 4.0;

-- ============================================================================
-- SECTION 8: REAL-WORLD SCENARIO - E-COMMERCE CATALOG
-- ============================================================================

-- Create a flexible product catalog
CREATE TABLE catalog_products (
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    base_price NUMERIC NOT NULL,
    category TEXT,
    attributes JSONB,
    inventory JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert various product types with different attributes
INSERT INTO catalog_products (sku, name, base_price, category, attributes, inventory) VALUES
('LAPTOP-001', 'Gaming Laptop Pro', 1599.99, 'electronics', '{
    "brand": "GameTech",
    "model": "Pro-X1",
    "specifications": {
        "processor": "Intel i9-12900H",
        "memory": "32GB DDR5",
        "storage": "1TB NVMe SSD",
        "graphics": "RTX 4070",
        "display": "15.6\" 165Hz QHD",
        "ports": ["USB-C", "USB-A", "HDMI", "Ethernet"]
    },
    "dimensions": {
        "width": 35.7,
        "depth": 25.9,
        "height": 2.39,
        "weight": 2.5
    },
    "certifications": ["Energy Star", "EPEAT Gold"],
    "warranty": "3 years"
}', '{
    "stock_level": 15,
    "reserved": 3,
    "available": 12,
    "warehouse_locations": ["US-West", "US-East"],
    "reorder_point": 5,
    "supplier": "GameTech Direct"
}'),
('BOOK-001', 'PostgreSQL Advanced Guide', 49.99, 'books', '{
    "isbn": "978-1234567890",
    "author": "Jane Database",
    "publisher": "Tech Books Inc",
    "publication_date": "2024-01-15",
    "pages": 450,
    "format": "paperback",
    "language": "English",
    "topics": ["PostgreSQL", "Database Design", "Performance Tuning"],
    "difficulty": "advanced",
    "edition": 2
}', '{
    "stock_level": 50,
    "reserved": 5,
    "available": 45,
    "warehouse_locations": ["US-Central"],
    "reorder_point": 10,
    "supplier": "Book Distributors LLC"
}');

-- Query examples for the catalog
-- Find all electronics with specific specs
SELECT name, attributes->'specifications'->>'processor' AS cpu
FROM catalog_products
WHERE category = 'electronics'
  AND attributes->'specifications' ? 'processor';

-- Find products with low inventory
SELECT name, inventory->>'available' AS available_stock
FROM catalog_products
WHERE (inventory->>'available')::INTEGER < (inventory->>'reorder_point')::INTEGER;

-- Search across all attributes
SELECT name, category
FROM catalog_products
WHERE attributes::text ILIKE '%postgresql%';

-- ============================================================================
-- SECTION 9: ANALYTICS AND AGGREGATION
-- ============================================================================

-- Create user analytics table
CREATE TABLE user_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    session_id TEXT,
    event_type TEXT,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Insert various event types
INSERT INTO user_analytics (user_id, session_id, event_type, event_data) VALUES
(1, 'sess_123', 'page_view', '{
    "page": "/products/laptops",
    "referrer": "https://google.com",
    "user_agent": "Mozilla/5.0...",
    "viewport": {"width": 1920, "height": 1080},
    "load_time": 1.2
}'),
(1, 'sess_123', 'product_view', '{
    "product_id": "LAPTOP-001",
    "product_name": "Gaming Laptop Pro",
    "category": "electronics",
    "price": 1599.99,
    "time_spent": 45,
    "images_viewed": 5,
    "tab_switches": 3
}'),
(1, 'sess_123', 'add_to_cart', '{
    "product_id": "LAPTOP-001",
    "quantity": 1,
    "price": 1599.99,
    "cart_total": 1599.99,
    "cart_items": 1
}'),
(2, 'sess_456', 'product_view', '{
    "product_id": "BOOK-001",
    "product_name": "PostgreSQL Advanced Guide",
    "category": "books",
    "price": 49.99,
    "time_spent": 30,
    "images_viewed": 2
}'),
(2, 'sess_456', 'purchase', '{
    "product_id": "BOOK-001",
    "quantity": 1,
    "price": 49.99,
    "payment_method": "credit_card"
}');

-- Analytics queries
-- Find users who viewed but didn't purchase
SELECT DISTINCT user_id
FROM user_analytics
WHERE event_type = 'product_view'
  AND user_id NOT IN (
    SELECT DISTINCT user_id
    FROM user_analytics
    WHERE event_type = 'purchase'
  );

-- Average time spent on product pages
SELECT 
    AVG((event_data->>'time_spent')::INTEGER) AS avg_time_spent
FROM user_analytics
WHERE event_type = 'product_view'
  AND event_data ? 'time_spent';

-- Most viewed product categories
SELECT 
    event_data->>'category' AS category,
    COUNT(*) AS view_count
FROM user_analytics
WHERE event_type = 'product_view'
GROUP BY event_data->>'category'
ORDER BY view_count DESC;

-- ============================================================================
-- SECTION 10: ADVANCED PATTERNS AND TECHNIQUES
-- ============================================================================

-- Working with arrays in JSONB
SELECT name, feature
FROM products,
LATERAL jsonb_array_elements_text(metadata->'features') AS feature
WHERE metadata ? 'features';

-- Aggregating JSONB data
SELECT 
    metadata->>'brand' AS brand,
    AVG((metadata->'ratings'->>'average')::NUMERIC) AS avg_rating,
    COUNT(*) AS product_count
FROM products
WHERE metadata ? 'brand' AND metadata->'ratings' ? 'average'
GROUP BY metadata->>'brand'
ORDER BY avg_rating DESC;

-- Complex filtering with multiple conditions
SELECT 
    name,
    metadata->>'brand' AS brand,
    (metadata->'ratings'->>'average')::NUMERIC AS rating
FROM products
WHERE metadata @> '{"specs": {"ram": "16GB"}}'
   OR (metadata->'ratings'->>'average')::NUMERIC > 4.5;

-- Using JSONB for flexible filtering
SELECT name, metadata->'specs' AS specs
FROM products
WHERE metadata->'specs' @> '{"storage": "1TB SSD"}'
   OR metadata->'specs' @> '{"storage": "512GB SSD"}';

-- ============================================================================
-- SECTION 11: DATA VALIDATION AND CONSTRAINTS
-- ============================================================================

-- Create a function to validate product JSON schema
CREATE OR REPLACE FUNCTION validate_product_json(data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check required fields
    IF NOT (data ? 'brand' AND data ? 'specs') THEN
        RETURN FALSE;
    END IF;
    
    -- Validate ratings if present
    IF data ? 'ratings' THEN
        IF NOT (data->'ratings' ? 'average' AND data->'ratings' ? 'count') THEN
            RETURN FALSE;
        END IF;
        
        -- Validate rating range
        IF (data->'ratings'->>'average')::NUMERIC < 0 OR 
           (data->'ratings'->>'average')::NUMERIC > 5 THEN
            RETURN FALSE;
        END IF;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Test the validation function
SELECT name, validate_product_json(metadata) AS is_valid
FROM products;

-- ============================================================================
-- SECTION 12: PERFORMANCE TESTING
-- ============================================================================

-- Create a larger dataset for testing
INSERT INTO products (name, price, metadata)
SELECT 
    'Product ' || generate_series,
    random() * 1000 + 100,
    jsonb_build_object(
        'brand', 'Brand' || (random() * 10)::INTEGER,
        'category', 'Category' || (random() * 5)::INTEGER,
        'rating', round((random() * 5)::NUMERIC, 1),
        'features', jsonb_build_array(
            'Feature' || (random() * 20)::INTEGER,
            'Feature' || (random() * 20)::INTEGER
        )
    )
FROM generate_series(1, 1000);

-- Test query performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM products 
WHERE metadata @> '{"brand": "Brand5"}';

-- ============================================================================
-- SECTION 13: CLEANUP (OPTIONAL)
-- ============================================================================

-- Uncomment these lines if you want to clean up the test data
-- DROP TABLE IF EXISTS products, user_preferences, events, catalog_products, user_analytics CASCADE;
-- DROP FUNCTION IF EXISTS validate_product_json(JSONB);

-- ============================================================================
-- WORKSHOP COMPLETE!
-- ============================================================================

-- Congratulations! You've completed the JSON/JSONB workshop.
-- 
-- Key concepts covered:
-- 1. JSON vs JSONB differences and use cases
-- 2. Basic and advanced JSONB operators
-- 3. JSONB functions for data manipulation
-- 4. Indexing strategies for performance
-- 5. Real-world application patterns
-- 6. Data validation and constraints
-- 7. Performance testing and optimization
--
-- Next steps:
-- - Practice with your own data
-- - Explore PostgreSQL's full-text search with JSONB
-- - Learn about JSONB aggregation functions
-- - Study advanced indexing for large datasets 
# Lab: JSON and JSONB in PostgreSQL (Non-Python Starter)

## Objective
This lab focuses on understanding **PostgreSQL's JSON and JSONB capabilities** without requiring Python programming. You'll learn how to store, query, and optimize semi-structured data using SQL.

## Learning Goals
- Understand the difference between JSON and JSONB data types
- Store and query flexible, schema-less data within relational tables
- Master JSONB operators and functions for data manipulation
- Implement indexing strategies for optimal JSONB performance
- Build real-world applications using hybrid relational-document patterns
- Understand when to use JSONB vs traditional relational design

## Prerequisites

Make sure you have a PostgreSQL database running with the pgvector extension:
```bash
# Start the database (from the course root directory)
cd ../../environment
docker-compose up -d

# Connect to the database
docker exec -it pgvector-db psql -U postgres -d pgvector
```

## JSON vs JSONB: The Foundation

### Understanding the Difference

| Aspect | JSON | JSONB |
|--------|------|-------|
| **Storage** | Text format (exact input preserved) | Binary format (optimized) |
| **Performance** | Slower (parses on every access) | Faster (pre-parsed) |
| **Indexing** | Limited indexing support | Full GIN indexing support |
| **Operators** | Basic operators only | Rich set of operators |
| **Space** | Larger storage footprint | Compressed, smaller storage |
| **Use Case** | Logging, audit trails | Searchable metadata, APIs |

### When to Use Each

**Use JSON when:**
- You need to preserve exact formatting (whitespace, key order)
- Data is write-heavy, read-light (logs, audit trails)
- You're storing data that won't be queried frequently

**Use JSONB when:**
- You need to query and index the data
- Performance is important
- You want to use advanced operators and functions
- Building APIs or storing user preferences/settings

## Approach Options

### Option A: Interactive SQL Workshop (Recommended)

Learn through hands-on SQL exercises with immediate feedback.

#### Step 1: Create Your Test Environment
```sql
-- Connect to PostgreSQL first
-- docker exec -it pgvector-db psql -U postgres -d pgvector

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
```

#### Step 2: Insert Sample Data
```sql
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
```

### Option B: Guided SQL Exploration

Follow structured exercises that build your understanding progressively.

#### Exercise 1: Basic JSONB Querying
```sql
-- 1. Extract top-level fields
SELECT name, price, metadata->>'brand' AS brand
FROM products;

-- 2. Extract nested fields
SELECT 
    name,
    metadata->'specs'->>'ram' AS ram,
    metadata->'specs'->>'storage' AS storage
FROM products;

-- 3. Extract array elements
SELECT 
    name,
    metadata->'features' AS all_features,
    metadata->'features'->>0 AS first_feature
FROM products;

-- 4. Work with numeric data in JSON
SELECT 
    name,
    metadata->'ratings'->>'average' AS rating_text,
    (metadata->'ratings'->>'average')::NUMERIC AS rating_number
FROM products
WHERE (metadata->'ratings'->>'average')::NUMERIC > 4.5;
```

**Questions to Consider:**
- What's the difference between `->` and `->>`?
- Why do we need to cast JSON values when doing numeric comparisons?
- How would you extract the second feature from the features array?

#### Exercise 2: Advanced JSONB Operators
```sql
-- 1. Check if a key exists (?)
SELECT name, metadata ? 'warranty' AS has_warranty
FROM products;

-- 2. Check if any of multiple keys exist (?|)
SELECT name, metadata ?| array['warranty', 'guarantee'] AS has_warranty_info
FROM products;

-- 3. Check if all keys exist (?&)
SELECT name, metadata ?& array['brand', 'specs'] AS has_basic_info
FROM products;

-- 4. Containment operator (@>)
SELECT name
FROM products
WHERE metadata @> '{"brand": "TechCorp"}';

-- 5. More complex containment
SELECT name
FROM products
WHERE metadata @> '{"specs": {"ram": "16GB"}}';

-- 6. Path exists operator (@?)
SELECT name
FROM products
WHERE metadata @? '$.specs.gpu';
```

**Questions to Consider:**
- When would you use `@>` vs `->>`?
- What's the performance difference between these operators?
- How does the path operator `@?` work with nested structures?

#### Exercise 3: JSONB Functions and Manipulation
```sql
-- 1. Get all keys at the top level
SELECT name, jsonb_object_keys(metadata) AS top_level_keys
FROM products;

-- 2. Get the type of a JSON value
SELECT 
    name,
    jsonb_typeof(metadata->'features') AS features_type,
    jsonb_typeof(metadata->'specs') AS specs_type
FROM products;

-- 3. Get array length
SELECT 
    name,
    jsonb_array_length(metadata->'features') AS feature_count
FROM products
WHERE metadata ? 'features';

-- 4. Convert JSONB to text for searching
SELECT name
FROM products
WHERE metadata::text ILIKE '%wireless%';

-- 5. Pretty print JSON
SELECT name, jsonb_pretty(metadata)
FROM products
LIMIT 1;
```

#### Exercise 4: Updating JSONB Data
```sql
-- 1. Add a new top-level field
UPDATE products
SET metadata = jsonb_set(metadata, '{discount}', '10'::jsonb)
WHERE name = 'Gaming Laptop';

-- 2. Update a nested field
UPDATE products
SET metadata = jsonb_set(metadata, '{specs, ram}', '"32GB"'::jsonb)
WHERE name = 'Gaming Laptop';

-- 3. Add to an array
UPDATE products
SET metadata = jsonb_set(
    metadata, 
    '{features}', 
    (metadata->'features') || '["Thunderbolt 4"]'::jsonb
)
WHERE name = 'Gaming Laptop';

-- 4. Remove a field
UPDATE products
SET metadata = metadata - 'discount'
WHERE name = 'Gaming Laptop';

-- 5. Remove nested field
UPDATE products
SET metadata = metadata #- '{specs,gpu}'
WHERE name = 'Gaming Laptop';

-- 6. Merge JSON objects
UPDATE user_preferences
SET settings = settings || '{"new_feature": true}'::jsonb
WHERE user_id = 1;
```

**Questions to Consider:**
- What's the difference between `jsonb_set` and `||` for updates?
- How do you safely update arrays without losing existing data?
- When would you use `#-` vs `-` for removing data?

### Option C: Real-World Scenarios

Apply JSONB concepts to practical use cases.

#### Scenario 1: E-commerce Product Catalog
```sql
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
```

#### Scenario 2: User Analytics and Preferences
```sql
-- Track user behavior with flexible event data
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
```

## Performance and Indexing

### Understanding JSONB Indexing

#### GIN Indexes for JSONB
```sql
-- Create a GIN index for general JSONB operations
CREATE INDEX idx_products_metadata_gin ON products USING GIN (metadata);

-- Test the index with containment queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT name FROM products 
WHERE metadata @> '{"brand": "TechCorp"}';

-- Create expression indexes for specific paths
CREATE INDEX idx_products_brand ON products USING BTREE ((metadata->>'brand'));
CREATE INDEX idx_products_rating ON products USING BTREE (((metadata->'ratings'->>'average')::NUMERIC));

-- Test the expression indexes
EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM products 
WHERE metadata->>'brand' = 'TechCorp';

EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM products 
WHERE (metadata->'ratings'->>'average')::NUMERIC > 4.0;
```

#### Advanced Indexing Strategies
```sql
-- Partial indexes for specific conditions
CREATE INDEX idx_products_high_rated ON products USING GIN (metadata)
WHERE (metadata->'ratings'->>'average')::NUMERIC > 4.0;

-- Multi-column indexes combining relational and JSONB data
CREATE INDEX idx_products_category_brand ON products (category, (metadata->>'brand'));

-- Functional indexes for complex expressions
CREATE INDEX idx_products_price_with_discount ON products 
USING BTREE (
    CASE 
        WHEN metadata ? 'discount' 
        THEN price * (1 - (metadata->>'discount')::NUMERIC / 100)
        ELSE price 
    END
);
```

### Performance Testing and Optimization

#### Benchmarking Queries
```sql
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
FROM generate_series(1, 10000);

-- Compare query performance with and without indexes
-- Without index (drop it first)
DROP INDEX IF EXISTS idx_products_metadata_gin;

EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM products 
WHERE metadata @> '{"brand": "Brand5"}';

-- With index
CREATE INDEX idx_products_metadata_gin ON products USING GIN (metadata);

EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM products 
WHERE metadata @> '{"brand": "Brand5"}';
```

## Best Practices and Patterns

### 1. Schema Design Patterns

#### Hybrid Approach (Recommended)
```sql
-- Store frequently queried fields as columns, flexible data as JSONB
CREATE TABLE hybrid_products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    category TEXT NOT NULL,
    brand TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Flexible attributes in JSONB
    specifications JSONB,
    metadata JSONB,
    
    -- Create indexes on both relational and JSONB fields
    INDEX idx_category_brand (category, brand),
    INDEX idx_specifications_gin USING GIN (specifications)
);
```

#### Document-Centric Approach
```sql
-- Store everything in JSONB with minimal relational structure
CREATE TABLE document_products (
    id SERIAL PRIMARY KEY,
    document JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Use generated columns for frequently accessed fields
ALTER TABLE document_products 
ADD COLUMN name TEXT GENERATED ALWAYS AS (document->>'name') STORED,
ADD COLUMN price NUMERIC GENERATED ALWAYS AS ((document->>'price')::NUMERIC) STORED,
ADD COLUMN category TEXT GENERATED ALWAYS AS (document->>'category') STORED;

-- Index the generated columns
CREATE INDEX idx_document_products_category ON document_products (category);
CREATE INDEX idx_document_products_price ON document_products (price);
```

### 2. Data Validation and Constraints

#### JSON Schema Validation
```sql
-- Create a function to validate product JSON schema
CREATE OR REPLACE FUNCTION validate_product_json(data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check required fields
    IF NOT (data ? 'name' AND data ? 'price' AND data ? 'category') THEN
        RETURN FALSE;
    END IF;
    
    -- Validate data types
    IF jsonb_typeof(data->'price') != 'number' THEN
        RETURN FALSE;
    END IF;
    
    -- Validate price range
    IF (data->>'price')::NUMERIC <= 0 THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add a check constraint
ALTER TABLE products 
ADD CONSTRAINT check_valid_metadata 
CHECK (validate_product_json(metadata));
```

#### Using JSON Schema (PostgreSQL 14+)
```sql
-- Define a JSON schema
CREATE TABLE product_schemas (
    schema_name TEXT PRIMARY KEY,
    schema_definition JSONB
);

INSERT INTO product_schemas VALUES ('product_v1', '{
    "type": "object",
    "required": ["name", "price", "category"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "price": {"type": "number", "minimum": 0},
        "category": {"type": "string"},
        "rating": {"type": "number", "minimum": 0, "maximum": 5}
    }
}');
```

### 3. Migration Strategies

#### Migrating from Relational to JSONB
```sql
-- Original relational table
CREATE TABLE old_products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    price NUMERIC,
    brand TEXT,
    category TEXT,
    ram TEXT,
    storage TEXT,
    cpu TEXT
);

-- New JSONB table
CREATE TABLE new_products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    price NUMERIC,
    metadata JSONB
);

-- Migration script
INSERT INTO new_products (id, name, price, metadata)
SELECT 
    id,
    name,
    price,
    jsonb_build_object(
        'brand', brand,
        'category', category,
        'specifications', jsonb_build_object(
            'ram', ram,
            'storage', storage,
            'cpu', cpu
        )
    )
FROM old_products;
```

#### Migrating from JSONB to Relational
```sql
-- Extract commonly queried fields to columns
ALTER TABLE products 
ADD COLUMN brand TEXT,
ADD COLUMN category TEXT,
ADD COLUMN rating NUMERIC;

-- Populate the new columns
UPDATE products 
SET 
    brand = metadata->>'brand',
    category = metadata->>'category',
    rating = (metadata->'ratings'->>'average')::NUMERIC;

-- Create indexes on the new columns
CREATE INDEX idx_products_brand_new ON products (brand);
CREATE INDEX idx_products_category_new ON products (category);
CREATE INDEX idx_products_rating_new ON products (rating);

-- Remove the data from JSONB to avoid duplication
UPDATE products 
SET metadata = metadata - 'brand' - 'category' #- '{ratings,average}';
```

## Troubleshooting Common Issues

### 1. Performance Problems
```sql
-- Identify slow JSONB queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE query ILIKE '%metadata%'
ORDER BY mean_exec_time DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename = 'products';
```

### 2. Data Type Issues
```sql
-- Handle NULL values in JSONB
SELECT name, COALESCE(metadata->>'rating', 'No rating') AS rating
FROM products;

-- Safe numeric conversion
SELECT name,
    CASE 
        WHEN metadata ? 'price' AND jsonb_typeof(metadata->'price') = 'number'
        THEN (metadata->>'price')::NUMERIC
        ELSE NULL
    END AS extracted_price
FROM products;
```

### 3. Complex Queries
```sql
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
```

## Real-World Applications

### 1. Content Management System
```sql
CREATE TABLE cms_content (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Store different content types with flexible metadata
INSERT INTO cms_content (slug, title, content_type, metadata) VALUES
('getting-started-postgresql', 'Getting Started with PostgreSQL', 'article', '{
    "author": "Jane Doe",
    "tags": ["postgresql", "database", "tutorial"],
    "seo": {
        "meta_description": "Learn PostgreSQL basics",
        "keywords": ["postgresql", "sql", "database"]
    },
    "content": {
        "sections": [
            {"title": "Introduction", "content": "PostgreSQL is..."},
            {"title": "Installation", "content": "To install..."}
        ]
    },
    "reading_time": 10,
    "difficulty": "beginner"
}');
```

### 2. Configuration Management
```sql
CREATE TABLE app_configurations (
    id SERIAL PRIMARY KEY,
    app_name TEXT NOT NULL,
    environment TEXT NOT NULL,
    config_version INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(app_name, environment, config_version)
);

-- Store application configurations
INSERT INTO app_configurations (app_name, environment, config_version, configuration) VALUES
('web-app', 'production', 1, '{
    "database": {
        "host": "prod-db.example.com",
        "port": 5432,
        "ssl": true,
        "pool_size": 20
    },
    "cache": {
        "provider": "redis",
        "ttl": 3600,
        "cluster_nodes": ["redis1.example.com", "redis2.example.com"]
    },
    "features": {
        "new_ui": true,
        "analytics": true,
        "beta_features": false
    },
    "limits": {
        "max_file_size": 10485760,
        "rate_limit": 1000
    }
}');
```

### 3. Multi-tenant SaaS Application
```sql
CREATE TABLE tenant_settings (
    tenant_id UUID PRIMARY KEY,
    tenant_name TEXT NOT NULL,
    subscription_tier TEXT NOT NULL,
    settings JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Store per-tenant configurations
INSERT INTO tenant_settings (tenant_id, tenant_name, subscription_tier, settings) VALUES
(gen_random_uuid(), 'Acme Corp', 'enterprise', '{
    "branding": {
        "logo_url": "https://acme.com/logo.png",
        "primary_color": "#0066cc",
        "custom_domain": "acme.myapp.com"
    },
    "limits": {
        "max_users": 1000,
        "storage_gb": 100,
        "api_calls_per_hour": 10000
    },
    "features": {
        "sso": true,
        "audit_logs": true,
        "custom_fields": true,
        "api_access": true
    },
    "integrations": {
        "slack": {"webhook_url": "https://hooks.slack.com/..."},
        "salesforce": {"enabled": true, "sync_frequency": "hourly"}
    }
}');
```

## Success Criteria

You've completed the lab when you can:
1. ✅ Explain the difference between JSON and JSONB and when to use each
2. ✅ Create tables with JSONB columns and insert complex nested data
3. ✅ Query JSONB data using various operators (`->`, `->>`, `@>`, `?`, etc.)
4. ✅ Update and manipulate JSONB data using functions like `jsonb_set`
5. ✅ Create appropriate indexes for JSONB data (GIN, expression indexes)
6. ✅ Design hybrid schemas that combine relational and document patterns
7. ✅ Implement real-world use cases using JSONB effectively

## Next Steps

Once you master these concepts:
1. Explore PostgreSQL's full-text search with JSONB data
2. Learn about JSONB aggregation functions
3. Study advanced indexing strategies for large datasets
4. Implement data validation using JSON Schema
5. Practice with time-series data stored in JSONB format
6. Explore integration with application frameworks

## Key Insights

After completing this lab, you should understand:

1. **JSONB is PostgreSQL's superpower** - it bridges relational and document databases
2. **Indexing strategy is crucial** - GIN indexes for containment, expression indexes for specific paths
3. **Hybrid schemas work best** - combine relational columns for frequently queried fields with JSONB for flexibility
4. **Performance requires planning** - understand your query patterns before designing your schema
5. **Validation is important** - implement constraints and validation functions for data quality
6. **Migration is possible** - you can evolve between relational and JSONB approaches

Remember: **JSONB gives you the flexibility of NoSQL with the power of SQL!** 
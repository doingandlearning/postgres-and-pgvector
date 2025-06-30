# PostgreSQL JSONB Cheat Sheet

## Quick Reference for JSON and JSONB Operations

### Basic Operators

| Operator | Description | Example | Result |
|----------|-------------|---------|--------|
| `->` | Get JSON object field as JSON | `'{"a":1}'::jsonb -> 'a'` | `1` |
| `->>` | Get JSON object field as text | `'{"a":1}'::jsonb ->> 'a'` | `"1"` |
| `#>` | Get JSON object at path as JSON | `'{"a":{"b":1}}'::jsonb #> '{a,b}'` | `1` |
| `#>>` | Get JSON object at path as text | `'{"a":{"b":1}}'::jsonb #>> '{a,b}'` | `"1"` |

### Existence Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `?` | Does key exist? | `'{"a":1}'::jsonb ? 'a'` → `true` |
| `?|` | Do any keys exist? | `'{"a":1}'::jsonb ?| array['a','b']` → `true` |
| `?&` | Do all keys exist? | `'{"a":1}'::jsonb ?& array['a','b']` → `false` |

### Containment Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `@>` | Contains (left contains right) | `'{"a":1,"b":2}'::jsonb @> '{"a":1}'` → `true` |
| `<@` | Contained by (left contained in right) | `'{"a":1}'::jsonb <@ '{"a":1,"b":2}'` → `true` |

### Path Operators (PostgreSQL 12+)

| Operator | Description | Example |
|----------|-------------|---------|
| `@?` | Does path exist? | `'{"a":{"b":1}}'::jsonb @? '$.a.b'` → `true` |
| `@@` | Does path match predicate? | `'{"a":2}'::jsonb @@ '$.a > 1'` → `true` |

### Modification Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `\|\|` | Concatenate/merge | `'{"a":1}'::jsonb \|\| '{"b":2}'` → `{"a":1,"b":2}` |
| `-` | Remove key | `'{"a":1,"b":2}'::jsonb - 'a'` → `{"b":2}` |
| `#-` | Remove at path | `'{"a":{"b":1}}'::jsonb #- '{a,b}'` → `{"a":{}}` |

## Essential Functions

### Creation Functions

```sql
-- Build JSON object from key-value pairs
jsonb_build_object('key1', 'value1', 'key2', 'value2')
-- Result: {"key1": "value1", "key2": "value2"}

-- Build JSON array from values
jsonb_build_array('value1', 'value2', 'value3')
-- Result: ["value1", "value2", "value3"]

-- Convert row to JSON
row_to_json(row(1, 'hello'))
-- Result: {"f1": 1, "f2": "hello"}
```

### Inspection Functions

```sql
-- Get all keys from top level
jsonb_object_keys('{"a":1,"b":2}'::jsonb)
-- Result: "a", "b" (as rows)

-- Get data type of JSON value
jsonb_typeof('{"a":1}'::jsonb -> 'a')
-- Result: "number"

-- Get array length
jsonb_array_length('[1,2,3]'::jsonb)
-- Result: 3

-- Pretty print JSON
jsonb_pretty('{"a":1,"b":2}'::jsonb)
-- Result: formatted JSON string
```

### Manipulation Functions

```sql
-- Set value at path
jsonb_set('{"a":1}'::jsonb, '{b}', '2'::jsonb)
-- Result: {"a": 1, "b": 2}

-- Insert value (only if path doesn't exist)
jsonb_insert('{"a":1}'::jsonb, '{b}', '2'::jsonb)
-- Result: {"a": 1, "b": 2}

-- Strip nulls
jsonb_strip_nulls('{"a":1,"b":null}'::jsonb)
-- Result: {"a": 1}
```

### Array Functions

```sql
-- Expand array to rows (as JSON)
jsonb_array_elements('[1,2,3]'::jsonb)
-- Result: 1, 2, 3 (as JSON values)

-- Expand array to rows (as text)
jsonb_array_elements_text('["a","b","c"]'::jsonb)
-- Result: "a", "b", "c" (as text)

-- Expand object to key-value pairs
jsonb_each('{"a":1,"b":2}'::jsonb)
-- Result: ("a", 1), ("b", 2)

-- Expand object to key-value pairs (text values)
jsonb_each_text('{"a":1,"b":2}'::jsonb)
-- Result: ("a", "1"), ("b", "2")
```

## Common Patterns

### 1. Extracting Data

```sql
-- Basic field extraction
SELECT metadata->>'name' AS product_name FROM products;

-- Nested field extraction
SELECT metadata->'specs'->>'cpu' AS processor FROM products;

-- Array element extraction
SELECT metadata->'features'->>0 AS first_feature FROM products;

-- Safe extraction with COALESCE
SELECT COALESCE(metadata->>'rating', 'No rating') FROM products;
```

### 2. Filtering Data

```sql
-- Filter by field existence
SELECT * FROM products WHERE metadata ? 'warranty';

-- Filter by field value
SELECT * FROM products WHERE metadata->>'brand' = 'Apple';

-- Filter by nested field
SELECT * FROM products WHERE metadata->'specs'->>'ram' = '16GB';

-- Filter by containment
SELECT * FROM products WHERE metadata @> '{"brand": "Apple"}';

-- Filter by array containment
SELECT * FROM products WHERE metadata->'features' @> '["WiFi"]';
```

### 3. Updating Data

```sql
-- Add new field
UPDATE products 
SET metadata = jsonb_set(metadata, '{discount}', '10'::jsonb)
WHERE id = 1;

-- Update nested field
UPDATE products 
SET metadata = jsonb_set(metadata, '{specs, ram}', '"32GB"'::jsonb)
WHERE id = 1;

-- Add to array
UPDATE products 
SET metadata = jsonb_set(
    metadata, 
    '{features}', 
    (metadata->'features') || '["New Feature"]'::jsonb
)
WHERE id = 1;

-- Merge objects
UPDATE products 
SET metadata = metadata || '{"new_field": "value"}'::jsonb
WHERE id = 1;

-- Remove field
UPDATE products 
SET metadata = metadata - 'old_field'
WHERE id = 1;

-- Remove nested field
UPDATE products 
SET metadata = metadata #- '{specs,old_spec}'
WHERE id = 1;
```

### 4. Aggregating Data

```sql
-- Count by JSON field
SELECT metadata->>'category', COUNT(*)
FROM products
GROUP BY metadata->>'category';

-- Average of numeric JSON field
SELECT AVG((metadata->>'rating')::NUMERIC)
FROM products
WHERE metadata ? 'rating';

-- Collect JSON objects
SELECT jsonb_agg(metadata)
FROM products
WHERE metadata->>'brand' = 'Apple';

-- Merge all JSON objects
SELECT jsonb_object_agg(id, metadata)
FROM products;
```

### 5. Working with Arrays

```sql
-- Expand array to rows
SELECT product_id, feature
FROM products,
LATERAL jsonb_array_elements_text(metadata->'features') AS feature;

-- Filter by array element
SELECT * FROM products
WHERE metadata->'features' @> '["WiFi"]';

-- Array length
SELECT name, jsonb_array_length(metadata->'features') AS feature_count
FROM products
WHERE metadata ? 'features';

-- Array concatenation
UPDATE products
SET metadata = jsonb_set(
    metadata,
    '{features}',
    (metadata->'features') || '["New Feature"]'::jsonb
);
```

## Indexing Strategies

### 1. GIN Index (General Purpose)

```sql
-- Index entire JSONB column
CREATE INDEX idx_metadata_gin ON products USING GIN (metadata);

-- Use for containment queries
SELECT * FROM products WHERE metadata @> '{"brand": "Apple"}';
```

### 2. Expression Index (Specific Fields)

```sql
-- Index specific field
CREATE INDEX idx_brand ON products USING BTREE ((metadata->>'brand'));

-- Index nested field
CREATE INDEX idx_cpu ON products USING BTREE ((metadata->'specs'->>'cpu'));

-- Index with type casting
CREATE INDEX idx_rating ON products USING BTREE (((metadata->>'rating')::NUMERIC));
```

### 3. Partial Index

```sql
-- Index only rows meeting condition
CREATE INDEX idx_high_rated ON products USING GIN (metadata)
WHERE (metadata->>'rating')::NUMERIC > 4.0;
```

### 4. Multi-column Index

```sql
-- Combine relational and JSONB columns
CREATE INDEX idx_category_brand ON products (category, (metadata->>'brand'));
```

## Performance Tips

### 1. Use Appropriate Operators

```sql
-- FAST: Use containment for exact matches
WHERE metadata @> '{"brand": "Apple"}'

-- SLOW: String comparison on entire JSON
WHERE metadata::text LIKE '%Apple%'

-- FAST: Use expression index
WHERE metadata->>'brand' = 'Apple'  -- with index on (metadata->>'brand')
```

### 2. Type Casting

```sql
-- Cast to appropriate type for comparisons
WHERE (metadata->>'price')::NUMERIC > 100
WHERE (metadata->>'created_at')::TIMESTAMP > '2024-01-01'
WHERE (metadata->>'active')::BOOLEAN = true
```

### 3. Null Handling

```sql
-- Safe null handling
WHERE metadata->>'field' IS NOT NULL
WHERE COALESCE(metadata->>'field', 'default') = 'value'
```

## Common Mistakes to Avoid

### 1. Type Issues

```sql
-- WRONG: Comparing numbers as strings
WHERE metadata->>'price' > '100'  -- String comparison!

-- RIGHT: Cast to numeric
WHERE (metadata->>'price')::NUMERIC > 100
```

### 2. Index Usage

```sql
-- WRONG: Won't use expression index
WHERE upper(metadata->>'brand') = 'APPLE'

-- RIGHT: Create functional index or use exact match
WHERE metadata->>'brand' = 'Apple'
```

### 3. Array Operations

```sql
-- WRONG: Checking if array contains string (type mismatch)
WHERE metadata->'tags' @> 'important'

-- RIGHT: Check if array contains JSON string
WHERE metadata->'tags' @> '"important"'
```

## Real-World Examples

### E-commerce Product Catalog

```sql
-- Find products with specific specs and price range
SELECT name, metadata->'specs' as specs
FROM products
WHERE metadata @> '{"category": "laptop"}'
  AND (metadata->>'price')::NUMERIC BETWEEN 1000 AND 2000
  AND metadata->'specs' @> '{"ram": "16GB"}';

-- Aggregate by brand with average rating
SELECT 
    metadata->>'brand' as brand,
    AVG((metadata->>'rating')::NUMERIC) as avg_rating,
    COUNT(*) as product_count
FROM products
WHERE metadata ? 'rating'
GROUP BY metadata->>'brand'
ORDER BY avg_rating DESC;
```

### User Preferences

```sql
-- Find users with specific notification settings
SELECT user_id, username
FROM user_preferences
WHERE settings @> '{"notifications": {"email": true, "push": false}}';

-- Update theme for all users
UPDATE user_preferences
SET settings = jsonb_set(settings, '{theme}', '"dark"'::jsonb)
WHERE settings->>'theme' = 'light';
```

### Analytics Events

```sql
-- Find conversion funnel
SELECT 
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users
FROM events
WHERE event_data->>'product_id' = 'LAPTOP-001'
GROUP BY event_type
ORDER BY event_count DESC;

-- Average session duration by page
SELECT 
    event_data->>'page' as page,
    AVG((event_data->>'duration')::INTEGER) as avg_duration
FROM events
WHERE event_type = 'page_view'
  AND event_data ? 'duration'
GROUP BY event_data->>'page';
```

## Troubleshooting

### Check Index Usage

```sql
-- See if query uses index
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM products WHERE metadata @> '{"brand": "Apple"}';
```

### Validate JSON Structure

```sql
-- Check for required fields
SELECT id, name
FROM products
WHERE NOT (metadata ? 'brand' AND metadata ? 'price');

-- Validate data types
SELECT id, name, metadata->>'price'
FROM products
WHERE metadata ? 'price' 
  AND jsonb_typeof(metadata->'price') != 'number';
```

### Performance Analysis

```sql
-- Find slow JSONB queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE query ILIKE '%metadata%'
ORDER BY mean_exec_time DESC;
```

This cheat sheet covers the most common JSONB operations you'll need for building applications with PostgreSQL's JSON capabilities! 
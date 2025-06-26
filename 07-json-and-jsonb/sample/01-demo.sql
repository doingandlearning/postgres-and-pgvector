SELECT name, item_data->'authors' AS author
FROM items;
-- ->> extracts a TEXT value (useful for direct display).
SELECT name, item_data
FROM items
WHERE item_data->>'subject' = 'programming';
-- This finds only items where "category": "programming".
SELECT name, item_data
FROM items
WHERE item_data ? 'discount';
-- This finds only items that have a "discount" key in item_data.
UPDATE items
SET item_data = jsonb_set(item_data, '{price}', to_jsonb(29.99))
WHERE item_data->>'subject' = 'programming';
-- Updates the "price" field for all programming books.
UPDATE items
SET item_data = jsonb_set(item_data, '{discount}', '10.0'::jsonb);
-- Adds a "discount": 10.0 key to all records.
UPDATE items
SET item_data = item_data - 'discount';
--  Removes "discount" from all records.
SELECT name, item_data
FROM items
WHERE item_data @> '{"subject": "web_development"}';
-- @> checks if the given JSON structure exists within item_data.
CREATE INDEX idx_items_jsonb ON items USING GIN (item_data);
-- A GIN index improves key lookups (?), containment queries (@>), and path queries (jsonb_path_query()).
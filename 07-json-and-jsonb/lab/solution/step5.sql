SELECT name, metadata
FROM products
WHERE metadata::TEXT ILIKE '%SSD%';
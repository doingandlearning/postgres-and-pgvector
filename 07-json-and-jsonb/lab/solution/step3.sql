SELECT name, metadata->>'brand' AS brand
FROM products;

SELECT name, metadata->>'battery' AS battery
FROM products
WHERE metadata->>'battery' > '5000mAh';

SELECT name, metadata->>'battery' AS battery
FROM products
WHERE (regexp_replace(metadata->>'battery', '[^0-9]', '', 'g'))::INTEGER > 5000;

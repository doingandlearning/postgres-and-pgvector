UPDATE products
SET metadata = jsonb_set(metadata, '{weight}', '"2kg"')
WHERE name = 'Laptop X1';

UPDATE products
SET metadata = jsonb_set(metadata, '{battery}', '"5000mAh"')
WHERE name = 'Phone Z9';


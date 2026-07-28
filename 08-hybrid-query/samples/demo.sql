-- ============================================================================
-- demo.sql -- Live demo: why hybrid queries beat pure vector search
-- ============================================================================
--
-- Run each block one at a time (psql, or paste into your SQL client) and
-- compare the result sets out loud with the room. No new data or Python
-- needed -- everything here uses the `items` table you already populated
-- in Module 03/05, and reuses an existing row's embedding as the "query"
-- instead of generating a fresh one, so this runs with zero setup.
--
-- The point isn't "hybrid gives better numbers" -- it's that pure vector
-- similarity has NO way to enforce a hard rule (a subject, a price cap,
-- a stock flag). It can only ever say "these are semantically close."
-- Hybrid queries add relational/JSONB filtering back in alongside that.
--
-- Connect first:
--   docker exec -it pgvector-db psql -U postgres -d pgvector

-- Add random prices.

UPDATE items
SET item_data = jsonb_set(
    item_data,
    '{price}',
    to_jsonb(round((random() * 80 + 10)::numeric, 2))
);

-- ============================================================================
-- 0. Pick a reference item to use as "the query"
-- ============================================================================
-- Look at what you've got before you run the rest -- this also doubles as
-- a quick reminder of the subject/price spread in the data.

SELECT name, item_data->>'subject' AS subject, item_data->>'price' AS price, item_data->>'first_publish_year' as year
FROM items
ORDER BY item_data->>'subject', (item_data->>'price')::numeric;

-- ============================================================================
-- 1. PURE VECTOR SEARCH -- no filters, just cosine similarity
-- ============================================================================
-- "Find things like this book" -- nothing here can stop a wildly
-- differently-priced or differently-subjected item from ranking highly
-- if the embedding happens to be close.

WITH reference_item AS (
    SELECT embedding, item_data->>'subject' AS subject, item_data->>'price' AS price
    FROM items
    WHERE item_data->>'subject' = 'programming'
    ORDER BY (item_data->>'price')::numeric ASC
    LIMIT 1
)
SELECT
    i.name,
    i.item_data->>'subject' AS subject,
    i.item_data->>'price' AS price,
    i.item_data->>'first_publish_year' AS year,
    ROUND((i.embedding <=> r.embedding)::numeric, 4) AS distance
FROM items i, reference_item r
ORDER BY distance ASC
LIMIT 5;

-- Talking point: point out anything in the top 5 that's a different
-- subject, or a much higher price, than the reference item. That's the
-- gap hybrid search closes.

-- ============================================================================
-- 2. HYBRID SEARCH -- vector similarity + a hard relational constraint
-- ============================================================================
-- Same ranking mechanism, but now a real business rule (same subject
-- only) is enforced with a WHERE clause instead of hoped for.

WITH reference_item AS (
    SELECT embedding, item_data->>'subject' AS subject
    FROM items
    WHERE item_data->>'subject' = 'programming'
    ORDER BY (item_data->>'price')::numeric ASC
    LIMIT 1
)
SELECT
    i.name,
    i.item_data->>'subject' AS subject,
    i.item_data->>'price' AS price,
    ROUND((i.embedding <=> r.embedding)::numeric, 4) AS distance
FROM items i, reference_item r
WHERE i.item_data->>'subject' = r.subject   -- <-- the constraint pure vector search can't express
ORDER BY distance ASC
LIMIT 5;

-- ============================================================================
-- 3. HYBRID SEARCH -- vector similarity + a price ceiling
-- ============================================================================
-- Same idea, different constraint: cap results to a price range instead
-- of a subject match. Useful if the subject demo above doesn't show a
-- clean contrast in your data -- try this one instead, or run both.

WITH reference_item AS (
    SELECT embedding, (item_data->>'price')::numeric AS price
    FROM items
    WHERE item_data->>'subject' = 'programming'
    ORDER BY (item_data->>'price')::numeric ASC
    LIMIT 1
)
SELECT
    i.name,
    i.item_data->>'subject' AS subject,
    i.item_data->>'price' AS price,
    ROUND((i.embedding <=> r.embedding)::numeric, 4) AS distance
FROM items i, reference_item r
WHERE (i.item_data->>'price')::numeric <= r.price * 1.5 -- <-- within 50% of the reference price
ORDER BY distance ASC
LIMIT 5;

-- ============================================================================
-- 4. HYBRID SEARCH -- weighted score fusion instead of a hard filter
-- ============================================================================
-- Sometimes you don't want to exclude results outright, just nudge the
-- ranking. This combines vector distance with a same-subject "boost" --
-- a softer version of constraints 2/3 above. (Same pattern as the
-- Personalized Ranking example later in this module.)

WITH reference_item AS (
    SELECT embedding, item_data->>'subject' AS subject
    FROM items
    WHERE item_data->>'subject' = 'programming'
    ORDER BY (item_data->>'price')::numeric ASC
    LIMIT 1
)
SELECT
    i.name,
    i.item_data->>'subject' AS subject,
    i.item_data->>'price' AS price,
    ROUND((i.embedding <=> r.embedding)::numeric, 4) AS raw_distance,
    ROUND(
        (i.embedding <=> r.embedding)::numeric *
        CASE WHEN i.item_data->>'subject' = r.subject THEN 0.8 ELSE 1.0 END *
        CASE WHEN (i.item_data->>'first_publish_year')::int < 2000 THEN 1 ELSE 0.8 END,
    4) AS adjusted_score
FROM items i, reference_item r
ORDER BY adjusted_score ASC
LIMIT 15;
-- ============================================================================
-- Debrief prompt for the room
-- ============================================================================
-- Ask: "Which of these four result sets would you actually want to ship
-- to a customer?" The answer is never #1 alone -- that's the whole
-- argument for this module in one sentence.

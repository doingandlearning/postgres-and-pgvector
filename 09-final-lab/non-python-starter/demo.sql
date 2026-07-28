-- ============================================================================
-- demo.sql -- Live demo: the capstone's payoff in one screen, not 10 steps
-- ============================================================================
--
-- Run each block one at a time and narrate the result sets. Assumes
-- Steps 1-3 of README.md have already happened (schema created, sample
-- tickets loaded, `python embed_text.py --bulk` run) -- if support_tickets
-- has real embeddings already, this needs nothing else.
--
-- The story across these four blocks: vector search alone -> add a hard
-- business rule -> pull in JSONB structure -> combine all three signals
-- in one query, which is the actual shape of the finished system.
--
-- Connect first:
--   docker exec -it pgvector-db psql -U postgres -d pgvector

-- ============================================================================
-- 0. What have we got?
-- ============================================================================

SELECT ticket_number, issue_description, priority, status, metadata->>'tags' AS tags
FROM support_tickets
ORDER BY priority DESC;

-- ============================================================================
-- 1. PURE VECTOR SEARCH -- "find tickets like this one"
-- ============================================================================
-- Uses an existing ticket's own embedding as the "new issue" so there's
-- nothing to generate live. No business logic here at all -- just "what's
-- semantically closest," including tickets that are still open, low
-- priority, or already closed as a duplicate.

WITH reference_ticket AS (
    SELECT embedding, ticket_number
    FROM support_tickets
    ORDER BY created_at DESC
    LIMIT 1
)
SELECT
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.status,
    ROUND((st.embedding <=> r.embedding)::numeric, 4) AS distance
FROM support_tickets st, reference_ticket r
WHERE st.ticket_number != r.ticket_number
ORDER BY distance ASC
LIMIT 5;

-- Talking point: notice status/priority are along for the ride here, not
-- driving anything. A support agent wants "similar AND actually useful"
-- -- that needs a rule, not just a ranking.

-- ============================================================================
-- 2. HYBRID -- vector similarity + a hard business rule
-- ============================================================================
-- Same ranking, but now: only resolved tickets count as candidate
-- solutions. An agent doesn't want to be pointed at another open,
-- unsolved problem.

WITH reference_ticket AS (
    SELECT embedding, ticket_number
    FROM support_tickets
    ORDER BY created_at DESC
    LIMIT 1
)
SELECT
    st.ticket_number,
    st.issue_description,
    st.status,
    st.metadata->>'resolution_steps' AS resolution_steps,
    ROUND((st.embedding <=> r.embedding)::numeric, 4) AS distance
FROM support_tickets st, reference_ticket r
WHERE st.ticket_number != r.ticket_number
  AND st.status = 'resolved'   -- <-- the rule pure vector search can't express
ORDER BY distance ASC
LIMIT 5;

-- ============================================================================
-- 3. JSONB -- pulling structured insight out of the match
-- ============================================================================
-- The similarity search found *a* ticket -- JSONB metadata is what turns
-- that into an actual answer: tags, resolution steps, how many users
-- were affected, without a separate table for every one of those fields.

SELECT
    ticket_number,
    metadata->>'root_cause' AS root_cause,
    metadata->'tags' AS tags,
    metadata->'resolution_steps' AS resolution_steps,
    (metadata->>'affected_users')::int AS affected_users
FROM support_tickets
WHERE status = 'resolved'
ORDER BY (metadata->>'affected_users')::int DESC NULLS LAST;

-- ============================================================================
-- 4. ALL THREE TOGETHER -- the shape of the real system
-- ============================================================================
-- Vector similarity + relational filtering + JSONB extraction, in one
-- query. This is the actual capstone: everything above, combined.

WITH reference_ticket AS (
    SELECT embedding, ticket_number, priority
    FROM support_tickets
    ORDER BY created_at DESC
    LIMIT 1
)
SELECT
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.metadata->>'resolution_steps' AS suggested_fix,
    st.metadata->'tags' AS tags,
    ROUND((st.embedding <=> r.embedding)::numeric, 4) AS similarity
FROM support_tickets st, reference_ticket r
WHERE st.ticket_number != r.ticket_number
  AND st.status = 'resolved'
  AND (st.priority = r.priority OR st.priority IN ('high', 'critical'))
ORDER BY similarity ASC
LIMIT 3;

-- ============================================================================
-- Debrief prompt for the room
-- ============================================================================
-- Ask: "Which of these four queries is the one you'd actually put in
-- front of a support agent?" Block 4 is the whole two-day course in one
-- query -- semantic search, business rules, and flexible metadata,
-- together.

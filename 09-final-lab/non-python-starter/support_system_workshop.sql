-- ============================================================================
-- Final Lab: AI-Powered Support System Workshop
-- Complete SQL implementation combining all course concepts
-- ============================================================================

-- Connect to your PostgreSQL database first:
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- ============================================================================
-- SECTION 1: SCHEMA DESIGN AND SETUP
-- ============================================================================

-- Create comprehensive support system schema
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    issue_description TEXT NOT NULL,
    customer_id INTEGER NOT NULL,
    department VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) CHECK (priority IN ('low', 'medium', 'high', 'critical')) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolution_time_hours INTEGER,
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(50) DEFAULT 'standard',
    subscription_tier VARCHAR(20) DEFAULT 'basic',
    account_manager VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    article_title VARCHAR(200) NOT NULL,
    article_content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    tags TEXT[],
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT NOW(),
    view_count INTEGER DEFAULT 0,
    helpfulness_score NUMERIC(3,2) DEFAULT 0.0
);

-- Add relationships (with error handling for existing constraints)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_customer' 
        AND conrelid = 'support_tickets'::regclass
    ) THEN
        ALTER TABLE support_tickets 
        ADD CONSTRAINT fk_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(id);
    END IF;
END $$;

-- ============================================================================
-- SECTION 2: SAMPLE DATA LOADING
-- ============================================================================

-- Insert sample customers
INSERT INTO customers (id, customer_name, customer_type, subscription_tier, account_manager) 
VALUES
(1, 'TechCorp Solutions', 'enterprise', 'premium', 'Sarah Johnson'),
(2, 'StartupXYZ', 'startup', 'standard', 'Mike Chen'),
(3, 'Global Industries', 'enterprise', 'enterprise', 'Sarah Johnson'),
(4, 'Local Business Inc', 'small_business', 'basic', 'Alex Rodriguez'),
(5, 'Innovation Labs', 'startup', 'standard', 'Mike Chen')
ON CONFLICT (id) DO NOTHING;

-- Insert comprehensive support ticket data
INSERT INTO support_tickets (
    ticket_number, issue_description, customer_id, department, category, 
    priority, status, created_at, resolved_at, resolution_time_hours, satisfaction_score, metadata
) VALUES
('TK-2024-001', 'Users cannot access the main dashboard after login, getting a blank white screen', 1, 'Technical', 'Authentication', 'high', 'resolved', 
 NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days 16 hours', 8, 4, 
 '{"tags": ["dashboard", "login", "ui"], "resolution_steps": ["Clear browser cache", "Update browser", "Check user permissions"], "affected_users": 15, "root_cause": "cached CSS conflict", "assignee": "John Doe"}'),

('TK-2024-002', 'API rate limiting is causing integration failures with external payment processor', 2, 'Technical', 'API', 'critical', 'resolved', 
 NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days 12 hours', 12, 5,
 '{"tags": ["api", "rate_limit", "payments"], "resolution_steps": ["Increase rate limits", "Implement backoff strategy", "Monitor API usage"], "affected_users": 100, "root_cause": "insufficient rate limits", "assignee": "Jane Smith"}'),

('TK-2024-003', 'Email notifications are not being sent to customers after order completion', 3, 'Technical', 'Email', 'medium', 'resolved', 
 NOW() - INTERVAL '7 days', NOW() - INTERVAL '6 days', 24, 3,
 '{"tags": ["email", "notifications", "orders"], "resolution_steps": ["Check SMTP configuration", "Verify email templates", "Test delivery"], "affected_users": 50, "root_cause": "SMTP server misconfiguration", "assignee": "Bob Wilson"}'),

('TK-2024-004', 'Mobile app crashes when uploading large images, especially on older devices', 4, 'Technical', 'Mobile', 'medium', 'in_progress', 
 NOW() - INTERVAL '2 days', NULL, NULL, NULL,
 '{"tags": ["mobile", "images", "performance"], "investigation_notes": ["Reproduced on Android 8", "Memory issues with large files", "Need compression algorithm"], "affected_users": 25, "assignee": "Alice Brown"}'),

('TK-2024-005', 'Database queries are running extremely slow during peak hours affecting user experience', 1, 'Technical', 'Performance', 'high', 'open', 
 NOW() - INTERVAL '1 day', NULL, NULL, NULL,
 '{"tags": ["database", "performance", "peak_hours"], "investigation_notes": ["CPU usage spikes", "Long-running queries identified", "Need query optimization"], "affected_users": 200, "assignee": "Charlie Davis"}'),

('TK-2024-006', 'Security vulnerability reported in user authentication system allowing unauthorized access', 3, 'Security', 'Authentication', 'critical', 'resolved',
 NOW() - INTERVAL '10 days', NOW() - INTERVAL '9 days 4 hours', 20, 5,
 '{"tags": ["security", "authentication", "vulnerability"], "resolution_steps": ["Patch authentication module", "Force password resets", "Audit access logs"], "affected_users": 500, "root_cause": "SQL injection vulnerability", "assignee": "Security Team"}'),

('TK-2024-007', 'Billing system charging incorrect amounts for premium subscriptions', 2, 'Billing', 'Payments', 'high', 'resolved',
 NOW() - INTERVAL '6 days', NOW() - INTERVAL '5 days 8 hours', 16, 4,
 '{"tags": ["billing", "payments", "subscriptions"], "resolution_steps": ["Fix pricing calculation", "Process refunds", "Update billing logic"], "affected_users": 80, "root_cause": "pricing tier configuration error", "assignee": "Finance Team"}')
ON CONFLICT (ticket_number) DO NOTHING;

-- Insert knowledge base articles
INSERT INTO knowledge_base (article_title, article_content, category, tags, helpfulness_score) VALUES
('Troubleshooting Login Issues', 'Common steps to resolve authentication problems: 1. Clear browser cache and cookies, 2. Check user permissions and account status, 3. Verify browser compatibility, 4. Test with different browsers, 5. Check network connectivity', 'Authentication', ARRAY['login', 'troubleshooting', 'authentication'], 4.5),
('API Rate Limiting Best Practices', 'Guidelines for implementing and managing API rate limits: 1. Set appropriate limits based on user tiers, 2. Implement exponential backoff, 3. Provide clear error messages, 4. Monitor usage patterns, 5. Allow burst capacity for legitimate use', 'API', ARRAY['api', 'rate_limits', 'best_practices'], 4.8),
('Email Delivery Configuration', 'Step-by-step guide for configuring SMTP settings: 1. Verify SMTP server credentials, 2. Check firewall and port settings, 3. Test with external email services, 4. Configure SPF and DKIM records, 5. Monitor delivery rates', 'Email', ARRAY['email', 'smtp', 'configuration'], 4.2),
('Mobile App Performance Optimization', 'Techniques for optimizing mobile app performance: 1. Implement image compression, 2. Use lazy loading for large content, 3. Optimize database queries, 4. Cache frequently accessed data, 5. Profile memory usage', 'Mobile', ARRAY['mobile', 'performance', 'optimization'], 4.6),
('Database Performance Tuning', 'Advanced strategies for optimizing database performance: 1. Analyze slow query logs, 2. Create appropriate indexes, 3. Optimize query execution plans, 4. Implement connection pooling, 5. Monitor resource usage during peak hours', 'Performance', ARRAY['database', 'performance', 'optimization'], 4.7),
('Security Incident Response', 'Protocol for handling security vulnerabilities: 1. Immediate containment, 2. Impact assessment, 3. Patch deployment, 4. User notification, 5. Post-incident review', 'Security', ARRAY['security', 'incident_response', 'vulnerability'], 4.9)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SECTION 3: EMBEDDING GENERATION
-- ============================================================================

-- Create embedding generation function (simplified for demo)
CREATE OR REPLACE FUNCTION generate_sample_embedding(text_input TEXT)
RETURNS VECTOR(1024) AS $$
DECLARE
    embedding_array NUMERIC[];
    i INTEGER;
    text_hash BIGINT;
BEGIN
    -- Generate deterministic embedding based on text content
    text_hash := abs(hashtext(text_input));
    embedding_array := ARRAY[]::NUMERIC[];
    
    FOR i IN 1..1024 LOOP
        embedding_array := array_append(embedding_array, 
            ((text_hash + i * 7919) % 2000 - 1000) / 1000.0);
        text_hash := (text_hash * 1103515245 + 12345) % 2147483647;
    END LOOP;
    
    RETURN embedding_array::VECTOR(1024);
END;
$$ LANGUAGE plpgsql;

-- Generate embeddings for all data
UPDATE support_tickets 
SET embedding = generate_sample_embedding(issue_description)
WHERE embedding IS NULL;

UPDATE knowledge_base 
SET embedding = generate_sample_embedding(article_title || ' ' || article_content)
WHERE embedding IS NULL;

-- Verify embeddings
SELECT 
    'Embeddings Generated' as status,
    (SELECT COUNT(*) FROM support_tickets WHERE embedding IS NOT NULL) as tickets_with_embeddings,
    (SELECT COUNT(*) FROM knowledge_base WHERE embedding IS NOT NULL) as kb_articles_with_embeddings;

-- ============================================================================
-- SECTION 4: BASIC VECTOR SEARCH
-- ============================================================================

-- Exercise 4.1: Find similar tickets to a new issue
WITH new_issue AS (
    SELECT 
        'Users are experiencing login failures with authentication errors' as description,
        generate_sample_embedding('Users are experiencing login failures with authentication errors') as query_embedding
)
SELECT 
    'Basic Vector Search: Similar Tickets' as exercise_name,
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.status,
    st.metadata->>'tags' as tags,
    ROUND((st.embedding <=> ni.query_embedding)::NUMERIC, 4) as similarity_score
FROM support_tickets st, new_issue ni
WHERE st.embedding <=> ni.query_embedding < 0.8  -- Similarity threshold
ORDER BY st.embedding <=> ni.query_embedding
LIMIT 5;

-- Exercise 4.2: Knowledge base article search
WITH search_query AS (
    SELECT 
        'How to fix email delivery problems' as query,
        generate_sample_embedding('How to fix email delivery problems') as search_vector
)
SELECT 
    'Knowledge Base Search' as exercise_name,
    kb.article_title,
    kb.category,
    kb.tags,
    kb.helpfulness_score,
    ROUND((kb.embedding <=> sq.search_vector)::NUMERIC, 4) as similarity_score
FROM knowledge_base kb, search_query sq
ORDER BY kb.embedding <=> sq.search_vector
LIMIT 3;

-- ============================================================================
-- SECTION 5: HYBRID QUERIES - CORE FUNCTIONALITY
-- ============================================================================

-- Exercise 5.1: Customer-specific similar ticket search
WITH customer_issue AS (
    SELECT 
        2 as customer_id,  -- StartupXYZ
        'Payment processing is timing out during checkout' as issue,
        generate_sample_embedding('Payment processing is timing out during checkout') as issue_embedding
),
customer_context AS (
    SELECT 
        c.customer_name,
        c.subscription_tier,
        c.account_manager
    FROM customers c
    WHERE c.id = 2
)
SELECT 
    'Customer-Specific Hybrid Search' as exercise_name,
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.status,
    c.customer_name as ticket_customer,
    cc.customer_name as current_customer,
    CASE 
        WHEN st.customer_id = ci.customer_id THEN 'Same Customer'
        WHEN c.subscription_tier = cc.subscription_tier THEN 'Same Tier'
        ELSE 'Different Context'
    END as customer_match,
    st.metadata->>'resolution_steps' as solutions,
    ROUND((st.embedding <=> ci.issue_embedding)::NUMERIC, 4) as similarity_score
FROM support_tickets st
JOIN customers c ON st.customer_id = c.id
CROSS JOIN customer_issue ci
CROSS JOIN customer_context cc
WHERE st.status IN ('resolved', 'closed')
  AND st.embedding <=> ci.issue_embedding < 0.7
ORDER BY 
    CASE 
        WHEN st.customer_id = ci.customer_id THEN 1
        WHEN c.subscription_tier = cc.subscription_tier THEN 2
        ELSE 3
    END,
    st.embedding <=> ci.issue_embedding,
    st.satisfaction_score DESC NULLS LAST
LIMIT 8;

-- Exercise 5.2: Priority-based search with performance metrics
WITH urgent_search AS (
    SELECT 
        'System performance degradation during peak hours' as search_description,
        generate_sample_embedding('System performance degradation during peak hours') as search_vector
)
SELECT 
    'Priority-Based Performance Search' as exercise_name,
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.category,
    st.resolution_time_hours,
    st.satisfaction_score,
    (st.metadata->>'affected_users')::INTEGER as affected_users,
    st.metadata->>'root_cause' as root_cause,
    ROUND((st.embedding <=> us.search_vector)::NUMERIC, 4) as similarity_score,
    CASE 
        WHEN st.resolution_time_hours <= 4 THEN 'Fast Resolution'
        WHEN st.resolution_time_hours <= 24 THEN 'Standard Resolution'
        ELSE 'Slow Resolution'
    END as resolution_speed
FROM support_tickets st, urgent_search us
WHERE st.priority IN ('high', 'critical')
  AND st.status IN ('resolved', 'closed')
  AND st.embedding <=> us.search_vector < 0.8
ORDER BY 
    CASE st.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 END,
    st.embedding <=> us.search_vector,
    st.satisfaction_score DESC NULLS LAST
LIMIT 10;

-- ============================================================================
-- SECTION 6: ADVANCED JSONB ANALYTICS
-- ============================================================================

-- Exercise 6.1: Tag analysis and trending issues
WITH tag_analysis AS (
    SELECT 
        jsonb_array_elements_text(metadata->'tags') as tag,
        COUNT(*) as frequency,
        AVG(resolution_time_hours) FILTER (WHERE resolution_time_hours IS NOT NULL) as avg_resolution_hours,
        AVG(satisfaction_score) FILTER (WHERE satisfaction_score IS NOT NULL) as avg_satisfaction,
        SUM((metadata->>'affected_users')::INTEGER) FILTER (WHERE (metadata->>'affected_users')::INTEGER IS NOT NULL) as total_users_affected,
        array_agg(DISTINCT priority) as priority_levels,
        array_agg(DISTINCT category) as categories
    FROM support_tickets
    WHERE metadata ? 'tags'
      AND created_at > NOW() - INTERVAL '30 days'
    GROUP BY jsonb_array_elements_text(metadata->'tags')
)
SELECT 
    'Tag Analysis: Trending Issues' as analysis_type,
    ta.tag,
    ta.frequency,
    ROUND(ta.avg_resolution_hours, 2) as avg_resolution_hours,
    ROUND(ta.avg_satisfaction, 2) as avg_satisfaction,
    ta.total_users_affected,
    ta.priority_levels,
    ta.categories,
    CASE 
        WHEN ta.frequency >= 3 AND ta.avg_satisfaction < 3.5 THEN 'High Priority Issue'
        WHEN ta.frequency >= 2 AND ta.total_users_affected > 50 THEN 'High Impact Issue'
        WHEN ta.frequency >= 2 THEN 'Common Issue'
        ELSE 'Occasional Issue'
    END as issue_classification
FROM tag_analysis ta
ORDER BY ta.frequency DESC, ta.total_users_affected DESC NULLS LAST
LIMIT 15;

-- Exercise 6.2: Resolution pattern analysis
WITH resolution_analysis AS (
    SELECT 
        category,
        priority,
        jsonb_array_length(metadata->'resolution_steps') as step_count,
        resolution_time_hours,
        satisfaction_score,
        (metadata->>'affected_users')::INTEGER as affected_users,
        metadata->>'root_cause' as root_cause
    FROM support_tickets
    WHERE status IN ('resolved', 'closed')
      AND metadata ? 'resolution_steps'
      AND resolution_time_hours IS NOT NULL
)
SELECT 
    'Resolution Pattern Analysis' as analysis_type,
    ra.category,
    ra.priority,
    COUNT(*) as ticket_count,
    ROUND(AVG(ra.step_count), 1) as avg_steps_to_resolve,
    ROUND(AVG(ra.resolution_time_hours), 2) as avg_resolution_hours,
    ROUND(AVG(ra.satisfaction_score), 2) as avg_satisfaction,
    array_agg(DISTINCT ra.root_cause) FILTER (WHERE ra.root_cause IS NOT NULL) as common_root_causes,
    CASE 
        WHEN AVG(ra.resolution_time_hours) <= 8 THEN 'Fast'
        WHEN AVG(ra.resolution_time_hours) <= 24 THEN 'Standard'
        ELSE 'Slow'
    END as resolution_speed_category
FROM resolution_analysis ra
GROUP BY ra.category, ra.priority
HAVING COUNT(*) >= 2
ORDER BY ra.category, 
    CASE ra.priority 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        WHEN 'low' THEN 4 
    END;

-- ============================================================================
-- SECTION 7: COMPREHENSIVE SEARCH FUNCTIONS
-- ============================================================================

-- Create the main search function for the support system
CREATE OR REPLACE FUNCTION search_support_system(
    search_query TEXT,
    customer_id_filter INTEGER DEFAULT NULL,
    priority_filter TEXT DEFAULT NULL,
    status_filter TEXT DEFAULT NULL,
    category_filter TEXT DEFAULT NULL,
    include_knowledge_base BOOLEAN DEFAULT TRUE,
    similarity_threshold NUMERIC DEFAULT 0.8,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    result_type TEXT,
    result_id INTEGER,
    title TEXT,
    content TEXT,
    metadata_info JSONB,
    similarity_score NUMERIC,
    relevance_rank BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH search_embedding AS (
        SELECT generate_sample_embedding(search_query) as query_vector
    ),
    ticket_results AS (
        SELECT 
            'ticket' as type,
            st.id,
            'Ticket: ' || st.ticket_number as title,
            st.issue_description as content,
            jsonb_build_object(
                'customer', c.customer_name,
                'priority', st.priority,
                'status', st.status,
                'category', st.category,
                'resolution_time_hours', st.resolution_time_hours,
                'satisfaction_score', st.satisfaction_score,
                'tags', st.metadata->'tags',
                'resolution_steps', st.metadata->'resolution_steps',
                'affected_users', st.metadata->'affected_users'
            ) as meta,
            st.embedding <=> se.query_vector as similarity
        FROM support_tickets st
        JOIN customers c ON st.customer_id = c.id
        CROSS JOIN search_embedding se
        WHERE (customer_id_filter IS NULL OR st.customer_id = customer_id_filter)
          AND (priority_filter IS NULL OR st.priority = priority_filter)
          AND (status_filter IS NULL OR st.status = status_filter)
          AND (category_filter IS NULL OR st.category = category_filter)
          AND st.embedding <=> se.query_vector <= similarity_threshold
    ),
    kb_results AS (
        SELECT 
            'knowledge_base' as type,
            kb.id,
            'KB Article: ' || kb.article_title as title,
            LEFT(kb.article_content, 300) || '...' as content,
            jsonb_build_object(
                'category', kb.category,
                'tags', array_to_json(kb.tags),
                'view_count', kb.view_count,
                'helpfulness_score', kb.helpfulness_score
            ) as meta,
            kb.embedding <=> se.query_vector as similarity
        FROM knowledge_base kb
        CROSS JOIN search_embedding se
        WHERE include_knowledge_base
          AND (category_filter IS NULL OR kb.category = category_filter)
          AND kb.embedding <=> se.query_vector <= similarity_threshold
    ),
    all_results AS (
        SELECT * FROM ticket_results
        UNION ALL
        SELECT * FROM kb_results
    )
    SELECT 
        ar.type,
        ar.id,
        ar.title,
        ar.content,
        ar.meta,
        ROUND(ar.similarity::NUMERIC, 4),
        ROW_NUMBER() OVER (ORDER BY ar.similarity, ar.type)
    FROM all_results ar
    ORDER BY ar.similarity, ar.type
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Exercise 7.1: Test comprehensive search
SELECT * FROM search_support_system(
    'login authentication problems',
    NULL,           -- any customer
    'high',         -- high priority only
    'resolved',     -- resolved tickets only
    NULL,           -- any category
    TRUE,           -- include knowledge base
    0.8,            -- similarity threshold
    8               -- limit results
);

-- Exercise 7.2: Customer-specific search
SELECT * FROM search_support_system(
    'payment processing issues',
    2,              -- StartupXYZ customer
    NULL,           -- any priority
    NULL,           -- any status
    NULL,           -- any category
    TRUE,           -- include knowledge base
    0.7,            -- more lenient similarity
    5               -- fewer results
);

-- ============================================================================
-- SECTION 8: PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Create comprehensive indexes
CREATE INDEX IF NOT EXISTS idx_tickets_embedding_ivfflat 
ON support_tickets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_tickets_metadata_gin 
ON support_tickets USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_tickets_composite_search 
ON support_tickets (status, priority, category, customer_id);

CREATE INDEX IF NOT EXISTS idx_tickets_resolution_metrics 
ON support_tickets (resolution_time_hours, satisfaction_score) 
WHERE status IN ('resolved', 'closed');

CREATE INDEX IF NOT EXISTS idx_kb_embedding_ivfflat 
ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE INDEX IF NOT EXISTS idx_kb_category_tags 
ON knowledge_base (category) INCLUDE (tags, helpfulness_score);

-- Performance analysis query
SELECT 
    'Index Usage Analysis' as analysis_type,
    schemaname,
    relname as tablename,
    indexrelname as indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
WHERE relname IN ('support_tickets', 'knowledge_base', 'customers')
ORDER BY idx_scan DESC;

-- ============================================================================
-- SECTION 9: BUSINESS INTELLIGENCE DASHBOARD
-- ============================================================================

-- Executive dashboard query
WITH support_kpis AS (
    SELECT 
        COUNT(*) as total_tickets,
        COUNT(*) FILTER (WHERE status IN ('resolved', 'closed')) as resolved_tickets,
        COUNT(*) FILTER (WHERE priority = 'critical') as critical_tickets,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as tickets_this_week,
        AVG(resolution_time_hours) FILTER (WHERE resolution_time_hours IS NOT NULL) as avg_resolution_time,
        AVG(satisfaction_score) FILTER (WHERE satisfaction_score IS NOT NULL) as avg_satisfaction,
        SUM((metadata->>'affected_users')::INTEGER) FILTER (WHERE (metadata->>'affected_users')::INTEGER IS NOT NULL) as total_users_impacted
    FROM support_tickets
    WHERE created_at > NOW() - INTERVAL '30 days'
),
department_metrics AS (
    SELECT 
        department,
        COUNT(*) as ticket_count,
        ROUND(AVG(resolution_time_hours), 2) as avg_resolution_hours,
        ROUND(AVG(satisfaction_score), 2) as avg_satisfaction,
        COUNT(*) FILTER (WHERE priority IN ('high', 'critical')) as high_priority_count
    FROM support_tickets
    WHERE created_at > NOW() - INTERVAL '30 days'
      AND status IN ('resolved', 'closed')
    GROUP BY department
),
customer_satisfaction AS (
    SELECT 
        c.subscription_tier,
        COUNT(st.*) as ticket_count,
        ROUND(AVG(st.satisfaction_score), 2) as avg_satisfaction,
        ROUND(AVG(st.resolution_time_hours), 2) as avg_resolution_hours
    FROM support_tickets st
    JOIN customers c ON st.customer_id = c.id
    WHERE st.created_at > NOW() - INTERVAL '30 days'
      AND st.satisfaction_score IS NOT NULL
    GROUP BY c.subscription_tier
)
SELECT 
    'Support System Dashboard - Last 30 Days' as dashboard_title,
    jsonb_build_object(
        'key_metrics', jsonb_build_object(
            'total_tickets', sk.total_tickets,
            'resolution_rate_percent', ROUND((sk.resolved_tickets::NUMERIC / NULLIF(sk.total_tickets, 0)) * 100, 1),
            'critical_tickets', sk.critical_tickets,
            'tickets_this_week', sk.tickets_this_week,
            'avg_resolution_hours', ROUND(sk.avg_resolution_time, 2),
            'avg_satisfaction_score', ROUND(sk.avg_satisfaction, 2),
            'total_users_impacted', sk.total_users_impacted
        ),
        'department_performance', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'department', department,
                    'ticket_count', ticket_count,
                    'avg_resolution_hours', avg_resolution_hours,
                    'avg_satisfaction', avg_satisfaction,
                    'high_priority_tickets', high_priority_count
                )
            )
            FROM department_metrics
        ),
        'customer_satisfaction_by_tier', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'subscription_tier', subscription_tier,
                    'ticket_count', ticket_count,
                    'avg_satisfaction', avg_satisfaction,
                    'avg_resolution_hours', avg_resolution_hours
                )
            )
            FROM customer_satisfaction
        )
    ) as dashboard_data
FROM support_kpis sk;

-- ============================================================================
-- SECTION 10: REAL-WORLD SCENARIOS
-- ============================================================================

-- Scenario 1: New ticket triage
WITH new_ticket AS (
    SELECT 
        'TK-2024-NEW' as ticket_number,
        'Users report that the mobile app freezes when trying to upload photos from their camera' as description,
        4 as customer_id,  -- Local Business Inc
        'Technical' as department,
        'Mobile' as category,
        'medium' as priority
)
SELECT 
    'Scenario 1: New Ticket Triage' as scenario,
    'Similar Historical Tickets' as result_type,
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.metadata->>'resolution_steps' as previous_solutions,
    st.satisfaction_score,
    ROUND((st.embedding <=> generate_sample_embedding(nt.description))::NUMERIC, 4) as similarity
FROM support_tickets st, new_ticket nt
WHERE st.category = nt.category
  AND st.status IN ('resolved', 'closed')
  AND st.embedding <=> generate_sample_embedding(nt.description) < 0.6
ORDER BY st.embedding <=> generate_sample_embedding(nt.description)
LIMIT 5;

-- Scenario 2: Escalation analysis
SELECT 
    'Scenario 2: Escalation Analysis' as scenario,
    'High Priority Open Tickets Requiring Attention' as result_type,
    st.ticket_number,
    st.issue_description,
    st.priority,
    st.customer_id,
    c.customer_name,
    c.subscription_tier,
    EXTRACT(DAYS FROM NOW() - st.created_at) as days_open,
    (st.metadata->>'affected_users')::INTEGER as affected_users,
    st.metadata->>'assignee' as current_assignee,
    CASE 
        WHEN EXTRACT(DAYS FROM NOW() - st.created_at) > 7 THEN 'Overdue'
        WHEN EXTRACT(DAYS FROM NOW() - st.created_at) > 3 THEN 'At Risk'
        ELSE 'On Track'
    END as escalation_status
FROM support_tickets st
JOIN customers c ON st.customer_id = c.id
WHERE st.status IN ('open', 'in_progress')
  AND st.priority IN ('high', 'critical')
ORDER BY 
    CASE st.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 END,
    st.created_at ASC;

-- ============================================================================
-- WORKSHOP COMPLETE!
-- ============================================================================

-- Summary of achievements
SELECT 
    'Final Lab Workshop Complete!' as achievement,
    jsonb_build_object(
        'skills_demonstrated', jsonb_build_array(
            'Vector embedding generation and storage',
            'Hybrid search combining similarity and business logic',
            'JSONB metadata analysis and extraction',
            'Performance optimization with appropriate indexing',
            'Reusable function development',
            'Business intelligence dashboard creation',
            'Real-world scenario handling'
        ),
        'tables_created', jsonb_build_array(
            'support_tickets', 'customers', 'knowledge_base'
        ),
        'functions_created', jsonb_build_array(
            'generate_sample_embedding()', 'search_support_system()'
        ),
        'queries_mastered', jsonb_build_array(
            'Vector similarity search',
            'Customer-specific hybrid queries',
            'Tag and metadata analysis',
            'Performance metrics extraction',
            'Business intelligence reporting'
        )
    ) as summary;

-- Next steps recommendation
SELECT 
    'Congratulations!' as message,
    'You have successfully built a complete AI-powered support system using PostgreSQL and pgvector.' as achievement,
    'You are now ready to build production-scale AI applications!' as next_step; 
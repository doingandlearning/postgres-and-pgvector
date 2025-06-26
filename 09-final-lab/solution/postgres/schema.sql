CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    issue_description TEXT NOT NULL,
    status TEXT CHECK (status IN ('open', 'resolved', 'in_progress')) NOT NULL,
    priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding vector(1024),  -- Store semantic meaning of the issue
    metadata JSONB  -- Stores flexible attributes (e.g., tags, resolution notes)
);

-- Indexes for performance optimization
CREATE INDEX idx_support_tickets_embedding ON support_tickets USING ivfflat (embedding);
CREATE INDEX idx_support_tickets_metadata ON support_tickets USING GIN (metadata);
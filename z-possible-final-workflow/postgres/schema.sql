CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE
  docs (
    id UUID PRIMARY KEY,
    pdf_id TEXT,
    page INTEGER,
    text TEXT,
    embedding VECTOR(1024),
    metadata JSONB,
    start INTEGER,
    end INTEGER
  ); 


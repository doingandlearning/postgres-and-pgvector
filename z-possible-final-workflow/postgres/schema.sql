CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS
  docs (
    id UUID PRIMARY KEY,
    pdf_id TEXT,
    page INTEGER,
    text TEXT,
    embedding VECTOR(1024)
  ); 


CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    doc_id TEXT,               -- Reference to the full document
    chunk_id INT,              -- Chunk index
    content TEXT,              -- Chunk text
    embedding vector(1024)     -- Vector representation
);
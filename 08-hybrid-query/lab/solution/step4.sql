CREATE INDEX idx_metadata_jsonb ON items USING GIN (metadata);

CREATE INDEX items_embedding_ivfflat
ON items USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
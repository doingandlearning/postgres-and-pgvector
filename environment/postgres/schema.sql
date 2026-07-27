CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE items (
	id SERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	item_data JSONB,
	embedding vector(1024)
);

-- Used by 04-chunking-pdfs (02-store-chunks.py, 03-batch-embed.py,
-- 04/05-complex-pdf-chunker*.py, 06-semantic-chunker.py) to store PDF chunks.
CREATE TABLE docs (
	id UUID PRIMARY KEY,
	pdf_id TEXT,
	page INTEGER,
	text TEXT,
	embedding VECTOR(1024),
	metadata JSONB,
	start INTEGER,
	"end" INTEGER
);
ALTER TABLE items ADD COLUMN subject TEXT;
ALTER TABLE items ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE items ADD COLUMN metadata JSONB;
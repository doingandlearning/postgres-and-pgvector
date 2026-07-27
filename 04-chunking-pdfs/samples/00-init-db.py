import psycopg
from utils import get_db_connection

# This mirrors postgres/schema.sql, but as a script so it can be re-run
# safely (IF NOT EXISTS) against the shared `environment/` database without
# needing a fresh container. Run this once before 01-06 in this module.

CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_DOCS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS docs (
    id UUID PRIMARY KEY,
    pdf_id TEXT,
    page INTEGER,
    text TEXT,
    embedding VECTOR(1024),
    metadata JSONB,
    start INTEGER,
    "end" INTEGER
);
"""

print("Connecting to the database...")
try:
    conn = get_db_connection()
except psycopg.OperationalError as e:
    print(f"Could not connect to the database: {e}")
    exit()

with conn, conn.cursor() as cur:
    cur.execute(CREATE_EXTENSION_SQL)
    print("Ensured the 'vector' extension is enabled.")

    cur.execute(CREATE_DOCS_TABLE_SQL)
    print("Ensured the 'docs' table exists.")

print("Done. You can now run 01-simple-chunker.py through 06-semantic-chunker.py.")

import uuid
import psycopg
import PyPDF2
from utils import get_db_connection, get_embedding
import os

def chunks_from_pdf(path, tokens=300, overlap=50):
    """
    Extracts text from a PDF, chunks it while preserving context across
    page breaks, and yields chunks with their starting page number.
    """
    # TODO: Implement the PDF text extraction and chunking logic.
    # - Read the PDF from `path`.
    # - For each page, extract the text.
    # - Split the text into words.
    # - Yield tuples of (page_number, chunk) for each chunk.
    pass # Replace this

# --- Main execution ---
pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data/alice.pdf")
pdf_id = "alice_in_wonderland"

try:
    conn = get_db_connection()
except psycopg.OperationalError as e:
    print(f"Could not connect to the database: {e}")
    exit()

with conn, conn.cursor() as cur:
    print(f"Processing and embedding '{pdf_path}'...")
    cur.execute("TRUNCATE TABLE docs")
    
    # TODO: Loop through the (page_num, chunk) tuples from the PDF.
    # For each one:
    # 1. Generate an embedding for the chunk using the `get_embedding()` function.
    # 2. Execute an INSERT statement to store the id, pdf_id, page_num,
    #    text, and embedding in the `docs` table.
    
    print("Committing changes to the database.")

print("Done.") 
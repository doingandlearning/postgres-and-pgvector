import uuid
import psycopg
import PyPDF2
from utils import get_db_connection, get_embedding
import os

def chunks_from_pdf(path, tokens=180, overlap=50):
    """
    Extracts text from a PDF, chunks it while preserving context across
    page breaks, and yields chunks with their starting page number.
    """
    reader = PyPDF2.PdfReader(path)
    words_with_pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            words_with_pages.extend([(word, i + 1) for word in text.split()])

    for start in range(0, len(words_with_pages), tokens - overlap):
        chunk_data = words_with_pages[start : start + tokens]
        if chunk_data:
            chunk_words = [item[0] for item in chunk_data]
            chunk_text = " ".join(chunk_words)
            start_page = chunk_data[0][1]
            yield (start_page, chunk_text)

# --- Main execution ---
pdf_path = os.path.join(os.path.dirname(__file__), "data", "alice.pdf")
pdf_id = "alice_in_wonderland"

print("Connecting to the database...")
try:
    conn = get_db_connection()
except psycopg.OperationalError as e:
    print(f"Could not connect to the database: {e}")
    exit()

with conn, conn.cursor() as cur:
    print(f"Processing and embedding '{pdf_path}'...")
    # Clear out the table before starting
    cur.execute("TRUNCATE TABLE docs")
    print("Existing documents cleared.")

    for page_num, chunk in chunks_from_pdf(pdf_path):
        embedding = get_embedding(chunk)

        if embedding is None:
            print(f"Skipping chunk due to embedding error: '{chunk[:50]}...'")
            continue

        cur.execute(
            "INSERT INTO docs (id, pdf_id, page, text, embedding) VALUES (%s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), pdf_id, page_num, chunk, embedding),
        )
    print("Committing changes to the database.")

print("Done.") 
import PyPDF2
from utils import get_embedding
import os

def chunks_from_pdf(path, tokens=300, overlap=50):
    """
    Extracts text from a PDF, chunks it while preserving context across
    page breaks, and yields chunks with their starting page number.
    """
    print(f"Reading '{path}'...")
    reader = PyPDF2.PdfReader(path)
    
    words_with_pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            # Store each word with its 1-indexed page number
            words_with_pages.extend([(word, i + 1) for word in text.split()])

    # Create chunks from the word list
    for start in range(0, len(words_with_pages), tokens - overlap):
        chunk_data = words_with_pages[start : start + tokens]
        
        if chunk_data:
            chunk_words = [item[0] for item in chunk_data]
            chunk_text = " ".join(chunk_words)
            # Use the page number of the first word in the chunk
            start_page = chunk_data[0][1]
            yield (start_page, chunk_text)

# --- Main execution ---
pdf_path = os.path.join(os.path.dirname(__file__), "data", "alice.pdf")
print("This script demonstrates chunking with page numbers.")
chunk_count = 0
for page_num, chunk in chunks_from_pdf(pdf_path):
    chunk_count += 1
    print(f"--- Chunk {chunk_count} (Page {page_num}, first 50 chars) ---")
    print(f"'{chunk[:50]}...'")
    # To embed this chunk, you would call:
    # embedding = get_embedding(chunk)
    # print(f"Embedding dimensions: {len(embedding)}") 
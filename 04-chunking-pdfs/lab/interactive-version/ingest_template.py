#!/usr/bin/env python3
"""
Template-based PDF ingestion script
Fill in the blanks marked with # TODO: FILL IN
"""

import uuid
import psycopg
import PyPDF2
import requests
import os

# TODO: FILL IN - Database connection details
DB_CONFIG = {
    "host": "localhost",        # TODO: FILL IN - Database host
    "port": "5050",            # TODO: FILL IN - Database port  
    "dbname": "pgvector",      # TODO: FILL IN - Database name
    "user": "postgres",        # TODO: FILL IN - Database user
    "password": "postgres"     # TODO: FILL IN - Database password
}

# TODO: FILL IN - Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/embed"  # TODO: FILL IN - Ollama URL
EMBEDDING_MODEL = "bge-m3"                       # TODO: FILL IN - Model name

# TODO: FILL IN - PDF processing parameters
PDF_PATH = "../data/alice.pdf"    # TODO: FILL IN - Path to your PDF
PDF_ID = "alice_in_wonderland"    # TODO: FILL IN - Unique ID for this PDF
CHUNK_SIZE = 300                  # TODO: FILL IN - Words per chunk
CHUNK_OVERLAP = 50                # TODO: FILL IN - Overlap between chunks

def get_db_connection():
    """Create database connection"""
    return psycopg.connect(**DB_CONFIG)

def get_embedding(text):
    """Generate embedding using Ollama"""
    payload = {"model": EMBEDDING_MODEL, "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data["embeddings"][0]
    else:
        raise Exception(f"Embedding error: {response.text}")

def chunks_from_pdf(path, chunk_size, overlap):
    """
    Extract text from PDF and create chunks
    """
    print(f"Reading PDF: {path}")
    
    with open(path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Extract all text with page tracking
        all_words = []
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            words = text.split()
            
            # Add page number to each word
            for word in words:
                all_words.append((word, page_num))
        
        print(f"Extracted {len(all_words)} words from {len(pdf_reader.pages)} pages")
        
        # Create chunks
        chunks = []
        i = 0
        while i < len(all_words):
            # Take chunk_size words
            chunk_words = all_words[i:i + chunk_size]
            
            if not chunk_words:
                break
            
            # Extract text and determine starting page
            text_parts = [word for word, _ in chunk_words]
            start_page = chunk_words[0][1]  # Page of first word
            
            chunk_text = ' '.join(text_parts)
            chunks.append((start_page, chunk_text))
            
            # Move forward by chunk_size - overlap
            i += max(1, chunk_size - overlap)
        
        print(f"Created {len(chunks)} chunks")
        return chunks

def main():
    print("Starting PDF ingestion...")
    
    # TODO: FILL IN - Check if PDF file exists
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found: {PDF_PATH}")
        return
    
    # Connect to database
    try:
        conn = get_db_connection()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Process PDF
    try:
        chunks = chunks_from_pdf(PDF_PATH, CHUNK_SIZE, CHUNK_OVERLAP)
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        return
    
    # Clear existing data and insert new chunks
    with conn, conn.cursor() as cur:
        # TODO: FILL IN - Delete existing data for this PDF
        cur.execute("DELETE FROM docs WHERE pdf_id = %s", (PDF_ID,))
        print(f"Cleared existing data for {PDF_ID}")
        
        # Process each chunk
        print("Generating embeddings and storing chunks...")
        for i, (page_num, chunk_text) in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)} (page {page_num})...")
            
            try:
                # TODO: FILL IN - Generate embedding for this chunk
                embedding = get_embedding(chunk_text)
                
                # TODO: FILL IN - Insert into database
                cur.execute(
                    """
                    INSERT INTO docs (id, pdf_id, page, text, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (str(uuid.uuid4()), PDF_ID, page_num, chunk_text, embedding)
                )
                
            except Exception as e:
                print(f"❌ Error processing chunk {i}: {e}")
                continue
        
        print("💾 Committing to database...")
    
    conn.close()
    print("✅ Ingestion complete!")
    print(f"📊 Processed {len(chunks)} chunks")

if __name__ == "__main__":
    main() 
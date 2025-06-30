#!/usr/bin/env python3
"""
Pre-built PDF ingestion script that reads configuration from config.json
No Python programming required - just modify the config file!
"""

import json
import uuid
import os
import sys
import psycopg
import PyPDF2
import requests

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json not found!")
        print("Please make sure config.json exists in the same directory as this script.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config.json: {e}")
        sys.exit(1)

def get_db_connection(db_config):
    """Create database connection from config"""
    try:
        return psycopg.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
    except psycopg.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure your Docker containers are running!")
        sys.exit(1)

def get_embedding(text, embedding_config):
    """Generate embedding using Ollama"""
    try:
        payload = {"model": embedding_config['model'], "input": text}
        response = requests.post(embedding_config['ollama_url'], json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data["embeddings"][0]
        else:
            raise Exception(f"Ollama API error: {response.text}")
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        print("Make sure Ollama is running and the model is downloaded!")
        sys.exit(1)

def chunks_from_pdf(path, chunk_size=300, overlap=50):
    """
    Extract text from PDF and create chunks with page information
    """
    print(f"📖 Reading PDF: {path}")
    
    if not os.path.exists(path):
        print(f"❌ Error: PDF file not found: {path}")
        sys.exit(1)
    
    try:
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
            
            print(f"📄 Extracted {len(all_words)} words from {len(pdf_reader.pages)} pages")
            
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
            
            print(f"✂️ Created {len(chunks)} chunks (size: {chunk_size}, overlap: {overlap})")
            return chunks
            
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        sys.exit(1)

def main():
    print("🚀 Starting PDF ingestion with configuration...")
    
    # Load configuration
    config = load_config()
    print(f"📋 Configuration loaded:")
    print(f"   PDF: {config['pdf_path']}")
    print(f"   Chunk size: {config['chunk_size']}")
    print(f"   Overlap: {config['chunk_overlap']}")
    
    # Connect to database
    conn = get_db_connection(config['database'])
    print("✅ Database connected")
    
    # Process PDF
    chunks = chunks_from_pdf(
        config['pdf_path'], 
        config['chunk_size'], 
        config['chunk_overlap']
    )
    
    # Clear existing data for this PDF
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM docs WHERE pdf_id = %s", (config['pdf_id'],))
        print(f"🗑️ Cleared existing data for {config['pdf_id']}")
        
        # Process each chunk
        print("🔄 Generating embeddings and storing chunks...")
        for i, (page_num, chunk_text) in enumerate(chunks, 1):
            print(f"   Processing chunk {i}/{len(chunks)} (page {page_num})...")
            
            # Generate embedding
            embedding = get_embedding(chunk_text, config['embedding'])
            
            # Store in database
            cur.execute(
                """
                INSERT INTO docs (id, pdf_id, page, text, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), config['pdf_id'], page_num, chunk_text, embedding)
            )
        
        print("💾 Committing to database...")
    
    conn.close()
    print("✅ Ingestion complete!")
    print(f"📊 Stored {len(chunks)} chunks in the database")
    print("\nNext steps:")
    print("1. Run: python generate_query_embedding.py \"Your question here\"")
    print("2. Use the embedding in your SQL query to search for similar text")

if __name__ == "__main__":
    main() 
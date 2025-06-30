#!/usr/bin/env python3
"""
Command-line PDF processor for vector search
No Python programming required - just use the CLI commands!

Usage:
  python pdf_processor.py ingest --file path/to/file.pdf --id pdf_identifier
  python pdf_processor.py query --question "Your question here"
"""

import argparse
import json
import uuid
import os
import sys
import psycopg
import PyPDF2
import requests

# Default configuration
DEFAULT_CONFIG = {
    "database": {
        "host": "localhost",
        "port": "5050", 
        "database": "pgvector",
        "user": "postgres",
        "password": "postgres"
    },
    "embedding": {
        "model": "bge-m3",
        "ollama_url": "http://localhost:11434/api/embed"
    },
    "chunk_size": 300,
    "chunk_overlap": 50
}

def load_config():
    """Load configuration from config.json or use defaults"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            # Merge with defaults
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
            return config
    except FileNotFoundError:
        print("ℹ️ No config.json found, using default configuration")
        return DEFAULT_CONFIG

def get_db_connection(db_config):
    """Create database connection"""
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
    """Extract text from PDF and create chunks with page information"""
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

def ingest_pdf(args):
    """Ingest a PDF file into the database"""
    config = load_config()
    
    print(f"🚀 Ingesting PDF: {args.file}")
    print(f"📋 PDF ID: {args.id}")
    print(f"📏 Chunk size: {args.chunk_size or config['chunk_size']}")
    print(f"🔄 Overlap: {args.overlap or config['chunk_overlap']}")
    
    # Connect to database
    conn = get_db_connection(config['database'])
    print("✅ Database connected")
    
    # Process PDF
    chunks = chunks_from_pdf(
        args.file, 
        args.chunk_size or config['chunk_size'], 
        args.overlap or config['chunk_overlap']
    )
    
    # Clear existing data for this PDF
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM docs WHERE pdf_id = %s", (args.id,))
        print(f"🗑️ Cleared existing data for {args.id}")
        
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
                (str(uuid.uuid4()), args.id, page_num, chunk_text, embedding)
            )
        
        print("💾 Committing to database...")
    
    conn.close()
    print("✅ Ingestion complete!")
    print(f"📊 Stored {len(chunks)} chunks in the database")

def query_pdf(args):
    """Query the database for similar text"""
    config = load_config()
    
    print(f"🔍 Searching for: {args.question}")
    
    # Generate embedding for query
    query_embedding = get_embedding(args.question, config['embedding'])
    print("✅ Query embedding generated")
    
    # Connect to database
    conn = get_db_connection(config['database'])
    print("✅ Database connected")
    
    # Execute similarity search
    with conn.cursor() as cur:
        sql = """
        SELECT 
            text,
            page,
            pdf_id,
            embedding <=> %s as similarity
        FROM docs 
        ORDER BY similarity ASC 
        LIMIT %s;
        """
        
        cur.execute(sql, (query_embedding, args.limit))
        results = cur.fetchall()
    
    conn.close()
    
    # Display results
    print(f"\n📊 Search Results for: '{args.question}'")
    print("=" * 60)
    
    if not results:
        print("❌ No results found")
        return
    
    for i, (text, page, pdf_id, similarity) in enumerate(results, 1):
        print(f"\n🔍 Result {i} (Similarity: {similarity:.4f})")
        print(f"📄 Source: {pdf_id}, Page: {page}")
        print(f"📝 Text: {text[:300]}...")  # Show first 300 characters
        print("-" * 40)
    
    # Show best result in full
    best_result = results[0]
    best_text, best_page, best_pdf_id, best_similarity = best_result
    
    print(f"\n🎯 Best Match (Similarity: {best_similarity:.4f}):")
    print(f"📄 Source: {best_pdf_id}, Page: {best_page}")
    print(f"📝 Full Text: {best_text}")

def main():
    parser = argparse.ArgumentParser(
        description="PDF Vector Search Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a PDF
  python pdf_processor.py ingest --file ../data/alice.pdf --id alice_in_wonderland
  
  # Query for similar text
  python pdf_processor.py query --question "What is Alice's sister's name?"
  
  # Ingest with custom chunk settings
  python pdf_processor.py ingest --file report.pdf --id my_report --chunk-size 500 --overlap 100
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a PDF file')
    ingest_parser.add_argument('--file', required=True, help='Path to PDF file')
    ingest_parser.add_argument('--id', required=True, help='Unique identifier for this PDF')
    ingest_parser.add_argument('--chunk-size', type=int, help='Words per chunk (default: 300)')
    ingest_parser.add_argument('--overlap', type=int, help='Overlap between chunks (default: 50)')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Search for similar text')
    query_parser.add_argument('--question', required=True, help='Question to search for')
    query_parser.add_argument('--limit', type=int, default=3, help='Number of results (default: 3)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'ingest':
        ingest_pdf(args)
    elif args.command == 'query':
        query_pdf(args)

if __name__ == "__main__":
    main() 
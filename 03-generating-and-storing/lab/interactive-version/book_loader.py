#!/usr/bin/env python3
"""
Command-line book loader for vector learning
No Python programming required - just use the CLI commands!

Usage:
  python book_loader.py --source open_library --categories "ai,programming" --limit 10
  python book_loader.py --source csv --file books.csv
  python book_loader.py --status
"""

import argparse
import json
import sys
import time
import csv
import psycopg
import requests
from typing import List, Dict, Any

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
    "processing": {
        "batch_size": 5,
        "delay_between_requests": 0.5
    }
}

def load_config():
    """Load configuration from data_config.json or use defaults"""
    try:
        with open('data_config.json', 'r') as f:
            config = json.load(f)
            # Merge with defaults
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
            return config
    except FileNotFoundError:
        print("ℹ️ No data_config.json found, using default configuration")
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

def fetch_books_from_open_library(categories, limit_per_category):
    """Fetch books from Open Library API"""
    print(f"📚 Fetching books from Open Library...")
    print(f"   Categories: {', '.join(categories)}")
    print(f"   Books per category: {limit_per_category}")
    
    all_books = []
    
    for category in categories:
        print(f"   Fetching {category} books...")
        
        try:
            api_category = category.replace(' ', '_').lower()
            url = f"https://openlibrary.org/subjects/{api_category}.json?limit={limit_per_category}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            books = data.get("works", [])
            
            for book in books:
                book_data = {
                    "title": book.get("title", "Untitled"),
                    "authors": [author.get("name", "Unknown") for author in book.get("authors", [])],
                    "first_publish_year": book.get("first_publish_year", "Unknown"),
                    "subject": category,
                    "key": book.get("key", "")
                }
                all_books.append(book_data)
            
            print(f"   ✅ Found {len(books)} books for {category}")
            
        except Exception as e:
            print(f"   ⚠️ Warning: Failed to fetch {category} books: {e}")
            continue
    
    print(f"📖 Total books fetched: {len(all_books)}")
    return all_books

def load_books_from_csv(csv_file):
    """Load books from a CSV file"""
    print(f"📄 Loading books from CSV: {csv_file}")
    
    if not csv_file.endswith('.csv'):
        print("❌ Error: File must be a CSV file")
        sys.exit(1)
    
    try:
        books = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            required_columns = ['title', 'authors', 'subject']
            if not all(col in reader.fieldnames for col in required_columns):
                print(f"❌ Error: CSV must contain columns: {', '.join(required_columns)}")
                print(f"Found columns: {', '.join(reader.fieldnames)}")
                sys.exit(1)
            
            for row in reader:
                # Parse authors (assume comma-separated)
                authors = [author.strip() for author in row['authors'].split(',')]
                
                book_data = {
                    "title": row['title'],
                    "authors": authors,
                    "first_publish_year": row.get('year', 'Unknown'),
                    "subject": row['subject'],
                    "description": row.get('description', ''),
                    "isbn": row.get('isbn', ''),
                    "pages": row.get('pages', '')
                }
                books.append(book_data)
        
        print(f"📖 Loaded {len(books)} books from CSV")
        return books
        
    except FileNotFoundError:
        print(f"❌ Error: CSV file not found: {csv_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        sys.exit(1)

def create_book_description(book):
    """Create a descriptive text for embedding generation"""
    authors_str = ", ".join(book['authors']) if book['authors'] else "Unknown Author"
    year_str = str(book['first_publish_year']) if book['first_publish_year'] != "Unknown" else "Unknown Year"
    
    description = (
        f"Book titled '{book['title']}' by {authors_str}. "
        f"Published in {year_str}. "
        f"This is a book about {book['subject']}."
    )
    
    if book.get('description'):
        description += f" {book['description']}"
    
    return description

def load_books_to_database(books, config):
    """Load books with embeddings into PostgreSQL"""
    print(f"💾 Loading {len(books)} books into database...")
    
    conn = get_db_connection(config['database'])
    processing_config = config['processing']
    
    # Clear existing data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM items")
        print("🗑️ Cleared existing data from items table")
    
    # Process books
    batch_size = processing_config['batch_size']
    delay = processing_config['delay_between_requests']
    
    successful_inserts = 0
    failed_inserts = 0
    
    for i, book in enumerate(books, 1):
        try:
            print(f"📚 Processing {i}/{len(books)}: {book['title'][:50]}...")
            
            # Create description for embedding
            description = create_book_description(book)
            
            # Generate embedding
            embedding = get_embedding(description, config['embedding'])
            
            # Insert into database
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO items (name, item_data, embedding)
                    VALUES (%s, %s, %s)
                    """,
                    (book["title"], json.dumps(book), embedding)
                )
            
            successful_inserts += 1
            
            # Small delay to be respectful
            if delay > 0:
                time.sleep(delay)
            
        except Exception as e:
            failed_inserts += 1
            print(f"   ❌ Failed to process '{book['title'][:50]}...': {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Data loading complete!")
    print(f"   📊 Successfully inserted: {successful_inserts} books")
    if failed_inserts > 0:
        print(f"   ⚠️ Failed to insert: {failed_inserts} books")

def show_database_status(config):
    """Show current database status"""
    print("📊 Database Status")
    print("=" * 30)
    
    try:
        conn = get_db_connection(config['database'])
        
        with conn.cursor() as cur:
            # Check if pgvector extension is installed
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            pgvector_installed = cur.fetchone() is not None
            
            if not pgvector_installed:
                print("❌ pgvector extension not installed!")
                print("   Run this in your database:")
                print("   CREATE EXTENSION IF NOT EXISTS vector;")
                conn.close()
                return
            
            # Check if items table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'items'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                print("❌ 'items' table does not exist!")
                print("   Make sure to run the database schema setup first.")
                conn.close()
                return
            
            # Count total items
            cur.execute("SELECT COUNT(*) FROM items")
            total_count = cur.fetchone()[0]
            print(f"Total books: {total_count}")
            
            if total_count > 0:
                # Count by subject
                cur.execute("""
                    SELECT item_data->>'subject' as subject, COUNT(*) as count
                    FROM items 
                    GROUP BY item_data->>'subject'
                    ORDER BY count DESC
                """)
                subjects = cur.fetchall()
                
                print("\nBooks by subject:")
                for subject, count in subjects:
                    print(f"  - {subject}: {count}")
                
                # Sample recent books
                cur.execute("""
                    SELECT name, item_data->>'subject' as subject
                    FROM items 
                    LIMIT 5
                """)
                samples = cur.fetchall()
                
                print("\nSample books:")
                for name, subject in samples:
                    print(f"  - {name[:50]}... ({subject})")
                
                # Check embedding dimensions (with better error handling)
                try:
                    cur.execute("SELECT embedding FROM items WHERE embedding IS NOT NULL LIMIT 1")
                    result = cur.fetchone()
                    if result and result[0]:
                        # For pgvector, we can get dimensions differently
                        cur.execute("SELECT vector_dims(embedding) FROM items WHERE embedding IS NOT NULL LIMIT 1")
                        dimensions = cur.fetchone()[0]
                        print(f"\nEmbedding dimensions: {dimensions}")
                    else:
                        print("\n⚠️ No embeddings found in database")
                except Exception as e:
                    # Fallback method
                    try:
                        cur.execute("SELECT LENGTH(embedding::text) FROM items WHERE embedding IS NOT NULL LIMIT 1")
                        result = cur.fetchone()
                        if result:
                            print(f"\nEmbedding data exists (length check passed)")
                        else:
                            print("\n⚠️ No embeddings found in database")
                    except Exception as e2:
                        print(f"\n⚠️ Could not check embedding dimensions: {e2}")
            else:
                print("\n📝 Database is empty. Load some books first!")
                print("   Example: python book_loader.py --source open_library --categories 'ai,programming' --limit 5")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database status: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure Docker containers are running:")
        print("      docker-compose up -d")
        print("   2. Check if you can connect to the database:")
        print("      docker exec -it pgvector-db psql -U postgres -d pgvector")
        print("   3. Ensure pgvector extension is installed:")
        print("      CREATE EXTENSION IF NOT EXISTS vector;")

def main():
    parser = argparse.ArgumentParser(
        description="Book Data Loader for Vector Learning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load from Open Library
  python book_loader.py --source open_library --categories "ai,programming" --limit 10
  
  # Load from CSV file
  python book_loader.py --source csv --file my_books.csv
  
  # Check database status
  python book_loader.py --status
  
  # Load with custom categories
  python book_loader.py --source open_library --categories "machine_learning,web_development,databases" --limit 5
        """
    )
    
    parser.add_argument('--source', choices=['open_library', 'csv'], 
                       help='Data source to load from')
    parser.add_argument('--categories', 
                       help='Comma-separated list of categories (for open_library)')
    parser.add_argument('--limit', type=int, default=10,
                       help='Books per category (for open_library, default: 10)')
    parser.add_argument('--file', 
                       help='CSV file path (for csv source)')
    parser.add_argument('--status', action='store_true',
                       help='Show current database status')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    if args.status:
        show_database_status(config)
        return
    
    if not args.source:
        print("❌ Error: Must specify --source or --status")
        parser.print_help()
        return
    
    # Load books based on source
    if args.source == 'open_library':
        if not args.categories:
            print("❌ Error: --categories required for open_library source")
            return
        
        categories = [cat.strip() for cat in args.categories.split(',')]
        books = fetch_books_from_open_library(categories, args.limit)
        
    elif args.source == 'csv':
        if not args.file:
            print("❌ Error: --file required for csv source")
            return
        
        books = load_books_from_csv(args.file)
    
    if not books:
        print("❌ No books were loaded. Please check your parameters.")
        return
    
    # Load books into database
    load_books_to_database(books, config)
    
    print(f"\n🎯 Next steps:")
    print(f"   1. Check status: python book_loader.py --status")
    print(f"   2. Connect to DB: docker exec -it pgvector-db psql -U postgres -d pgvector")
    print(f"   3. Run queries: SELECT name, item_data->>'subject' FROM items LIMIT 5;")

if __name__ == "__main__":
    main() 
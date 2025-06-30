#!/usr/bin/env python3
"""
Configuration-based book data loader
No Python programming required - just modify data_config.json!
"""

import json
import sys
import time
import psycopg
import requests
from typing import List, Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from data_config.json"""
    try:
        with open('data_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: data_config.json not found!")
        print("Please make sure data_config.json exists in the same directory as this script.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in data_config.json: {e}")
        sys.exit(1)

def get_db_connection(db_config: Dict[str, str]) -> psycopg.Connection:
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

def get_embedding(text: str, embedding_config: Dict[str, str]) -> List[float]:
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

def fetch_books_from_open_library(categories: List[str], books_per_category: int) -> List[Dict[str, Any]]:
    """Fetch books from Open Library API"""
    print(f"📚 Fetching books from Open Library...")
    print(f"   Categories: {', '.join(categories)}")
    print(f"   Books per category: {books_per_category}")
    
    all_books = []
    
    for category in categories:
        print(f"   Fetching {category} books...")
        
        try:
            # Convert category name for API (replace spaces with underscores)
            api_category = category.replace(' ', '_').lower()
            url = f"https://openlibrary.org/subjects/{api_category}.json?limit={books_per_category}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            books = data.get("works", [])
            
            for book in books:
                # Extract and clean book data
                book_data = {
                    "title": book.get("title", "Untitled"),
                    "authors": [author.get("name", "Unknown") for author in book.get("authors", [])],
                    "first_publish_year": book.get("first_publish_year", "Unknown"),
                    "subject": category,
                    "key": book.get("key", ""),
                    "subject_places": book.get("subject_places", []),
                    "subject_people": book.get("subject_people", []),
                    "subject_times": book.get("subject_times", [])
                }
                
                all_books.append(book_data)
            
            print(f"   ✅ Found {len(books)} books for {category}")
            
        except requests.RequestException as e:
            print(f"   ⚠️ Warning: Failed to fetch {category} books: {e}")
            continue
        except Exception as e:
            print(f"   ⚠️ Warning: Error processing {category} books: {e}")
            continue
    
    print(f"📖 Total books fetched: {len(all_books)}")
    return all_books

def create_book_description(book: Dict[str, Any]) -> str:
    """Create a descriptive text for embedding generation"""
    authors_str = ", ".join(book['authors']) if book['authors'] else "Unknown Author"
    year_str = str(book['first_publish_year']) if book['first_publish_year'] != "Unknown" else "Unknown Year"
    
    description = (
        f"Book titled '{book['title']}' by {authors_str}. "
        f"Published in {year_str}. "
        f"This is a book about {book['subject']}."
    )
    
    # Add additional context if available
    if book.get('subject_places'):
        description += f" Related to places: {', '.join(book['subject_places'][:3])}."
    
    if book.get('subject_people'):
        description += f" Related to people: {', '.join(book['subject_people'][:3])}."
    
    return description

def load_books_to_database(books: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
    """Load books with embeddings into PostgreSQL"""
    print(f"💾 Loading {len(books)} books into database...")
    
    conn = get_db_connection(config['database'])
    processing_config = config['processing']
    
    # Clear existing data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM items")
        print("🗑️ Cleared existing data from items table")
    
    # Process books in batches
    batch_size = processing_config['batch_size']
    delay = processing_config['delay_between_requests']
    
    successful_inserts = 0
    failed_inserts = 0
    
    for i in range(0, len(books), batch_size):
        batch = books[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(books) + batch_size - 1) // batch_size
        
        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} books)...")
        
        with conn.cursor() as cur:
            for j, book in enumerate(batch, 1):
                try:
                    print(f"   📚 Processing: {book['title'][:50]}...")
                    
                    # Create description for embedding
                    description = create_book_description(book)
                    
                    # Generate embedding
                    embedding = get_embedding(description, config['embedding'])
                    
                    # Insert into database
                    cur.execute(
                        """
                        INSERT INTO items (name, item_data, embedding)
                        VALUES (%s, %s, %s)
                        """,
                        (book["title"], json.dumps(book), embedding)
                    )
                    
                    successful_inserts += 1
                    print(f"   ✅ Inserted: {book['title'][:50]}...")
                    
                    # Small delay to be respectful to the embedding service
                    if delay > 0:
                        time.sleep(delay)
                    
                except Exception as e:
                    failed_inserts += 1
                    print(f"   ❌ Failed to process '{book['title'][:50]}...': {e}")
                    continue
        
        # Commit batch
        conn.commit()
        print(f"   💾 Batch {batch_num} committed to database")
    
    conn.close()
    
    print(f"\n✅ Data loading complete!")
    print(f"   📊 Successfully inserted: {successful_inserts} books")
    if failed_inserts > 0:
        print(f"   ⚠️ Failed to insert: {failed_inserts} books")
    
    print(f"\n🎯 Next steps:")
    print(f"   1. Connect to your database: docker exec -it pgvector-db psql -U postgres -d pgvector")
    print(f"   2. Check your data: SELECT COUNT(*) FROM items;")
    print(f"   3. Explore subjects: SELECT DISTINCT item_data->>'subject' FROM items;")

def main():
    print("🚀 Starting configuration-based book data loading...")
    
    # Load configuration
    config = load_config()
    print("📋 Configuration loaded successfully")
    
    # Validate configuration
    required_keys = ['data_source', 'categories', 'books_per_category', 'database', 'embedding']
    for key in required_keys:
        if key not in config:
            print(f"❌ Error: Missing required configuration key: {key}")
            sys.exit(1)
    
    # Fetch books based on configuration
    if config['data_source'] == 'open_library':
        books = fetch_books_from_open_library(
            config['categories'], 
            config['books_per_category']
        )
    else:
        print(f"❌ Error: Unsupported data source: {config['data_source']}")
        print("Currently supported: 'open_library'")
        sys.exit(1)
    
    if not books:
        print("❌ No books were fetched. Please check your configuration and network connection.")
        sys.exit(1)
    
    # Load books into database
    load_books_to_database(books, config)

if __name__ == "__main__":
    main() 
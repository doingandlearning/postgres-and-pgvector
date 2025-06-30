#!/usr/bin/env python3
"""
Load pre-generated sample data for SQL-focused learning
No API calls required - focuses on database and vector concepts
"""

import json
import psycopg
import sys
from typing import List, Dict, Any

# Pre-generated sample book data with realistic information
SAMPLE_BOOKS = [
    {
        "title": "Python Programming for Beginners",
        "authors": ["John Smith"],
        "first_publish_year": 2020,
        "subject": "programming",
        "description": "A comprehensive guide to learning Python programming from scratch.",
        "isbn": "978-1234567890",
        "pages": 350
    },
    {
        "title": "Machine Learning Fundamentals",
        "authors": ["Sarah Johnson", "Mike Davis"],
        "first_publish_year": 2021,
        "subject": "ai",
        "description": "Introduction to machine learning concepts and algorithms.",
        "isbn": "978-2345678901",
        "pages": 420
    },
    {
        "title": "Web Development with JavaScript",
        "authors": ["Alice Brown"],
        "first_publish_year": 2019,
        "subject": "web_development",
        "description": "Modern web development techniques using JavaScript and frameworks.",
        "isbn": "978-3456789012",
        "pages": 280
    },
    {
        "title": "Deep Learning Neural Networks",
        "authors": ["Robert Chen"],
        "first_publish_year": 2022,
        "subject": "ai",
        "description": "Advanced deep learning techniques and neural network architectures.",
        "isbn": "978-4567890123",
        "pages": 520
    },
    {
        "title": "Advanced Python Techniques",
        "authors": ["Emily Wilson"],
        "first_publish_year": 2021,
        "subject": "programming",
        "description": "Advanced Python programming patterns and best practices.",
        "isbn": "978-5678901234",
        "pages": 390
    },
    {
        "title": "React and Modern Frontend",
        "authors": ["David Lee", "Jennifer Taylor"],
        "first_publish_year": 2022,
        "subject": "web_development",
        "description": "Building modern web applications with React and contemporary tools.",
        "isbn": "978-6789012345",
        "pages": 310
    },
    {
        "title": "Computer Vision Applications",
        "authors": ["Maria Garcia"],
        "first_publish_year": 2020,
        "subject": "ai",
        "description": "Practical computer vision applications and image processing techniques.",
        "isbn": "978-7890123456",
        "pages": 450
    },
    {
        "title": "Database Design Principles",
        "authors": ["Thomas Anderson"],
        "first_publish_year": 2019,
        "subject": "programming",
        "description": "Fundamental principles of database design and optimization.",
        "isbn": "978-8901234567",
        "pages": 320
    },
    {
        "title": "CSS Grid and Flexbox",
        "authors": ["Lisa Park"],
        "first_publish_year": 2021,
        "subject": "web_development",
        "description": "Modern CSS layout techniques with Grid and Flexbox.",
        "isbn": "978-9012345678",
        "pages": 250
    },
    {
        "title": "Natural Language Processing",
        "authors": ["Kevin Zhang", "Anna Rodriguez"],
        "first_publish_year": 2022,
        "subject": "ai",
        "description": "NLP techniques for text analysis and language understanding.",
        "isbn": "978-0123456789",
        "pages": 480
    }
]

# Pre-calculated embeddings (simplified for demonstration)
# In a real scenario, these would be actual embedding vectors
SAMPLE_EMBEDDINGS = {
    "programming": [0.1, 0.8, 0.2, 0.9, 0.3, 0.7, 0.4, 0.6, 0.5, 0.8] + [0.0] * 1014,  # 1024 dimensions
    "ai": [0.9, 0.2, 0.8, 0.1, 0.7, 0.3, 0.6, 0.4, 0.8, 0.2] + [0.0] * 1014,
    "web_development": [0.5, 0.5, 0.6, 0.4, 0.7, 0.3, 0.8, 0.2, 0.9, 0.1] + [0.0] * 1014
}

def get_db_connection() -> psycopg.Connection:
    """Create database connection with default settings"""
    try:
        return psycopg.connect(
            host="localhost",
            port="5050",
            dbname="pgvector",
            user="postgres",
            password="postgres"
        )
    except psycopg.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure your Docker containers are running!")
        sys.exit(1)

def create_book_description(book: Dict[str, Any]) -> str:
    """Create a descriptive text for the book"""
    authors_str = ", ".join(book['authors'])
    
    description = (
        f"Book titled '{book['title']}' by {authors_str}. "
        f"Published in {book['first_publish_year']}. "
        f"{book['description']} "
        f"This {book['pages']}-page book covers {book['subject']} topics."
    )
    
    return description

def generate_realistic_embedding(book: Dict[str, Any]) -> List[float]:
    """Generate a realistic-looking embedding based on book subject"""
    import random
    
    # Use base embedding for the subject
    base_embedding = SAMPLE_EMBEDDINGS.get(book['subject'], SAMPLE_EMBEDDINGS['programming'])
    
    # Add some variation based on book characteristics
    embedding = []
    random.seed(hash(book['title']))  # Consistent randomization per book
    
    for i, base_val in enumerate(base_embedding):
        # Add small random variation
        variation = random.uniform(-0.1, 0.1)
        new_val = max(-1.0, min(1.0, base_val + variation))  # Clamp to [-1, 1]
        embedding.append(new_val)
    
    return embedding

def load_sample_data():
    """Load sample book data into the database"""
    print("🚀 Loading pre-generated sample data...")
    print(f"📊 Loading {len(SAMPLE_BOOKS)} sample books")
    
    conn = get_db_connection()
    print("✅ Database connected")
    
    # Clear existing data
    with conn.cursor() as cur:
        cur.execute("DELETE FROM items")
        print("🗑️ Cleared existing data from items table")
    
    # Insert sample books
    successful_inserts = 0
    
    with conn.cursor() as cur:
        for book in SAMPLE_BOOKS:
            try:
                print(f"📚 Loading: {book['title']}")
                
                # Generate embedding
                embedding = generate_realistic_embedding(book)
                
                # Insert into database
                cur.execute(
                    """
                    INSERT INTO items (name, item_data, embedding)
                    VALUES (%s, %s, %s)
                    """,
                    (book["title"], json.dumps(book), embedding)
                )
                
                successful_inserts += 1
                
            except Exception as e:
                print(f"❌ Failed to load '{book['title']}': {e}")
                continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Sample data loading complete!")
    print(f"📊 Successfully loaded: {successful_inserts} books")
    
    print(f"\n🎯 Now you can explore the data with SQL:")
    print(f"   1. Connect: docker exec -it pgvector-db psql -U postgres -d pgvector")
    print(f"   2. Count records: SELECT COUNT(*) FROM items;")
    print(f"   3. View subjects: SELECT DISTINCT item_data->>'subject' FROM items;")
    print(f"   4. Sample data: SELECT name, item_data->>'subject' FROM items LIMIT 5;")
    
    print(f"\n📚 Subjects included:")
    subjects = set(book['subject'] for book in SAMPLE_BOOKS)
    for subject in sorted(subjects):
        count = sum(1 for book in SAMPLE_BOOKS if book['subject'] == subject)
        print(f"   - {subject}: {count} books")

def show_sample_queries():
    """Display sample SQL queries for exploration"""
    print("\n📝 Sample SQL queries to try:")
    print("=" * 50)
    
    print("\n-- 1. Count books by subject")
    print("SELECT item_data->>'subject' as subject, COUNT(*) as book_count")
    print("FROM items")
    print("GROUP BY item_data->>'subject'")
    print("ORDER BY book_count DESC;")
    
    print("\n-- 2. Find books published after 2020")
    print("SELECT name, item_data->>'first_publish_year' as year")
    print("FROM items")
    print("WHERE (item_data->>'first_publish_year')::int > 2020")
    print("ORDER BY year DESC;")
    
    print("\n-- 3. Check embedding dimensions")
    print("SELECT name, array_length(embedding, 1) as dimensions")
    print("FROM items")
    print("LIMIT 3;")
    
    print("\n-- 4. Find programming books")
    print("SELECT name, item_data->>'authors' as authors")
    print("FROM items")
    print("WHERE item_data->>'subject' = 'programming';")
    
    print("\n-- 5. Sample similarity search (basic)")
    print("SELECT name, embedding <=> (")
    print("    SELECT embedding FROM items WHERE name LIKE '%Python%' LIMIT 1")
    print(") as similarity")
    print("FROM items")
    print("ORDER BY similarity")
    print("LIMIT 5;")

def main():
    print("📚 Sample Data Loader for Vector Learning")
    print("=" * 40)
    
    # Load the sample data
    load_sample_data()
    
    # Show sample queries
    show_sample_queries()
    
    print(f"\n🎓 Learning Focus:")
    print(f"   - Understand how embeddings are stored in PostgreSQL")
    print(f"   - Practice querying vector data with SQL")
    print(f"   - Explore the relationship between text and vectors")
    print(f"   - Learn pgvector operators and functions")

if __name__ == "__main__":
    main() 
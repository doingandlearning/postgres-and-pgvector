import psycopg2
import json
import random
from datetime import datetime, timedelta

# Database connection details
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}

# Possible values for randomization
FORMATS = ["ebook", "paperback", "hardcover"]
PRICE_RANGE = (10, 100)  # Price between $10 and $100
STOCK_RANGE = (5, 500)  # Stock between 5 and 500 units

# Generate a random date within the last 18 months
def random_date():
    days_back = random.randint(0, 18 * 30)  # Approximate days in 18 months
    return (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d %H:%M:%S")

def update_books():
    """Retrieve books, generate new metadata, and upsert into the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Fetch all books from the items table
    cursor.execute("SELECT id, item_data FROM items;")
    books = cursor.fetchall()

    for book_id, item_data in books:
        item_data = json.loads(item_data) if isinstance(item_data, str) else item_data
        subject = item_data.get("subject", "Unknown")  # Extract subject

        # Generate random metadata values
        metadata = {
            "price": round(random.uniform(*PRICE_RANGE), 2),
            "stock": random.randint(*STOCK_RANGE),
            "format": random.choice(FORMATS),
            "authors": item_data.get("authors", []),  # Retain existing author data if available
        }

        created_at = random_date()  # Generate random created_at

        # Update the record in the database
        sql = """
        UPDATE items
        SET created_at = %s, subject = %s, metadata = %s
        WHERE id = %s;
        """
        cursor.execute(sql, (created_at, subject, json.dumps(metadata), book_id))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Successfully updated {len(books)} books with metadata and created_at timestamps.")

# Run the script
if __name__ == "__main__":
    update_books()

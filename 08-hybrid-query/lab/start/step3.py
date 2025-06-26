import psycopg2
import json
from utils_lib import get_embedding_ollama

# Database Configuration
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}

def connect_db():
    """Establish a connection to PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)

def run_query(sql, params=None):
    """Execute a query and return results."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params or ())
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"⚠️ Query failed: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def main():
    print("\n🔹 Welcome to the Query Runner")
    print("This tool allows you to test various SQL queries as you progress.")

    while True:
        print("\n🔹 Choose an Option:")
        print("1 - Find similar books using vector search")
        print("2 - Filter books by price and format")
        print("3 - Run a custom query (for advanced users)")
        print("0 - Exit")

        choice = input("Enter option (0-3): ")

        if choice == "1":
            user_query = input("Enter a book-related query: ")
            query_embedding = get_embedding_ollama(user_query)

            sql = None
            if not sql: 
              return 
            results = run_query(sql, (json.dumps(query_embedding), json.dumps(query_embedding)))
        
        elif choice == "2":
            subject = input("Enter book subject (e.g., AI, Programming): ")
            max_price = float(input("Enter max price: "))
            format_type = input("Enter format (ebook, paperback, hardcover): ")

            sql = None
            if not sql:
              return
            results = run_query(sql, (subject, max_price, format_type))

        elif choice == "3":
            sql = input("\nEnter your SQL query:\n")
            results = run_query(sql)

        elif choice == "0":
            print("✅ Exiting Query Runner.")
            break
        
        else:
            print("❌ Invalid option. Please try again.")
            continue

        # Display results
        if results:
            print("\n🔹 Query Results:")
            for row in results:
                print(row)

if __name__ == "__main__":
    main()

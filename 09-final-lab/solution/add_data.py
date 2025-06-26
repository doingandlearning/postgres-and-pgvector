import psycopg
import csv
import json

# Database connection configuration
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",  # Change if using Docker, e.g., "db"
    "port": "5050"  # Ensure this matches your PostgreSQL setup
}

# Path to CSV file
CSV_FILE = "tickets.csv"

# Function to insert data into PostgreSQL
def insert_tickets_from_csv():
    """Insert support tickets from a CSV file into PostgreSQL."""
    conn = psycopg.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    INSERT INTO support_tickets (issue_description, status, priority, metadata)
    VALUES (%s, %s, %s, %s);
    """

    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        rows = []
        for row in reader:
            # Convert metadata field from string to JSONB format
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}

            rows.append((row["issue_description"], row["status"], row["priority"], json.dumps(metadata)))

        cursor.executemany(sql, rows)  # Bulk insert for efficiency

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Successfully inserted {len(rows)} support tickets from {CSV_FILE}!")

# Run the script
if __name__ == "__main__":
    insert_tickets_from_csv()

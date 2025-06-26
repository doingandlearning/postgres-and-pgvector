### **🛠 Demo: Batch Insertion Techniques for Large Datasets**  

This demo **follows up on the lab** and shows how to optimize inserting multiple records at once using **batch processing techniques** in PostgreSQL.  

✅ **What This Covers**:  
- **Single-row insertions (Baseline)**
- **`executemany()` for bulk inserts**
- **Using `COPY` for high-performance batch inserts**
- **Handling large data efficiently in `pgvector`**

---

## **📌 Step 1: Baseline – Single Row Insertion**  
This method **inserts one record at a time**, which is **inefficient for large datasets**.

```python
import psycopg2
import json

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}

def insert_single_record(book):
    """Insert a single book into the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    INSERT INTO items (name, item_data, embedding)
    VALUES (%s, %s, %s);
    """

    cursor.execute(sql, (book["title"], json.dumps(book), json.dumps(book["embedding"])))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted: {book['title']}")

# Example book entry
book = {
    "title": "Introduction to Algorithms",
    "authors": ["Thomas H. Cormen"],
    "first_publish_year": 2009,
    "subject": "computer_science",
    "embedding": [0.12, -0.04, 0.33, ...]
}

insert_single_record(book)
```

❌ **Why This is Inefficient?**  
- **One transaction per insert** → Slow for large datasets.  
- **High overhead** → Each `INSERT` incurs latency.  
- **Limited scalability** → Not suitable for bulk operations.

---

## **📌 Step 2: Faster Batch Inserts with `executemany()`**
`executemany()` allows **batch insertion**, reducing overhead by grouping queries.

```python
import psycopg2
import json

def batch_insert_books(books):
    """Insert multiple books in a single batch using executemany()."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    INSERT INTO items (name, item_data, embedding)
    VALUES (%s, %s, %s);
    """

    batch_data = [(book["title"], json.dumps(book), json.dumps(book["embedding"])) for book in books]

    cursor.executemany(sql, batch_data)  # Efficient batch execution

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Successfully inserted {len(books)} books in a batch!")

# Example list of books
books = [
    {"title": "Deep Learning", "authors": ["Ian Goodfellow"], "first_publish_year": 2016, "subject": "ai", "embedding": [0.11, -0.02, 0.28, ...]},
    {"title": "Python Crash Course", "authors": ["Eric Matthes"], "first_publish_year": 2015, "subject": "programming", "embedding": [0.21, -0.01, 0.18, ...]},
]

batch_insert_books(books)
```

✅ **Why is `executemany()` better?**  
- **Fewer transactions** → Speeds up insertions.  
- **Reduces latency** → Groups multiple inserts into one call.  
- **Good for medium-sized data (~1000 rows at a time)**.

---

## **📌 Step 3: High-Performance Inserts with `COPY`**
For **very large datasets**, use **PostgreSQL's `COPY`** command, which is **much faster** than `INSERT`.

### **1️⃣ Create a CSV for Bulk Loading**
First, save the books to a CSV file:

```python
import csv

def save_books_to_csv(books, filename="books.csv"):
    """Save book data to a CSV file for bulk loading."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "item_data", "embedding"])  # Header

        for book in books:
            writer.writerow([book["title"], json.dumps(book), json.dumps(book["embedding"])])

    print(f"✅ Books saved to {filename}")

save_books_to_csv(books)
```

---

### **2️⃣ Load the CSV into PostgreSQL using `COPY`**
```python
def bulk_insert_with_copy(csv_file):
    """Use PostgreSQL COPY for high-speed batch insert."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = f"""
    COPY items (name, item_data, embedding)
    FROM '{csv_file}'
    DELIMITER ','
    CSV HEADER;
    """

    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"🚀 Bulk inserted data from {csv_file} using COPY")

bulk_insert_with_copy("books.csv")
```

---

## **📌 Performance Comparison**
| Method               | Speed 🚀 | Best Use Case |
|----------------------|---------|--------------|
| **Single-row INSERT** | ❌ Slow | Small datasets |
| **executemany()**    | ✅ Medium | Medium-sized data (~1000 rows) |
| **COPY (Bulk Load)** | 🚀 Fastest | Large-scale datasets |

✅ **Use `COPY` when dealing with massive datasets (>10,000 rows).**  
✅ **Use `executemany()` for flexible inserts without pre-generating CSVs.**


### **🛠 Lab: Generate & Search with Python and Ollama**  

## **📌 Objective**
By the end of this lab, you will:  
✅ **Generate embeddings dynamically using Ollama**.  
✅ **Insert embeddings into PostgreSQL (`pgvector`)**.  
✅ **Perform a similarity search on vectorized data** using SQL.  
✅ **Retrieve relevant results using Python.**  

---

## **📌 Step 1: Connect to the Database**
Ensure that **PostgreSQL (`pgvector`) is running inside Docker**.

```bash
docker exec -it pgvector-db psql -U postgres -d pgvector
```
This allows you to **manually inspect data** before running Python scripts.

To check existing data:
```sql
SELECT * FROM items LIMIT 5;
```

---

## **📌 Step 2: Generate an Embedding from User Input**
You will now use **Ollama's `bge-m3` model** to generate embeddings dynamically.

### **1️⃣ Install Required Dependencies**
Ensure your Python environment has the necessary libraries:

```bash
pip install requests psycopg2 json
```

### **2️⃣ Define the Embedding Generation Function**
```python
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/embed"

def get_embedding_ollama(text):
    """Generate an embedding using Ollama's bge-m3 model."""
    payload = {"model": "bge-m3", "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data["embeddings"][0]
    else:
        raise Exception(f"Error fetching embedding: {response.text}")

# Example usage
user_query = "Find books related to artificial intelligence"
query_embedding = get_embedding_ollama(user_query)

print(f"Generated embedding: {query_embedding[:5]}...")  # Show a preview
```

✅ **Now, you have an embedding for a user query**.

---

## **📌 Step 3: Query the Database for Similar Results**
Now that we have an **embedding**, we can search for **similar items in `pgvector`**.

### **1️⃣ Define Database Connection**
```python
import psycopg2

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}
```

### **2️⃣ Perform a Vector Similarity Search**
We use **cosine similarity (`<=>`)** to find **the most relevant items**.

```python
def search_similar_items(query_embedding, top_n=5):
    """Find similar items in PostgreSQL using vector search."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, embedding <=> %s AS similarity
    FROM items
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

# Perform search
results = search_similar_items(query_embedding)
print("\n🔹 Top Similar Books:")
for name, similarity in results:
    print(f"{name} (Similarity: {similarity:.4f})")
```

✅ **Now, we retrieve the most relevant books based on their vector embeddings.**

---

## **📌 Step 4: Automating Dynamic Recommendations**
We can **dynamically select a book and use its embedding** for similarity search.

### **1️⃣ Select a Random Book and Retrieve Its Embedding**
```python
def get_random_book_embedding():
    """Retrieve a random book embedding from the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, embedding
    FROM items
    ORDER BY random()
    LIMIT 1;
    """

    cursor.execute(sql)
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if result:
        name, embedding = result
        print(f"\n📖 Using '{name}' for similarity search...")
        return name, json.loads(embedding)
    else:
        return None, None

# Get random book embedding
book_name, book_embedding = get_random_book_embedding()
```

### **2️⃣ Find Similar Books Based on the Random Selection**
```python
if book_embedding:
    similar_books = search_similar_items(book_embedding)
    print("\n🔹 Recommended Books Similar to", book_name)
    for name, similarity in similar_books:
        print(f"{name} (Similarity: {similarity:.4f})")
```

✅ **Now, we can dynamically recommend similar books based on existing database entries.**

---

## **📌 Step 5: Challenge Task – Hybrid Query**
Modify the query to **filter results by genre** before ranking by similarity.

```python
def search_filtered_similar_items(query_embedding, genre, top_n=5):
    """Find similar items but filter by a specific genre."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, embedding <=> %s AS similarity
    FROM items
    WHERE item_data->>'subject' = %s
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), genre, json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

# Example: Find books about 'artificial_intelligence' that are most relevant
if __name__ == "__main__":
  # Example: Find books about 'artificial_intelligence' that are most relevant
  genre = "artificial_intelligence"
  filtered_results = search_filtered_similar_items(get_embedding_ollama(genre), genre)

  print(f"\n🔹 Top AI Books:")
  for name, similarity in filtered_results:
      print(f"{name} (Similarity: {similarity:.4f})")
```

✅ **Combines structured metadata (`JSONB`) + vector search for more precise recommendations.**

---

## **📌 Recap**
| Step | Task |
|------|------|
| **Step 1** | Connect to the database |
| **Step 2** | Generate an embedding using Ollama |
| **Step 3** | Query similar items using vector search |
| **Step 4** | Automate dynamic recommendations |
| **Step 5** | Implement hybrid queries with JSONB filtering |


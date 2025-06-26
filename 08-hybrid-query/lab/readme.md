# 🛠 Lab: Integrating Vector, Relational, and JSONB Data in Queries

This lab will guide you through combining structured relational data, vector embeddings, and JSONB metadata in PostgreSQL queries.

## 📌 Objective

By the end of this lab, you will:
✅ Run hybrid queries combining relational, vector, and JSONB data.
✅ Filter search results using structured and unstructured data.
✅ Optimize query performance with indexing strategies.


## **📌 Step 1: Enhancing the `items` Table**
We will modify the `items` table to store:  
✅ **Relational Data** → `id`, `name`, `subject`, `created_at`  
✅ **Vector Data** → `embedding` (for semantic similarity search)  
✅ **JSONB Metadata** → `metadata` (e.g., price, stock, author details)

### **1️⃣ Modify the Schema**
Run this SQL to update the `items` table:

```sql
ALTER TABLE items ADD COLUMN subject TEXT;
ALTER TABLE items ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE items ADD COLUMN metadata JSONB;
```

✅ **Enhancements:**  
- **`subject`** → Allows **filtering by category** (e.g., "AI", "Programming").  
- **`created_at`** → Helps **prioritize recent books**.  
- **`metadata` (JSONB)** → Stores **price, stock, format (ebook, paperback, hardcover)**.  

---

## **📌 Step 2: Inserting Enhanced Book Data**
Have a look at `step2.py` in both the solution and start folder. See that it's using the current metadata and some randomly generated data to enhance the data we have.

Run it:

```
python step2.py
```

✅ **Now we can search, filter, and rank books by vector, relational, and JSONB attributes.**

---

## **📌 Step 3: Querying with Hybrid Data**
Now, let’s **combine vector search, metadata filtering, and relational conditions**.

### **1️⃣ Retrieve Books Similar to a Query (Vector Search)**
Find **books similar to a user query** based on vector similarity.

```sql
SELECT name, subject, metadata->>'price' AS price
FROM items
ORDER BY embedding <=> '[0.12, -0.04, 0.33, ...]'
LIMIT 5;
```

✅ **Retrieves the 5 most similar books using `pgvector`**.  

---

### **2️⃣ Retrieve Similar Books with a Category Filter**
Find **books similar to a query**, but **only from the "Programming" category**.

```sql
SELECT name, subject, metadata->>'price' AS price
FROM items
WHERE subject = 'Programming'
ORDER BY embedding <=> '[0.12, -0.04, 0.33, ...]'
LIMIT 5;
```

✅ **Restricts results to a relevant category.**

---

### **3️⃣ Retrieve Books Based on Price Range (JSONB Query)**
Find **all books under $40**, ordered by similarity.

```sql
SELECT name, subject, metadata->>'price' AS price
FROM items
WHERE (metadata->>'price')::NUMERIC < 40
ORDER BY embedding <=> '[0.12, -0.04, 0.33, ...]'
LIMIT 5;
```

✅ **Extracts the JSONB `price` field, converts it to a number, and filters results.**

---

### **4️⃣ Retrieve Books by Stock Availability (JSONB Query)**
Find books **in stock** and sort by **availability**.

```sql
SELECT name, subject, metadata->>'stock' AS stock
FROM items
WHERE (metadata->>'stock')::INTEGER > 50
ORDER BY (metadata->>'stock')::INTEGER DESC;
```

✅ **Sorts results by stock quantity in descending order.**

---

### **5️⃣ Retrieve Books with a Specific Format (JSONB Query)**
Find **all books available as ebooks**.

```sql
SELECT name, metadata->>'format' AS format
FROM items
WHERE metadata->>'format' = 'ebook';
```

✅ **Filters books by `format` stored in JSONB.**

---

## **📌 Step 4: Optimizing Queries with Indexes**
Hybrid queries **can slow down** as data grows. Use **indexes** to improve performance.

### **1️⃣ Create an Index for JSONB Queries**
```sql
CREATE INDEX idx_metadata_jsonb ON items USING GIN (metadata);
```

✅ **Speeds up JSONB filtering (e.g., `WHERE metadata->>'format' = 'ebook'`).**

---

### **2️⃣ Create an Index for Vector Similarity**
```sql
CREATE INDEX items_embedding_ivfflat
ON items USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

✅ **Speeds up vector similarity queries (`embedding <=> query_vector`).**

---

## **📌 Step 5: Challenge Task**
Modify the previous queries to **retrieve books by multiple filters**.  

💡 **Example:**
```sql
SELECT name, subject, metadata->>'price' AS price, metadata->>'stock' AS stock
FROM items
WHERE subject = 'AI'
AND (metadata->>'price')::NUMERIC < 50
AND (metadata->>'stock')::INTEGER > 20
ORDER BY embedding <=> '[0.12, -0.04, 0.33, ...]'
LIMIT 5;
```
✅ **Finds AI books under $50 that are in stock, ranked by vector similarity.**

---

## **📌 Recap**
| Step | Task |
|------|------|
| **Step 1** | Enhance the `items` table (relational, vector, JSONB) |
| **Step 2** | Insert books with metadata & embeddings |
| **Step 3** | Query books using hybrid techniques (vector + relational + JSONB) |
| **Step 4** | Optimize performance with indexes |

---
### **Generate and Search**

Connect to DB:
docker exec -it pgvector-db psql -U postgres -d pgvector

#### **1. Select an Existing Embedding as the Query Vector**
You can use an embedding from an existing item in the database as the query vector.

**SQL Example:**
```sql
-- Select an embedding from an existing item
SELECT embedding
FROM items
WHERE name = 'I, Robot';
```

---

#### **2. Use the Selected Embedding for a Similarity Search**
Once you have the embedding, use it to find items most similar to the selected item.

**SQL Example:**
```sql
-- Find items similar to 'The Great Gatsby'
SELECT name, embedding <=> (
    SELECT embedding
    FROM items
    WHERE name = 'I, Robot'
) AS similarity
FROM items
ORDER BY embedding <=> (
    SELECT embedding
    FROM items
    WHERE name = 'I, Robot'
)
LIMIT 5;
```

This query:
- Retrieves the embedding for "The Great Gatsby".
- Searches for other items with similar embeddings.

---

#### **3. Generate Dynamic Recommendations**
Select a random book or a frequently searched one, then use its embedding for similarity-based recommendations.

**SQL Example:**
```sql
-- Randomly select a book and find similar items
WITH random_book AS (
    SELECT embedding
    FROM items
    ORDER BY random()
    LIMIT 1
)
SELECT name, embedding <=> (SELECT embedding FROM random_book) AS similarity
FROM items
ORDER BY embedding <=> (SELECT embedding FROM random_book)
LIMIT 5;
```

---

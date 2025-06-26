### **1️⃣ Create an IVFFLAT Index**
```sql
-- Ensure pgvector is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create an IVFFLAT index on the embeddings column
CREATE INDEX items_embedding_ivfflat
ON items
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);
```

#### **Explanation**
✅ `ivfflat`: Inverted file index for faster approximate nearest neighbor (ANN) search.  
✅ `vector_l2_ops`: Uses L2 (Euclidean distance) for similarity.  
✅ `lists = 100`: Controls the number of clusters (higher = more precise, but slower inserts).  
- **For smaller datasets**, `lists = 50` might be better.  
- **For larger datasets**, `lists = 200+` improves search accuracy.

---

| **Index Type**       | **Distance Operator** | **Similarity Metric**  |
|----------------------|----------------------|------------------------|
| `vector_l2_ops`     | `<->`                | **L2 (Euclidean) distance** |
| `vector_ip_ops`     | `<#>`                | **Inner product (dot product)** |
| `vector_cosine_ops` | `<=>`                | **Cosine similarity** |


---

### **2️⃣ Create an HNSW Index**
```sql
-- Create an HNSW index on the embeddings column
CREATE INDEX items_embedding_hnsw
ON items
USING hnsw (embedding vector_l2_ops)
WITH (m = 16, ef_construction = 200);
```

#### **Explanation**
✅ `hnsw`: Hierarchical Navigable Small World (HNSW) graph index (faster and more accurate than IVFFLAT).  
✅ `vector_l2_ops`: Uses L2 (Euclidean distance).  
✅ `m = 16`: Number of connections per node in the graph (default is **16**).  
✅ `ef_construction = 200`: Controls the accuracy of the index (higher = better recall, but slower build time).  

- **Use HNSW for high-accuracy search with fast lookups.**  
- **Use IVFFLAT for balanced insert/search speed.**  

---

### **3️⃣ Querying with Nearest Neighbors**
Once indexed, you can run **vector similarity queries**:

#### **L2 Distance (Euclidean) Search**
```sql
SELECT name, embedding <-> target_embedding AS similarity
FROM items, 
     (SELECT embedding AS target_embedding FROM items WHERE name = 'I, Robot') AS subquery
ORDER BY similarity
LIMIT 5;

```
- Replace `[EMBEDDING_VECTOR]` with an actual **vector**.
- `<->` is the **L2 (Euclidean distance) operator** (use `<=>` for **cosine similarity**).

---

### **Which Index to Use?**
| **Index Type** | **Pros** | **Cons** |
|--------------|-------------|----------------|
| **IVFFLAT** | ✅ Faster for large-scale searches | ❌ Requires tuning (`lists` parameter) |
| **HNSW** | ✅ More accurate (good recall) | ❌ Higher memory usage, longer index build time |

Use **IVFFLAT for large-scale retrieval** and **HNSW for high-precision, low-latency search**. 🚀






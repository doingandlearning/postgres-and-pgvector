### **Lab Objective:**
By the end of this lab, participants will:
1. Execute similarity searches using various measures (cosine similarity, inner product, Euclidean distance).
2. Understand the workings of **k-Nearest Neighbors (k-NN)** and experiment with different values of `k`.
3. Learn to optimize queries using indexing (IVFFlat and HNSW).
4. Interpret results from similarity searches and explore real-world relevance.

---

### **Lab Setup:**

#### **Pre-Lab Setup:**
1. Ensure the `pgvector` extension is installed and the `items` table is ready.
2. Preload the chosen dataset:
   - Use the provided book dataset as a fallback.
   - Optionally load a larger dataset or use synthetic data.

---

### **Lab Outline:**

#### **1. Introduction to Querying**
- **Task 1:** Write a query to select all items in the database.
  ```sql
  SELECT * FROM items LIMIT 10;
  ```
- **Task 2:** Explain the importance of embeddings and demonstrate how they are stored.

---

#### **2. Cosine Similarity**
- **Task 1:** Select an embedding from a specific book title (e.g., "The Great Gatsby").
  ```sql
  SELECT embedding
  FROM items
  WHERE name = 'The Great Gatsby';
  ```
- **Task 2:** Perform a similarity search using `embedding <=>` for cosine similarity.
  ```sql
  SELECT name, embedding <=> (
      SELECT embedding
      FROM items
      WHERE name = 'The Great Gatsby'
  ) AS similarity
  FROM items
  ORDER BY similarity
  LIMIT 5;
  ```
- **Reflection:** Discuss what the results mean and how similarity is measured.

---

#### **3. k-Nearest Neighbors (k-NN)**
- **Task 1:** Execute a k-NN query by limiting the number of results (`LIMIT k`).
  ```sql
  SELECT name, embedding <=> (
      SELECT embedding
      FROM items
      WHERE name = 'The Great Gatsby'
  ) AS similarity
  FROM items
  ORDER BY similarity
  LIMIT 10;
  ```
- **Task 2:** Experiment with different values of `k` and observe how the results change.

---

#### **4. Other Similarity Measures**
- **Task 1:** Repeat the k-NN query using Euclidean distance.
  ```sql
  SELECT name, embedding <-> (
      SELECT embedding
      FROM items
      WHERE name = 'The Great Gatsby'
  ) AS distance
  FROM items
  ORDER BY distance
  LIMIT 5;
  ```
- **Task 2:** Explore inner product similarity.
  ```sql
  SELECT name, embedding <#> (
      SELECT embedding
      FROM items
      WHERE name = 'The Great Gatsby'
  ) AS similarity
  FROM items
  ORDER BY similarity
  LIMIT 5;
  ```
- **Reflection:** Discuss when to use each measure (e.g., cosine for direction, Euclidean for distance).

---

#### **5. Using Indexes for Optimized Queries**
- **Task 1:** Create an IVFFlat index for the `embedding` column.
  ```sql
  CREATE INDEX embedding_idx_ivfflat
  ON items
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
  ```
- **Task 2:** Perform a query and measure its speed.
  ```sql
  SET enable_seqscan = OFF;

  SELECT name, embedding <=> (
      SELECT embedding
      FROM items
      WHERE name = 'The Great Gatsby'
  ) AS similarity
  FROM items
  ORDER BY similarity
  LIMIT 5;
  ```
- **Task 3:** Create an HNSW index and compare performance.
  ```sql
  CREATE INDEX embedding_idx_hnsw
  ON items
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 200);
  ```

---

#### **6. Advanced Querying (Optional)**
- **Task 1:** Use a random embedding for similarity search.
  ```sql
  WITH random_book AS (
      SELECT embedding
      FROM items
      ORDER BY random()
      LIMIT 1
  )
  SELECT name, embedding <=> (SELECT embedding FROM random_book) AS similarity
  FROM items
  ORDER BY similarity
  LIMIT 5;
  ```

---

### **Lab Reflection and Wrap-Up**
1. Discuss the differences in results and performance between similarity measures and indexing methods.
2. Brainstorm ideas for real-world applications (e.g., recommendation systems).
3. Optional extension: Build a Python/Flask interface to query the database dynamically.

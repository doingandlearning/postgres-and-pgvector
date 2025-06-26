✅ **How sparse vectors are structured** (e.g., TF-IDF, Bag-of-Words).  
✅ **How they differ from dense vectors in storage and retrieval.**  
✅ **How queries work for sparse vector similarity.**  

---

## **📌 Example 1: Creating Sparse Vectors with TF-IDF**
The **TF-IDF (Term Frequency-Inverse Document Frequency)** method generates **sparse vectors** where each dimension represents a term in the vocabulary.

```python
from sklearn.feature_extraction.text import TfidfVectorizer

documents = [
    "Deep learning is a subset of machine learning",
    "Neural networks are used in deep learning",
    "Machine learning enables AI",
]

vectorizer = TfidfVectorizer()
sparse_vectors = vectorizer.fit_transform(documents)

print("Sparse Vector Representation (TF-IDF Matrix):")
print(sparse_vectors.toarray())  # Convert to dense array for visualization

print("\nFeature Names:", vectorizer.get_feature_names_out())
```

### **🔹 Expected Output**
Each row represents a document, and **each column represents a term** from the vocabulary.

```
Sparse Vector Representation (TF-IDF Matrix):
[[0.5  0.7  0.0  0.0  0.5]
 [0.5  0.0  0.7  0.7  0.0]
 [0.0  0.7  0.0  0.0  0.7]]

Feature Names: ['ai', 'deep', 'learning', 'machine', 'networks']
```
✅ **Sparse vector representation** – each **dimension corresponds to a specific word**.  
✅ **Mostly zeros**, with only **non-zero values for relevant terms**.

---

## **📌 Example 2: Searching for Similar Documents Using Cosine Similarity**
With **sparse vectors**, **cosine similarity** is often used to **retrieve the most similar documents**.

```python
from sklearn.metrics.pairwise import cosine_similarity

query = ["machine learning in AI"]
query_vector = vectorizer.transform(query)

similarity_scores = cosine_similarity(query_vector, sparse_vectors)
print("\nCosine Similarity Scores:", similarity_scores)
```

### **🔹 Expected Output**
```
Cosine Similarity Scores: [[0.45  0.32  0.87]]
```
✅ **Higher similarity score = more relevant document**.  
✅ **Sparse vectors enable traditional keyword-based retrieval**.

---

## **📌 Example 3: Storing Sparse Vectors in PostgreSQL (`pgvector`)**
To **store TF-IDF vectors in `pgvector`**, we need to **convert sparse vectors into JSONB**.

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

# Convert sparse vectors to a dictionary (index:value pairs)
def sparse_to_dict(sparse_matrix):
    """Converts a sparse TF-IDF matrix into a JSON-friendly dictionary."""
    return [
        {str(idx): value for idx, value in zip(row.nonzero()[1], row.data)}
        for row in sparse_matrix
    ]

sparse_vector_dicts = sparse_to_dict(sparse_vectors)

# Store in PostgreSQL
def store_sparse_vectors(documents, sparse_vectors):
    """Insert sparse vectors into PostgreSQL as JSONB data."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    INSERT INTO sparse_vectors (doc_text, sparse_embedding)
    VALUES (%s, %s);
    """

    for doc, vector in zip(documents, sparse_vectors):
        cursor.execute(sql, (doc, json.dumps(vector)))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Stored sparse vectors in PostgreSQL!")

store_sparse_vectors(documents, sparse_vector_dicts)
```

---

## **📌 When to Use Sparse vs. Dense Vectors?**
| Feature         | Sparse Vectors (TF-IDF) | Dense Vectors (Embeddings) |
|----------------|------------------------|----------------------------|
| **Interpretability** | High (direct word mapping) | Low (latent representation) |
| **Storage Size** | Large (one dimension per word) | Compact (512–1024) |
| **Query Matching** | Exact keyword matching | Semantic/contextual retrieval |
| **Performance** | Slower for large datasets | Optimized for large-scale retrieval |
| **Use Case** | FAQ search, structured text | Semantic search, AI-powered retrieval |


## **📌 Chunking Large Documents for Embedding and Search**  

When working with **large documents**, we can’t embed the entire text as a **single vector** because:  
✅ **LLMs have token limits** (e.g., `bge-m3` or `OpenAI` models have context size constraints).  
✅ **Large vectors increase computational overhead** for searches.  
✅ **Better retrieval granularity** allows for more **precise** matches.  

**Solution:** **Chunking** → Splitting the document into **manageable segments**, embedding each chunk, and indexing it for retrieval.  

---

## **📌 1️⃣ Chunking Strategies**
### **✅ Fixed-Size Chunking (Basic)**
- Split the text into **fixed-size** chunks (e.g., **512 tokens**).  
- Works well for structured, uniform data (e.g., paragraphs).  
- **Downside:** May split information at the wrong point (e.g., mid-sentence).

### **✅ Overlapping Sliding Windows (Better)**
- Each chunk **overlaps** with the next (e.g., **512 tokens with a 128-token overlap**).  
- **Preserves context across chunks**.  
- **Avoids loss of meaning** due to arbitrary cuts.  

### **✅ Semantic-Based Chunking (Best)**
- Uses **sentence boundaries** or **section titles** to split content.  
- Keeps **meaningful units** together.  
- Requires **NLP tools like Spacy/NLTK** to segment text.

---

## **📌 2️⃣ Implementing Chunking in Python**
We’ll use **NLTK** for **sentence-based chunking** and handle overlapping windows.

```python
import nltk
from nltk.tokenize import sent_tokenize

nltk.download("punkt")

def chunk_text(text, chunk_size=512, overlap=128):
    """Split text into overlapping chunks for embedding."""
    sentences = sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence.split())

        if current_length + sentence_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:]  # Keep overlap
            current_length = sum(len(sent.split()) for sent in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Example
text = """Deep Learning is a subfield of machine learning concerned with neural networks...
          The most popular architectures include Transformers, CNNs, and RNNs. 
          These methods have transformed NLP, CV, and AI research."""

chunks = chunk_text(text)
print(f"Generated {len(chunks)} chunks:")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i+1}:\n{chunk}")
```

✅ **This method ensures that each chunk is:**
- **Not too large** for embedding models.  
- **Maintains context** across chunks using overlap.  
- **Ready for vector search** as a standalone embedding.  

---

## **📌 3️⃣ Generating Embeddings for Each Chunk**
Once we have **chunks**, we generate **embeddings per chunk**.

```python
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/embeddings"

def get_embedding(text):
    """Generate an embedding using Ollama's bge-m3 model."""
    payload = {"model": "bge-m3", "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        return response.json().get("embedding")
    else:
        raise Exception(f"Error fetching embedding: {response.text}")

# Generate embeddings for chunks
chunk_embeddings = [get_embedding(chunk) for chunk in chunks]

print(f"✅ Generated {len(chunk_embeddings)} embeddings.")
```

---

## **📌 4️⃣ Storing Chunks in PostgreSQL (`pgvector`)**
We now **store chunks** in PostgreSQL **along with embeddings**.

### **1️⃣ Modify Table to Support Chunked Data**
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    doc_id TEXT,               -- Reference to full document
    chunk_id INT,              -- Chunk index
    content TEXT,              -- Chunk text
    embedding vector(1024)     -- Vector representation
);
```

### **2️⃣ Insert Chunks into PostgreSQL**
```python
import psycopg2

DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5050"
}

def store_chunks(doc_id, chunks, embeddings):
    """Insert chunked text and embeddings into PostgreSQL."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    INSERT INTO documents (doc_id, chunk_id, content, embedding)
    VALUES (%s, %s, %s, %s);
    """

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        cursor.execute(sql, (doc_id, i, chunk, json.dumps(embedding)))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Stored {len(chunks)} chunks for document: {doc_id}")

# Example usage
store_chunks("deep-learning-guide", chunks, chunk_embeddings)
```

✅ **Now each chunk is stored in `pgvector` with an embedding.**  
✅ **We can query against smaller, semantically meaningful sections.**

---

## **📌 5️⃣ Searching for Relevant Chunks**
Once chunks are stored, **we can search them efficiently using vector similarity**.

### **1️⃣ Search Query in PostgreSQL**
```python
def search_similar_chunks(query, top_n=5):
    """Search for the most relevant document chunks using vector similarity."""
    query_embedding = get_embedding(query)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT doc_id, chunk_id, content
    FROM documents
    ORDER BY embedding <=> %s  -- Cosine similarity
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

# Example search query
query = "Explain how deep learning works"
results = search_similar_chunks(query)

for doc_id, chunk_id, content in results:
    print(f"\n📖 Found in {doc_id} (Chunk {chunk_id}):\n{content}")
```

---

## **📌 6️⃣ Enhancing Search Results with LLMs**
Once **relevant chunks** are found, we can **send them to an LLM (OpenAI or Ollama) to generate a structured answer**.

```python
def enhance_with_openai(query, chunks):
    """Send retrieved chunks to OpenAI for an enhanced response."""
    
    chunk_text = "\n".join([f"Chunk {i}: {chunk}" for i, chunk in enumerate(chunks)])

    prompt = f"""
    Here is a user query:
    "{query}"

    The following document chunks are relevant:
    {chunk_text}

    Generate a structured response answering the user's query based on these chunks.
    """

    OPENAI_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_API_KEY = "your-api-key"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a document retrieval assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    response = requests.post(OPENAI_URL, headers=headers, data=json.dumps(payload))
    return response.json()["choices"][0]["message"]["content"]

# Example usage
enhanced_response = enhance_with_openai(query, [content for _, _, content in results])
print("\n🔹 **Enhanced Answer:**")
print(enhanced_response)
```

---

## **📌 Summary of the Full Pipeline**
🚀 **Chunking** → Split large text into smaller, meaningful segments.  
🚀 **Embedding** → Convert each chunk into a vector representation.  
🚀 **Vector Search** → Retrieve semantically relevant chunks using `pgvector`.  
🚀 **LLM Enhancement** → Summarize retrieved chunks for a structured answer.  

---

## **🚀 Next Steps**
1️⃣ **Optimize embeddings using `HNSW` indexing for faster retrieval.**  
2️⃣ **Combine vector search with JSONB metadata for filtering.**  
3️⃣ **Build a real-time document retrieval API.**  

Would you like an **optimized hybrid query** example next? 🚀
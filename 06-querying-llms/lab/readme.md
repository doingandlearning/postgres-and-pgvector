### **🛠 Lab: Querying LLMs with Retrieved Data**  
This lab focuses on **retrieving relevant data via vector search** and **enhancing LLM responses with structured context**.

---

## **📌 Objective**
By the end of this lab, you will:  
✅ **Retrieve relevant context using vector similarity search**.  
✅ **Format and structure retrieved data for an LLM**.  
✅ **Query an LLM with optimized parameters**.  
✅ **Compare different LLM responses based on parameter tuning**.  

---

## **📌 Step 1: Retrieve Relevant Data via Vector Search**  
Before querying the LLM, we **retrieve relevant stored information** using **vector similarity search**.

### **1️⃣ Generate an Embedding for the Query**
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

user_query = "What are the best books on artificial intelligence?"
query_embedding = get_embedding_ollama(user_query)
print(f"Generated embedding: {query_embedding[:5]}...")  # Preview
```

✅ **We now have an embedding representation of our query.**  

---

## **📌 Step 2: Perform a Vector Similarity Search**
Using **pgvector**, we retrieve **relevant book recommendations**.

### **1️⃣ Define Database Connection**
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
```

### **2️⃣ Retrieve Relevant Data**
```python
def search_similar_books(query_embedding, top_n=5):
    """Retrieve books with the most similar vector embeddings."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, item_data, embedding <=> %s AS similarity
    FROM items
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

# Retrieve relevant books
books = search_similar_books(query_embedding)
print("\n🔹 Top Recommended Books:")
for name, metadata, similarity in books:
    print(f"{name} (Similarity: {similarity:.4f})")
```

✅ **Now we have a list of books similar to the user's query.**  

---

## **📌 Step 3: Enhance the Query with Structured Context**
Now, we format the retrieved books **to provide structured input to the LLM**.

```python
def format_books_for_prompt(books):
    """Format book data for use in LLM queries."""
    book_text = "\n".join(
        [
            f"- {book[0]} ({book[1].get('subject', 'Unknown Subject')})"
            for book in books
        ]
    )

    prompt = f"""
    The user asked about books related to artificial intelligence.

    Based on vector search, here are relevant books:
    {book_text}

    Provide a structured summary and categorize these books for beginners, intermediate, and advanced learners.
    """

    return prompt

# Generate structured prompt
structured_prompt = format_books_for_prompt(books)
print("\n🔹 Structured Prompt for LLM:")
print(structured_prompt)
```

✅ **We now have a well-structured prompt that provides relevant data to the LLM.**  

---

## **📌 Step 4: Query the LLM with Retrieved Data**
Using **OpenAI's API**, we send the structured context to the LLM. Swap out the URL and key for your internal version of the LLM.

### **1️⃣ Define API Connection**
```python
OPENAI_API_KEY = "your-api-key"  # Replace with your actual key
url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}
```

### **2️⃣ Send Request to LLM**
```python
def query_llm(prompt):
    """Query OpenAI's LLM with retrieved book data."""
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are an AI assistant helping a user find books."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"

# Query LLM
llm_response = query_llm(structured_prompt)
print("\n🔹 LLM Response:")
print(llm_response)
```

✅ **Now, we receive an enriched response from the LLM!**  

---

## **📌 Step 5: Experimenting with LLM Parameters**
Modify **`temperature`**, **`top_p`**, and **`max_tokens`** to see their effect.

### **Example 1: High Creativity (temperature = 0.9)**
```python
payload["temperature"] = 0.9  # More variation in responses
```

### **Example 2: Concise Answer (max_tokens = 100)**
```python
payload["max_tokens"] = 100  # Shorter, to-the-point responses
```

### **Example 3: Structured Response Using JSON**
```python
payload["messages"].append(
    {"role": "system", "content": "Format the response as structured JSON."}
)
```

✅ **Try different values and compare LLM behavior!**

---

## **📌 Challenge Task: Hybrid Query**
Modify the **vector query** to **filter books by subject before ranking by similarity**.

```python
def search_filtered_books(query_embedding, subject, top_n=5):
    """Retrieve books related to a specific subject and order by vector similarity."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT name, item_data, embedding <=> %s AS similarity
    FROM items
    WHERE item_data->>'subject' = %s
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (json.dumps(query_embedding), subject, json.dumps(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

# Example: Find AI books with best recommendations
filtered_books = search_filtered_books(query_embedding, "artificial_intelligence")
print("\n🔹 AI-Specific Book Recommendations:")
for name, metadata, similarity in filtered_books:
    print(f"{name} (Similarity: {similarity:.4f})")
```

✅ **This ensures we retrieve books on the correct subject before querying the LLM.**  

---

## **📌 Recap**
| Step | Task |
|------|------|
| **Step 1** | Generate an embedding for user query |
| **Step 2** | Retrieve similar books using vector search |
| **Step 3** | Format retrieved data for structured LLM input |
| **Step 4** | Query an LLM and analyze response quality |
| **Step 5** | Experiment with different LLM parameters |
🚀
### **Final Lab: AI-Powered Support Ticket Retrieval System**  
*(Applying hybrid queries to retrieve and enhance past customer support tickets using vector search, relational data, and JSONB metadata.)*  

---

## **📌 Lab Overview**  
**Objective:**  
- Build a **customer support assistant** that retrieves similar past tickets and enhances them with an LLM.  
- Use **vector embeddings** to find semantically similar issues.  
- Apply **relational filtering** (e.g., priority, department, ticket status).  
- Query **JSONB metadata** for additional insights (e.g., tags, resolution steps).  

🔹 **Real-World Use Case:**  
> "A support agent enters a user problem. The system retrieves similar past tickets, filters by priority, and generates an LLM-enhanced summary to assist with resolution."  

✅ **Key Techniques Applied:**  
- **Vector search:** Finds support tickets with similar issue descriptions.  
- **Relational filtering:** Limits results by **priority, status, and department**.  
- **JSONB extraction:** Uses structured metadata (e.g., `"tags": ["network", "authentication"]`).  
- **LLM augmentation:** Summarizes retrieved results and suggests resolution steps.  

---

## **🛠 Step 1: Define the Database Schema**  
We create a `support_tickets` table that includes:  
1. **Relational fields** (structured metadata: `id`, `status`, `priority`).  
2. **Vector embeddings** (`pgvector` to store semantic issue representations).  
3. **JSONB metadata** (tags, resolution steps, timestamps).  

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    issue_description TEXT NOT NULL,
    status TEXT CHECK (status IN ('open', 'resolved', 'in_progress')) NOT NULL,
    priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding vector(1024),  -- Store semantic meaning of the issue
    metadata JSONB  -- Stores flexible attributes (e.g., tags, resolution notes)
);

-- Indexes for performance optimization
CREATE INDEX idx_support_tickets_embedding ON support_tickets USING ivfflat (embedding);
CREATE INDEX idx_support_tickets_metadata ON support_tickets USING GIN (metadata);
```

✅ **Why This Works?**  
- `embedding`: Allows **vector similarity search** on issue descriptions.  
- `status`, `priority`: Enables **structured filtering** on ticket metadata.  
- `metadata`: Stores **tags, resolution steps, customer impact, and timestamps** flexibly.  

---

### **🛠 Step 2: Populate the Database Using `tickets.csv`**  

Instead of manually inserting records, we will **load support tickets from a CSV file (`tickets.csv`)** into the `support_tickets` table. The CSV file should include:  

| issue_description | status | priority | metadata |
|------------------|--------|----------|----------|
| "User cannot log in to the system, getting authentication error" | open | high | `{"tags": ["authentication", "login"], "resolution_steps": ["Reset password", "Check logs"]}` |
| "Network connection drops intermittently for remote workers" | resolved | medium | `{"tags": ["network", "VPN"], "resolution_steps": ["Check ISP", "Restart router"]}` |

✅ **Why This Approach Works?**  
- Allows **bulk loading of support tickets** from an external dataset.  
- Ensures **consistent structure** without manual SQL statements.  
- Can be **extended to handle large datasets efficiently**.  

---

### **📌 1️⃣ Ensure `tickets.csv` Format is Correct**
Before importing, confirm the **CSV file is properly formatted**. Example:

```
issue_description,status,priority,metadata
"User cannot log in to the system, getting authentication error",open,high,"{""tags"": [""authentication"", ""login""], ""resolution_steps"": [""Reset password"", ""Check logs""]}"
"Network connection drops intermittently for remote workers",resolved,medium,"{""tags"": [""network"", ""VPN""], ""resolution_steps"": [""Check ISP"", ""Restart router""]}"
```

---

### **📌 2️⃣ Load the CSV File into PostgreSQL Using Python**
We will use `psycopg2` to read the CSV file and insert the data.

#### **Python Script: Load `tickets.csv` into PostgreSQL**
```python
import psycopg2
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
    conn = psycopg2.connect(**DB_CONFIG)
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

```

✅ **What This Script Does:**  
- **Reads `tickets.csv` using Pandas**.  
- **Converts the metadata column into valid JSONB format**.  
- **Inserts each ticket into the `support_tickets` table**.  
- **Commits the transactions** to persist data.  

---

### **📌 3️⃣ Alternative: Load CSV Directly via `COPY` in SQL**
If the **CSV file is stored on the database server**, you can use `COPY` in SQL:

```sql
COPY support_tickets(issue_description, status, priority, metadata)
FROM '/path/to/tickets.csv'
DELIMITER ','
CSV HEADER;
```

✅ **Why Use `COPY`?**  
- **Much faster for large datasets** than `INSERT`.  
- **Requires the CSV file to be accessible by PostgreSQL**.  
- **No need for a Python script** if you can upload files directly to the DB server.  


---
### **🛠 Step 3: Generate Embeddings for Support Tickets**  

Now that we have support tickets stored in PostgreSQL, we need to **generate vector embeddings** for the `issue_description` field. This will allow us to perform **semantic similarity searches** using `pgvector`.  

#### Ensure the model is installed in your Ollama instance

```bash
docker exec -it ollama-service-final-lab /bin/sh
ollama pull bge-m3
```

✅ **What This Step Will Do:**  
- **Retrieve all tickets without embeddings**.  
- **Generate vector embeddings** using **Ollama's `bge-m3` model**.  
- **Update the `support_tickets` table** to store embeddings for future searches.  

---

## **📌 1️⃣ Retrieve Support Tickets Without Embeddings**
Before generating embeddings, check which records **are missing embeddings**.

```sql
SELECT id, issue_description FROM support_tickets WHERE embedding IS NULL;
```
📌 **Why?**  
- Ensures we **only process new tickets** without embeddings.  

---

## **📌 2️⃣ Python Script: Generate & Store Embeddings**
We will use **Ollama (`bge-m3` model)** to convert ticket descriptions into **vector embeddings** and update PostgreSQL.

### **Python Script: Generate Embeddings and Update DB**
```python
import psycopg2
import requests
import json

# Database configuration
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",  # Change if using Docker, e.g., "db"
    "port": "5050"
}

# Ollama API Configuration
OLLAMA_URL = "http://localhost:11434/api/embed"

def get_embedding_ollama(text):
    """Generate an embedding using Ollama's bge-m3 model."""
    payload = {"model": "bge-m3", "input": text}
    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data["embeddings"][0]
    else:
        raise Exception(f"Error fetching embedding: {response.text}")

def generate_embeddings_for_tickets():
    """Fetch tickets without embeddings, generate embeddings, and update the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Fetch tickets missing embeddings
    cursor.execute("SELECT id, issue_description FROM support_tickets WHERE embedding IS NULL;")
    tickets = cursor.fetchall()

    if not tickets:
        print("✅ All tickets already have embeddings.")
        return

    print(f"🎯 Found {len(tickets)} tickets to process.")

    # Generate embeddings and update database
    update_sql = "UPDATE support_tickets SET embedding = %s WHERE id = %s;"

    for ticket_id, issue_description in tickets:
        try:
            embedding = get_embedding_ollama(issue_description)
            cursor.execute(update_sql, (json.dumps(embedding), ticket_id))
            print(f"✅ Updated ticket {ticket_id} with embedding.")
        except Exception as e:
            print(f"❌ Error processing ticket {ticket_id}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("🚀 Embeddings updated successfully!")

# Run the script
if __name__ == "__main__":
    generate_embeddings_for_tickets()
```

---

## **📌 3️⃣ What This Script Does**
✅ **Fetches support tickets without embeddings.**  
✅ **Uses `bge-m3` from Ollama** to generate embeddings.  
✅ **Updates PostgreSQL to store embeddings for future searches.**  
✅ **Handles errors gracefully** (if embedding generation fails).  

---

## **📌 4️⃣ Expected Database Update**
After running the script, checking the database should show the embeddings stored:

```sql
SELECT id, issue_description, embedding FROM support_tickets WHERE embedding IS NOT NULL LIMIT 5;
```

✅ **Example Output (Truncated for Readability)**  
```
+----+--------------------------------------+-------------------------------------------+
| id | issue_description                    | embedding                                |
+----+--------------------------------------+-------------------------------------------+
| 1  | "User cannot log in"                 | [-0.23, 0.11, 0.05, ...]                 |
| 2  | "Network issues for remote workers"  | [0.12, -0.09, 0.31, ...]                 |
| 3  | "Payment processing errors"          | [-0.15, 0.24, -0.01, ...]                |
+----+--------------------------------------+-------------------------------------------+
```

---

## **🛠 Step 4: Querying Support Tickets Using Hybrid Search**  
### **1️⃣ Retrieve Similar Past Tickets Using Vector Search**
Find **past tickets** similar to a new user query.  

```sql
SELECT id, issue_description, metadata->>'resolution_steps' AS resolution_steps
FROM support_tickets
ORDER BY embedding <=> (SELECT embedding FROM support_tickets WHERE issue_description = 'VPN connection is slow')
LIMIT 3;
```
📌 **What This Does:**  
✅ Retrieves **top 3 tickets** closest in meaning to `"VPN connection is slow"`.  
✅ Uses `embedding <=>` operator to perform **vector similarity search**.  
✅ Extracts **resolution steps** from JSONB metadata.  

---

### **2️⃣ Filtering by Status & Priority**
Find **only unresolved high-priority tickets**.

```sql
SELECT id, issue_description, priority, metadata->>'tags' AS tags
FROM support_tickets
WHERE status = 'open' AND priority = 'high';
```
📌 **What This Does:**  
✅ Filters **only unresolved tickets** (`status = 'open'`).  
✅ Retrieves **high-priority issues** to focus on critical cases.  
✅ Extracts **tags** from JSONB metadata.  

---

### **3️⃣ Searching for Specific Issue Tags in JSONB**  
Find all tickets **related to authentication issues**.

```sql
SELECT id, issue_description
FROM support_tickets
WHERE metadata @> '{"tags": ["authentication"]}';
```
📌 **What This Does:**  
✅ Finds tickets where **tags include `"authentication"`**.  
✅ Uses the **JSONB containment (`@>`) operator** for efficient filtering.  

---

## **🛠 Step 5: Enhancing Results with an LLM**  
Now, we use an **LLM (OpenAI or Ollama) to generate a support response** based on the retrieved tickets.

### **1️⃣ Python Function to Retrieve Relevant Tickets**
```python
def find_similar_tickets(user_issue, top_n=3):
    """Retrieve similar past tickets based on vector similarity."""
    query_embedding = get_embedding_ollama(user_issue)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT issue_description, metadata->>'resolution_steps'
    FROM support_tickets
    ORDER BY embedding <=> %s
    LIMIT %s;
    """

    cursor.execute(sql, (Json(query_embedding), top_n))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results if results else "No relevant tickets found."
```

✅ **This function:**  
- **Generates an embedding** for the new issue description.  
- **Queries `pgvector`** for similar past tickets.  
- **Extracts resolution steps** from JSONB.  

---

### **2️⃣ Sending Retrieved Data to OpenAI for Response Generation**
```python
def enhance_with_openai(tickets, user_issue):
    """Send retrieved support tickets to OpenAI to generate a response."""

    ticket_text = "\n".join(
        [f"- {ticket[0]} (Resolution: {ticket[1]})" for ticket in tickets]
    )

    prompt = f"""
    A customer support agent received this issue:
    "{user_issue}"

    Here are similar past tickets:
    {ticket_text}

    Generate a structured response summarizing the best solution steps.
    """

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a support assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    response = requests.post(OPENAI_URL, headers=HEADERS, data=json.dumps(payload))
    return response.json()["choices"][0]["message"]["content"]
```

✅ **What This Does:**  
- **Summarizes retrieved tickets** into a structured LLM response.  
- **Guides the agent** with **AI-suggested resolution steps**.  

---

## **📌 Expected Output Example**
```
🔹 User Issue: "VPN is not connecting for remote users."
🔹 Suggested Solution:
1️⃣ Restart the router and try connecting again.
2️⃣ Check ISP connection for outages.
3️⃣ Ensure VPN client settings match company security policies.
```

---

## **🚀 Final Deliverable: A Working AI-Powered Support Assistant**  
✅ Retrieves similar past tickets using **vector search**.  
✅ Filters results by **status, priority, and tags**.  
✅ Enhances responses with an **LLM-powered solution generator**.  

📌 **Next Steps:**  
1️⃣ **Should we add UI elements to make this interactive?**  
2️⃣ **Would caching LLM results improve performance?**  
3️⃣ **How can we handle multi-step conversations for long-running issues?**  

Let me know where you’d like to refine this! 🚀
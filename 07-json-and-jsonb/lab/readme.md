### **🛠 Lab: Querying and Optimizing JSONB Data in PostgreSQL**  

This lab focuses on **storing, querying, and optimizing JSONB data** inside a PostgreSQL database.  

---

## **📌 Objective**  
By the end of this lab, you will:  
✅ **Understand the difference between JSON and JSONB**.  
✅ **Store JSONB data inside a relational table**.  
✅ **Query and filter JSONB fields using SQL**.  
✅ **Index JSONB fields for faster retrieval**.  

---

PostgreSQL supports **both `JSON` and `JSONB`**, but they behave differently:  

| Feature | JSON | JSONB |
|---------|------|-------|
| **Storage** | Stored as text (unprocessed) | Stored in binary format (optimized) |
| **Query Performance** | Slower (parses every time) | Faster (indexed & optimized) |
| **Indexing** | Not indexable | Indexable with GIN |
| **Use Case** | Logging, rarely queried data | Searchable, structured metadata |

📌 **Rule of Thumb:** **Use `JSONB` if you need indexing & queries.**  

---

## **📌 Step 1: Creating a Table with JSONB Data**  
We'll create a **product catalog** where each product has structured data (name, price) and **flexible attributes** stored in JSONB.

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    metadata JSONB
);
```

✅ **`metadata` stores product details dynamically** (e.g., specifications, reviews).  

You can do this in either a SQL viewer or by storing the query in a file and executing it with Docker like this:

```bash
docker exec -i pgvector-db psql -U postgres -d pgvector < step1.sql 
```

---

## **📌 Step 2: Inserting JSONB Data**  
Let's insert **sample product records** with JSONB metadata.

```sql
INSERT INTO products (name, price, metadata)
VALUES 
    ('Laptop X1', 1299.99, '{"brand": "TechCorp", "ram": "16GB", "storage": "512GB SSD"}'),
    ('Phone Z9', 899.50, '{"brand": "SmartTech", "battery": "4000mAh", "camera": "108MP"}'),
    ('Tablet M5', 499.99, '{"brand": "TabWorld", "screen_size": "10.5 inches", "battery": "6000mAh"}');
```

✅ **No schema change required** if new attributes are added later.  

---

## **📌 Step 3: Querying JSONB Data**  
### **1️⃣ Extracting a Specific JSONB Field**
Retrieve **brand names** from all products:

```sql
SELECT name, metadata->>'brand' AS brand
FROM products;
```

### **2️⃣ Filtering by JSONB Attributes**
Find **all products with at least 5000mAh battery**:

```sql
SELECT name, metadata->>'battery' AS battery
FROM products
WHERE metadata->>'battery' > '5000mAh';
```

📌 **PostgreSQL treats JSONB values as text, so numeric comparison requires casting.**  

```sql
SELECT name, metadata->>'battery' AS battery
FROM products
WHERE (regexp_replace(metadata->>'battery', '[^0-9]', '', 'g'))::INTEGER > 5000;
```

---

## **📌 Step 4: Indexing JSONB for Faster Queries**  
To speed up searches, we add a **GIN index** on JSONB fields.

```sql
CREATE INDEX idx_metadata ON products USING GIN (metadata);
```

✅ **Queries filtering by JSONB attributes now run much faster.**  

---

## **📌 Step 5: Running Full-Text Search on JSONB Data**  
Find products **where metadata contains "SSD"**:

```sql
SELECT name, metadata
FROM products
WHERE metadata::TEXT ILIKE '%SSD%';
```

✅ **Allows searching across nested JSONB fields.**  

---

## **📌 Step 6: Updating JSONB Data**  
### **1️⃣ Adding a New Attribute**
Add `"weight": "2kg"` to **Laptop X1**:

```sql
UPDATE products
SET metadata = jsonb_set(metadata, '{weight}', '"2kg"')
WHERE name = 'Laptop X1';
```

### **2️⃣ Modifying an Existing Attribute**
Change the **battery capacity** of **Phone Z9**:

```sql
UPDATE products
SET metadata = jsonb_set(metadata, '{battery}', '"5000mAh"')
WHERE name = 'Phone Z9';
```

✅ **JSONB fields can be updated dynamically without modifying the table schema.**  

---

## **📌 Recap**  
| Step | Task |
|------|------|
| **Step 1** | Understand JSON vs. JSONB differences |
| **Step 2** | Create a table with JSONB fields |
| **Step 3** | Insert dynamic JSONB data |
| **Step 4** | Query JSONB data efficiently |
| **Step 5** | Add a GIN index for optimization |
| **Step 6** | Perform full-text search on JSONB |
| **Step 7** | Update JSONB fields dynamically |

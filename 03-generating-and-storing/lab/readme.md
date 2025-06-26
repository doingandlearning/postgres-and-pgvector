### Lab: Evolving the Code - From Single Book Entry to Dynamic Data Integration

---

#### **Objective**
Transform the starting code into a fully-functional script that:
1. Fetches data dynamically from the Open Library API.
2. Processes multiple books across different categories.
3. Stores the data and embeddings in a PostgreSQL database.

---

Note: You can run the output of this lab in it's own docker container or on your local machine.

---

### **Step-by-Step Lab**

---

#### **Step 1: Understanding the Starting Code**
1. **Objective of the Starting Code:**
   - Generate embeddings for a single book (`The Great Gatsby`).
   - Insert the book data and embedding into the database.

2. **Run the Starting Code:**
   - Set up the database and ensure the `items` table exists.
   - Verify that the single book entry is successfully inserted.

**Checkpoint:**  
Ensure the embedding is generated, and the record is visible in the database.

---

#### **Step 2: Refactoring for Dynamic Data**

1. **Add a Function to Fetch Data from an External API:**
   - Introduce the `fetch_books()` function to retrieve books from Open Library's API.
   - Categories to query: Programming, Web Development, AI, Computer Science, Software Engineering.
   - Fetch up to 10 books per category.

2. **Implementation:**
   - Use Python’s `requests` library to query Open Library's API.
   - Extract relevant fields (`title`, `authors`, `first_publish_year`, `subject`) for each book. You can add additional fields to the metadata object if you'd prefer.
   - Format the data into a consistent structure.

**Code Example:**
   ```python
   def fetch_books():
       categories = ["programming", "web_development", "ai", "computer_science"]
       all_books = []

       for category in categories:
           url = f"https://openlibrary.org/subjects/{category}.json?limit=10"
           response = requests.get(url)
           data = response.json()
           books = data.get("works", [])

           for book in books:
               all_books.append({
                   "title": book.get("title", "Untitled"),
                   "authors": [author.get("name", "Unknown") for author in book.get("authors", [])],
                   "first_publish_year": book.get("first_publish_year", "Unknown"),
                   "subject": category,
               })

       return all_books
   ```

**Checkpoint:**  
Print the fetched data to verify its structure.

---

#### **Step 3: Generate Embeddings for Each Book**
1. Use the `get_embedding()` function to create an embedding for the book description.
2. Description format: Combine title, authors, year, and subject into a coherent sentence.

**Example:**
   ```python
   description = (
       f"Book titled '{book['title']}' by {', '.join(book['authors'])}. "
       f"Published in {book['first_publish_year']}. "
       f"This is a book about {book['subject']}."
   )
   embedding = get_embedding(description)
   ```

**Checkpoint:**  
Ensure the embeddings are generated correctly for multiple books.

---

#### **Step 4: Insert Multiple Books into the Database**
1. Refactor `load_data_db()` into `load_books_to_db()` to handle multiple records.
2. Use a loop to iterate over books fetched by `fetch_books()`.
3. Insert each book’s data and its corresponding embedding into the database.

**Code Example:**
   ```python
   cur.execute(
       """
       INSERT INTO items (name, item_data, embedding)
       VALUES (%s, %s, %s)
       """,
       (book["title"], json.dumps(book), embedding),
   )
   ```

**Checkpoint:**  
Run the code and check the `items` table to ensure all books are inserted correctly.

---

#### **Step 5: Error Handling**
1. Wrap the database operations in a `try-except` block.
2. Print meaningful error messages and stack traces to debug issues.

**Code Example:**
   ```python
   try:
       load_books_to_db()
   except Exception as e:
       traceback.print_exc()
       print(f"Error loading books: {e}")
   ```

**Checkpoint:**  
Deliberately introduce an error (e.g., invalid database URL) to test error handling.

---

#### **Step 6: Final Testing**
1. Test the script end-to-end:
   - Ensure data is fetched dynamically.
   - Validate embeddings are generated for each book.
   - Check that all records are inserted into the database.

2. Verify:
   - Use SQL queries to inspect the `items` table.
   - Ensure the correct number of records exist and the data is complete.

---

#### **Bonus Task: Improving Efficiency**
1. Add **batch insertion** for large datasets to reduce database overhead.
2. Use **placeholder embeddings** (e.g., zero vectors) for testing if embedding generation fails.

---

### **Expected Outcome**
Participants will have transformed the starting code into a robust script that dynamically fetches, processes, and stores book data and embeddings in a PostgreSQL database. The final solution should handle multiple records efficiently and include proper error handling. 


# Lab: Chunking and Querying "Alice in Wonderland"

## Objective
In this lab, you will implement a pipeline to chunk a PDF version of "Alice in Wonderland", store the chunks and their embeddings in a database, and then run a vector similarity search to answer a question.

## The Question
What is Alice's sister's name?

*Hint: The answer is in the first paragraph of the book.*

## Instructions

### Part 1: Ingest the Document
1.  **Complete the `ingest.py` script:**
    *   You will find a starter script in the `start/` directory.
    *   Your task is to fill in the logic to:
        a.  Read the `alice.pdf` file (provided in the `data` directory).
        b.  Chunk the text using a simple word-based approach.
        c.  For each chunk, generate a (dummy) embedding using the provided `embed` function.
        d.  Insert each chunk's data (`id`, `pdf_id`, `text`, `embedding`) into the `docs` table in your PostgreSQL database.
2.  **Run the script:**
    *   Make sure your Docker environment is running (`docker compose up -d`).
    *   Execute your script to populate the database.

### Part 2: Query for the Answer
1.  **Complete the `query.py` script:**
    *   You will find a starter script in the `start/` directory.
    *   Your task is to:
        a.  Define the `query_text`: "What is the name of Alice's sister?"
        b.  Generate an embedding for the `query_text`.
        c.  Write a SQL query to find the most similar chunk in the database using cosine similarity (`<=>`).
        d.  Fetch and print the top result.
2.  **Run the script:**
    *   Execute your `query.py` script and examine the output. Does the returned chunk contain the answer to the question?

## Success Criteria
You've completed the lab when your `query.py` script successfully retrieves the chunk of text that mentions Alice's sister sitting on the bank with her.

Good luck! You can find a complete solution in the `solution/` directory if you get stuck. 
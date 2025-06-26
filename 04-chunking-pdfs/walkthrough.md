# 04: Chunking PDFs for Vector Ingestion

This lesson covers strategies for breaking down large PDF documents into smaller chunks suitable for vector embedding and retrieval.

## Learning Objectives

- Understand why chunking is crucial for working with large documents and LLMs.
- Compare different chunking strategies: fixed-size, semantic, and structure-aware.
- Implement a simple, plain-Python chunking pipeline.
- Learn how to store document chunks with metadata to link back to the source.
- See how to perform batch embedding using a local model in a Docker container.
- Discuss how to evaluate chunk size and overlap for retrieval effectiveness.

## Slide by Slide

### 1. Why chunk?

LLMs have a limited context window. We can't just feed a 100-page document into a prompt. By chunking documents, we can retrieve only the most relevant sections to a user's query at runtime. This balances the need for comprehensive information (recall) with the cost and performance of the LLM call.

### 2. Chunking strategies

There are several ways to split a document:

- **Fixed-size chunking**: The simplest method. Split the text into chunks of `N` tokens, often with some overlap (`M` tokens) to preserve context between chunks.
- **Content-aware chunking**: Splitting based on document structure, like headings, paragraphs, or other semantic boundaries.
- **Semantic splitting**: Using NLP techniques (like TextTiling) to identify topic shifts and split the document accordingly.

### 3. Plain-Python pipeline

We can build a straightforward chunking pipeline without complex libraries like LangChain. The process looks like this:

1.  Extract text from the PDF (e.g., using `PyPDF2`).
2.  Split the text into chunks (e.g., using `textwrap.wrap` or a custom function).
3.  Generate an embedding for each chunk.
4.  Store the chunk and its embedding.

Here's a reference implementation:

```python
import pathlib, uuid, psycopg
from PyPDF2 import PdfReader
from textwrap import wrap
from my_local_embedding import embed  # your Docker container exposes this

def chunks_from_pdf(path, tokens=300, overlap=50):
    txt = "\n".join(page.extract_text() for page in PdfReader(path).pages)
    # naïve token split
    words = txt.split()
    for start in range(0, len(words), tokens - overlap):
        yield " ".join(words[start:start + tokens])

conn = psycopg.connect("postgresql://pgvector:@localhost/db")
with conn, conn.cursor() as cur:
    for chunk in chunks_from_pdf("alice.pdf"):
        vec = embed(chunk)              # returns list[float]
        cur.execute(
            "INSERT INTO docs (id, pdf_id, page, text, embedding) VALUES (%s,%s,%s,%s,%s)",
            (uuid.uuid4(), "alice", None, chunk, vec)
        )
```

### 4. Metadata schema

When storing chunks, it's vital to include metadata. This allows you to trace a retrieved chunk back to its source. A good schema includes:

- `id`: A unique identifier for the chunk.
- `pdf_id`: An identifier for the source PDF.
- `page`: The page number where the chunk originated.
- `text`: The chunk of text itself.
- `embedding`: The vector representation of the text.

```sql
CREATE TABLE
  docs (
    id UUID PRIMARY KEY,
    pdf_id TEXT,
    page INTEGER,
    text TEXT,
    embedding VECTOR(1024)
  );
```

### 5. Batch embedding script

To process large documents efficiently, embed chunks in batches. This reduces the number of database round-trips. A simple script could loop through chunks, accumulate a batch (e.g., 100 chunks), and commit to the database every 1,000 rows.

### 6. Lab: "Alice in Wonderland"

The hands-on lab for this section will have you chunk the text of "Alice in Wonderland", embed the chunks, and then write a query to find the answer to the question: "What is Alice's sister's name?". This will give you practical experience with the concepts covered.

### 7. Performance tips

- **Multiprocessing**: Use Python's `multiprocessing` module to parallelize the embedding process and speed up ingestion.
- **Progress Bars**: Use a library like `tqdm` to monitor the progress of long-running embedding jobs.
- **Docker Memory**: When running embedding models in Docker, ensure the container has sufficient memory allocated.

### 8. Common pitfalls

- **OCR Errors**: Scanned PDFs may contain OCR errors that corrupt the text.
- **Identical Chunks**: Poor chunking can lead to identical or near-identical chunks, which is inefficient.
- **Forgetting Overlap**: Not using overlap between chunks can cause you to lose context at the boundaries.
- **Page breaks**: A naive implementation may not handle page breaks correctly, splitting a sentence in half.

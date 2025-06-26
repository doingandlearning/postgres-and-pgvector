---
marp: true
theme: uncover
---

# 04: Chunking PDFs for Vector Ingestion

---

## Why Chunk?

- **LLM Context Windows**: Language models have a fixed input size. We can't pass a full 100-page document.
- **Recall vs. Cost**: We need to find the most relevant information (high recall) without overwhelming the LLM (high cost).
- **Strategy**: Break down large documents into smaller, indexed pieces. At query time, retrieve only the relevant pieces to build a concise context for the LLM.

---

## Chunking Strategies

1.  **Fixed-Size**: Simple and effective.
    - Split text into `N` tokens.
    - Use `M` tokens of overlap to preserve context across chunks.
2.  **Heading-Aware**: Use document structure.
    - Split text based on headings, sections, or paragraphs.
3.  **Semantic Split**: Use NLP to find topic boundaries.
    - Algorithms like TextTiling can detect shifts in topic.

---

## Plain-Python Pipeline

You don't need a heavy framework to get started.

```python
// 1. Extract text from PDF
import PyPDF2
reader = PyPDF2.PdfReader("my_doc.pdf")
text = "\n".join(p.extract_text() for p in reader.pages)

// 2. Naive word-based chunking
words = text.split()
chunks = [" ".join(words[i:i+300]) for i in range(0, len(words), 250)]

// 3. Embed and store (next steps)
for chunk in chunks:
    embedding = model.embed(chunk)
    database.store(chunk, embedding)
```

---

## Metadata Schema

Don't just store the vector; store information that links it back to the source.

**Table: `docs`**
| Column | Type | Description |
|---|---|---|
| `id` | `UUID` | Primary key for the chunk |
| `pdf_id` | `TEXT` | Identifier for the source PDF |
| `page` | `INTEGER` | Page number of the chunk |
| `text` | `TEXT` | The actual text content of the chunk |
| `embedding` | `VECTOR(384)` | The embedding vector |

---

## Batch Embedding Script

Avoid committing to the database one row at a time. Process in batches for much better performance.

```python
# Loop with chunk_size=100; commit every 1k rows.
batch = []
for chunk in all_chunks:
  batch.append( (uuid.uuid4(), "alice", None, chunk, embed(chunk)) )
  if len(batch) >= 1000:
    # Use fast COPY command to insert batch
    with cur.copy(...) as copy:
        for record in batch:
            copy.write_row(record)
    batch = [] # Reset batch
# Commit final batch...
```

---

## Lab: Chunk Alice!

"Chunk *Alice in Wonderland*, embed its text, and answer the question: **What is Alice's sister's name?**"

This lab will give you hands-on experience with:
- Implementing a chunking function.
- Storing chunks and vectors in `psycopg`.
- Writing a query to find the most relevant chunk.

---

## Performance Tips

- **Multiprocessing**: Use `multiprocessing.Pool` to run embedding generation in parallel across CPU cores.
- **Progress Bars**: Long ingestion job? Use a library like `tqdm` to visualize progress.
- **Docker Memory Flags**: Embedding models can be memory-hungry. Make sure your Docker container has enough RAM allocated (`--memory="4g"`).

---

## Common Pitfalls

- **OCR Errors**: Text from scanned PDFs can be messy.
- **Identical Chunks**: Whitespace or boilerplate can lead to useless, identical chunks.
- **Forgetting Overlap**: Losing context between chunks can hurt retrieval accuracy.
- **Page Breaks**: Naively chunking can split sentences right down the middle. A more robust solution would handle this. 
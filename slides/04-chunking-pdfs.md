# 04: Chunking PDFs for Vector Ingestion

---

## Why Chunk?

- <span class="fragment"><strong>LLM Context Windows</strong>: Language models have a fixed input size. We can't pass a full 100-page document.</span>
- <span class="fragment"><strong>Recall vs. Cost</strong>: We need to find the most relevant information (high recall) without overwhelming the LLM (high cost).</span>
- <span class="fragment"><strong>Strategy</strong>: Break down large documents into smaller, indexed pieces. At query time, retrieve only the relevant pieces to build a concise context for the LLM.</span>

---

## Chunking Strategies

1. <span class="fragment"><strong>Fixed-Size</strong>: Simple and effective.</span>
   - <span class="fragment">Split text into <code>N</code> tokens.</span>
   - <span class="fragment">Use <code>M</code> tokens of overlap to preserve context across chunks.</span>

---

## Chunking Strategies (cont.)

2. <span class="fragment"><strong>Heading-Aware</strong>: Use document structure.</span>
   - <span class="fragment">Split text based on headings, sections, or paragraphs.</span>

---

## Chunking Strategies (cont.)

3. <span class="fragment"><strong>Semantic Split</strong>: Use NLP to find topic boundaries.</span>
   - <span class="fragment">Algorithms like TextTiling can detect shifts in topic.</span>

---

## Plain-Python Pipeline

<span class="fragment">You don't need a heavy framework to get started.</span>

---

## Plain-Python Pipeline (cont.)

```python
# 1. Extract text from PDF
import PyPDF2
reader = PyPDF2.PdfReader("my_doc.pdf")
text = "\n".join(p.extract_text() for p in reader.pages)
```

````

---

## Plain-Python Pipeline (cont.)

```python
# 2. Naive word-based chunking
words = text.split()
chunks = [" ".join(words[i:i+300]) for i in range(0, len(words), 250)]
```

---

## Plain-Python Pipeline (cont.)

```python
# 3. Embed and store (next steps)
for chunk in chunks:
    embedding = model.embed(chunk)
    database.store(chunk, embedding)
```

---

## Metadata Schema

<span class="fragment">Don't just store the vector; store information that links it back to the source.</span>

---

## Metadata Schema (cont.)

| Column      | Type          | Description                          |
| ----------- | ------------- | ------------------------------------ |
| `id`        | `UUID`        | Primary key for the chunk            |
| `pdf_id`    | `TEXT`        | Identifier for the source PDF        |
| `page`      | `INTEGER`     | Page number of the chunk             |
| `text`      | `TEXT`        | The actual text content of the chunk |
| `embedding` | `VECTOR(384)` | The embedding vector                 |

---

## Batch Embedding Script

<span class="fragment">Avoid committing to the database one row at a time. Process in batches for much better performance.</span>

---

## Batch Embedding Script (cont.)

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

<span class="fragment">"Chunk <em>Alice in Wonderland</em>, embed its text, and answer the question: <strong>What is Alice's sister's name?</strong>"</span>

---

## Lab: Chunk Alice! (cont.)

This lab will give you hands-on experience with:

- <span class="fragment">Implementing a chunking function.</span>
- <span class="fragment">Storing chunks and vectors in <code>psycopg</code>.</span>
- <span class="fragment">Writing a query to find the most relevant chunk.</span>

---

## Performance Tips

- <span class="fragment"><strong>Multiprocessing</strong>: Use <code>multiprocessing.Pool</code> to run embedding generation in parallel across CPU cores.</span>
- <span class="fragment"><strong>Progress Bars</strong>: Long ingestion job? Use a library like <code>tqdm</code> to visualize progress.</span>
- <span class="fragment"><strong>Docker Memory Flags</strong>: Embedding models can be memory-hungry. Make sure your Docker container has enough RAM allocated (<code>--memory="4g"</code>).</span>

---

## Common Pitfalls

- <span class="fragment"><strong>OCR Errors</strong>: Text from scanned PDFs can be messy.</span>
- <span class="fragment"><strong>Identical Chunks</strong>: Whitespace or boilerplate can lead to useless, identical chunks.</span>
- <span class="fragment"><strong>Forgetting Overlap</strong>: Losing context between chunks can hurt retrieval accuracy.</span>
- <span class="fragment"><strong>Page Breaks</strong>: Naively chunking can split sentences right down the middle. A more robust solution would handle this.</span>
````

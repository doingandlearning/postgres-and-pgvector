# PDF Chunking: From Simple to Complex

This module demonstrates a progressive approach to PDF document processing, starting with basic text extraction and evolving into sophisticated structure-aware chunking. Each script builds upon the previous one, introducing new concepts and techniques.

## Script Progression Overview

1. **01-simple-chunker.py** - Basic text extraction and fixed-size chunking
2. **02-store-chunks.py** - Adding database storage and embeddings
3. **03-batch-embed.py** - Optimizing for performance with batch processing
4. **04-complex-pdf-chunker.py** - Advanced structure-aware chunking

---

## Script 1: Simple Chunking (`01-simple-chunker.py`)

### Purpose
Introduces the fundamental concepts of PDF text extraction and basic chunking while preserving page context.

### Key Concepts

**Page-Aware Chunking**: Unlike naive text splitting, this approach tracks which page each word comes from:
```python
words_with_pages = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        # Store each word with its 1-indexed page number
        words_with_pages.extend([(word, i + 1) for word in text.split()])
```

**Sliding Window with Overlap**: Prevents important information from being split across chunk boundaries:
```python
for start in range(0, len(words_with_pages), tokens - overlap):
    chunk_data = words_with_pages[start : start + tokens]
```

**Why This Matters**:
- **Context Preservation**: Maintains page numbers for source attribution
- **Information Continuity**: Overlap ensures sentences aren't arbitrarily cut
- **Consistent Sizing**: Fixed token counts help with LLM processing limits

### Limitations
- No semantic understanding of content structure
- Treats all text equally (headers, body, footnotes)
- No handling of tables, images, or complex layouts

---

## Script 2: Database Storage (`02-store-chunks.py`)

### Purpose
Extends basic chunking by adding persistent storage and embedding generation for each chunk.

### New Concepts

**Database Integration**: Stores chunks with rich metadata:
```sql
INSERT INTO docs (id, pdf_id, page, text, embedding) 
VALUES (%s, %s, %s, %s, %s)
```

**Embedding Generation**: Each chunk gets a vector representation:
```python
embedding = get_embedding(chunk)
```

**Error Handling**: Graceful degradation when embeddings fail:
```python
if embedding is None:
    print(f"Skipping chunk due to embedding error: '{chunk[:50]}...'")
    continue
```

### Why This Matters
- **Persistence**: Chunks are saved for later retrieval
- **Searchability**: Embeddings enable semantic search
- **Metadata**: Page numbers allow source attribution
- **Robustness**: Continues processing even if individual chunks fail

### Performance Considerations
- One database transaction per chunk (inefficient for large documents)
- Individual embedding API calls (could be batched)
- No connection pooling

---

## Script 3: Batch Processing (`03-batch-embed.py`)

### Purpose
Optimizes the storage process for large documents by processing chunks in batches.

### Key Improvements

**Batch Database Writes**: Uses PostgreSQL's COPY command for efficiency:
```python
with cur.copy("COPY docs (id, pdf_id, page, text, embedding) FROM STDIN") as copy:
    for record in batch:
        copy.write_row(record)
```

**Memory Management**: Processes chunks in configurable batch sizes:
```python
batch_size = 100
# ... collect chunks in batches ...
if len(batch) >= batch_size:
    # Process batch and clear memory
    batch = []
```

**Vector Format Handling**: Converts embeddings to strings for COPY command:
```python
batch.append((str(uuid.uuid4()), pdf_id, page_num, chunk, str(embedding)))
```

### Performance Benefits
- **Database Efficiency**: COPY is much faster than individual INSERTs
- **Memory Control**: Batching prevents memory exhaustion on large documents
- **Transactional Safety**: Batches can be committed incrementally

### When to Use This Approach
- Large PDFs (hundreds of pages)
- Production environments with performance requirements
- When processing multiple documents in sequence

---

## Script 4: Complex Structure-Aware Chunking (`04-complex-pdf-chunker.py`)

### Purpose
Demonstrates advanced PDF processing that understands document structure, handles multimedia content, and uses semantic chunking strategies.

### Advanced Concepts

#### 1. **Visual Content Detection**
Identifies pages with diagrams, charts, or complex layouts:
```python
def page_has_diagram(page, threshold=20, area_ratio=0.05):
    num_graphical_objects = len(page.rects) + len(page.curves) + len(page.lines)
    # ... analysis logic ...
    return has_complex_graphics
```

#### 2. **Page Rendering for Complex Content**
Converts diagram-heavy pages to images:
```python
def render_page_as_image(page, page_num, output_dir="extracted_pages"):
    im = page.to_image(resolution=300)
    image_path = os.path.join(output_dir, f"page_{page_num}.png")
    im.save(image_path, format="PNG")
```

#### 3. **Table Extraction and Placeholder System**
Preserves table structure while maintaining text flow:
```python
tables = page.extract_tables()
for i, table in enumerate(tables, start=1):
    placeholder = f"{{{{ TABLE_PAGE_{page_num}_{i} }}}}"
    text += f"\n\n{placeholder}"
```

#### 4. **Legal/Technical Document Chunking**
Uses domain-specific knowledge to split on semantic boundaries:
```python
LEGAL_CLAUSE_SPLITTERS = [
    r"Provided however",
    r"Except as", 
    r"Notwithstanding",
]
```

#### 5. **Intelligent Chunk Classification**
Tags chunks based on content type:
```python
def classify_chunk(text):
    if any(signal.lower() in text.lower() for signal in LEGAL_CLAUSE_SPLITTERS):
        return "exception_clause"
    elif "{{ TABLE" in text:
        return "table_reference"
    # ... more classifications
```

### Why This Complexity Matters

**Document Fidelity**: Preserves the original document's structure and meaning rather than treating it as plain text.

**Multimedia Handling**: Tables and diagrams are critical in technical documents - losing them means losing key information.

**Semantic Chunking**: Legal and technical documents have logical structure that should guide chunking decisions.

**Metadata Richness**: Classification helps downstream systems understand what type of content they're working with.

### Real-World Applications

- **Legal Document Processing**: Contracts, regulations, court filings
- **Technical Manuals**: Software documentation, engineering specs
- **Research Papers**: Academic papers with figures and tables
- **Compliance Documents**: Regulatory filings with complex formatting

---

## Choosing the Right Approach

| Document Type | Recommended Script | Reasoning |
|---------------|-------------------|-----------|
| Simple text documents | Script 1 or 2 | Basic chunking sufficient |
| Large document collections | Script 3 | Performance matters |
| Legal/technical documents | Script 4 | Structure preservation critical |
| Documents with tables/diagrams | Script 4 | Multimedia content handling |

## Key Takeaways

1. **Start Simple**: Basic chunking works for many use cases
2. **Optimize When Needed**: Batch processing for performance
3. **Preserve Structure**: Complex documents need sophisticated handling
4. **Consider Context**: Domain knowledge improves chunking quality
5. **Test and Iterate**: Different approaches work for different document types

## Next Steps

After running these examples:
- Experiment with different chunk sizes and overlap values
- Try processing documents from your domain
- Evaluate retrieval quality with different chunking strategies
- Consider hybrid approaches that combine multiple techniques

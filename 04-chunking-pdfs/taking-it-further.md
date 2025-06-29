# Resources: Chunking and Performance Tips for Vector Ingestion

This resource sheet extends the topics from our workshop section **04: Chunking PDFs for Vector Ingestion.**

Below you’ll find advice, code snippets, and links for deeper exploration.

---

## Splitting Text by Headings

When documents are well-structured (e.g. PDFs with clear headings), splitting based on headings can preserve context far better than blind fixed-size chunks.

### Why Heading-Aware Splitting?

✅ Respects logical boundaries  
✅ Keeps paragraphs together  
✅ Reduces chances of splitting a sentence in half

### Simple Example

Suppose you’ve extracted a plain-text document where headings are in uppercase and separated by newlines.

```python
import re

text = """
INTRODUCTION
This is the introduction text.

METHODS
These are the methods.

RESULTS
These are the results.
"""

# Split by uppercase headings
sections = re.split(r"\n([A-Z ]+)\n", text)

# sections -> ['', 'INTRODUCTION', 'This is the introduction text.', 'METHODS', ...]
# Remove empty strings and group pairs
chunks = []
for i in range(1, len(sections), 2):
    heading = sections[i]
    body = sections[i + 1]
    chunks.append(f"{heading}\n{body}")

for chunk in chunks:
    print("----\n", chunk)
```

### Libraries and Tools

- **pdfplumber**: preserves layout and heading context when extracting PDFs
  → [https://github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)

- **PyMuPDF**: extract text with structural tags from PDFs
  → [https://pymupdf.readthedocs.io/](https://pymupdf.readthedocs.io/)

---

## Splitting Text by Semantic Boundaries

Instead of just headings or token sizes, you can split text by **semantic shifts** (topic changes). This reduces context fragmentation.

### TextTiling

TextTiling segments text into multi-paragraph blocks based on topic changes. Originally designed for plain text.

- Paper: [TextTiling: Segmenting Text into Multi-Paragraph Subtopic Passages](https://www.aclweb.org/anthology/J97-1003/)

- Python library:
  → [https://pypi.org/project/texttiling/](https://pypi.org/project/texttiling/)

### Example with TextTiling

```python
from texttiling import TextTilingTokenizer

tokenizer = TextTilingTokenizer()

text = """
Alice was beginning to get very tired of sitting by her sister...
Suddenly a White Rabbit with pink eyes ran close by her...
...

Then the March Hare and the Hatter were having tea together...
"""

tiles = tokenizer.tokenize(text)
for i, tile in enumerate(tiles):
    print(f"Tile {i}: {tile[:100]}")
```

Limitations:

- Works best on plain text
- Not perfect for scanned PDFs or documents with heavy layout

---

## Multiprocessing for Faster Embeddings

Embedding large documents can be slow. Instead of looping chunk-by-chunk, use **multiprocessing** to parallelise your embedding calls.

### Example with multiprocessing.Pool

```python
from multiprocessing import Pool
from my_embedding_model import embed

chunks = ["chunk one text", "chunk two text", ...]

with Pool(processes=4) as pool:
    embeddings = pool.map(embed, chunks)

# embeddings now contains a list of vectors
```

Tips:

- Watch memory usage. Large models can exhaust RAM if you spawn too many processes.
- For async models (e.g. HTTP APIs), use `asyncio` or concurrent libraries instead.

More on Python multiprocessing:
→ [https://docs.python.org/3/library/multiprocessing.html](https://docs.python.org/3/library/multiprocessing.html)

---

## Progress Bars for Long Tasks

Long-running chunking or embedding jobs benefit from progress bars, so you know they haven’t stalled.

### Using tqdm

The [`tqdm`](https://tqdm.github.io/) library is the gold standard for progress bars.

#### Example

```python
from tqdm import tqdm

for chunk in tqdm(chunks, desc="Embedding chunks"):
    embedding = embed(chunk)
    # store embedding
```

#### With multiprocessing

`tqdm` also works with multiprocessing using `tqdm.contrib.concurrent`:

```python
from tqdm.contrib.concurrent import process_map

# process_map automatically adds a progress bar
embeddings = process_map(embed, chunks, max_workers=4)
```

---

## More Resources

- **LangChain Text Splitters**
  [https://python.langchain.com/docs/modules/data_connection/document_transformers/text_splitter/](https://python.langchain.com/docs/modules/data_connection/document_transformers/text_splitter/)

- **Haystack Text Splitters**
  [https://haystack.deepset.ai/tutorials/first-qa](https://haystack.deepset.ai/tutorials/first-qa)

- **pdfplumber** – PDF parsing
  [https://github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)

- **TextTiling Paper**
  [TextTiling: Segmenting Text into Multi-Paragraph Subtopic Passages](https://www.aclweb.org/anthology/J97-1003/)

- **tqdm Docs**
  [https://tqdm.github.io/](https://tqdm.github.io/)

---

Happy chunking!

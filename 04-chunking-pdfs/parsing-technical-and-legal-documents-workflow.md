# 📄 **Handout: Chunking Technical & Legal Documents for Vector Search**

## Why “Naive” Chunking Falls Short

✅ Works for plain text
❌ Breaks down for:

- Equations (LaTeX, images)
- Tables and figures
- Legal clauses (exceptions, “notwithstanding,” etc.)
- Contradictory or overlapping rules

Blind splitting risks:

- Losing critical context
- Splitting rules from their exceptions
- Dropping key non-text objects

---

## Principles for Better Chunking

### 1. Parse Structured Objects

Instead of extracting only raw text:

- Identify:

  - Headings
  - Paragraphs
  - Tables
  - Figures + captions
  - Equations (LaTeX or images)

- Replace objects with placeholders in text, e.g. `{{ EQUATION_BLOCK_1 }}`

→ Preserve relationships between text and visuals/tables.

---

### 2. Chunk at Meaningful Boundaries

- Headings → natural split points
- Legal signals:

  - “Provided however”
  - “Except as…”
  - “Notwithstanding”

- Semantic shifts → TextTiling or custom models

→ Avoid splitting mid-rule or mid-topic.

---

### 3. Maintain Context Across Chunks

- Add **token overlap** between chunks (e.g. 100–200 tokens)
- Keep rules and exceptions close

→ Prevent contradictory interpretations.

---

### 4. Tag Chunks with Metadata

Record:

- Heading or section title
- Page number
- Chunk type:

  - Rule
  - Exception
  - Definition
  - Table, figure

→ Improves filtering & retrieval relevance.

---

### 5. Hybrid Retrieval for Contradictions

Legal & technical docs often contain contradictions. Retrieve:

- Rules **and** their exceptions
- Multiple chunks if context is split

Combine:

- Embedding similarity
- Keyword search
- Metadata filters

→ Ensures correct legal/technical interpretation.

---

## Suggested Tools

| Purpose                | Tools                           |
| ---------------------- | ------------------------------- |
| PDF parsing            | pdfplumber, PyMuPDF, Grobid     |
| Table extraction       | pdfplumber, Tabula              |
| Math OCR               | MathPix, pdf2xml                |
| Legal clause detection | LexNLP                          |
| Semantic splitting     | TextTiling, LangChain splitters |
| Progress bars          | tqdm                            |
| Parallel embeddings    | multiprocessing, asyncio        |

---

## Example Workflow

✅ Parse PDF → extract objects

✅ Replace objects with placeholders

✅ Chunk text using:

- Headings
- Semantic boundaries
- Legal clause patterns

✅ Tag chunks with metadata

✅ Embed text + references

✅ Hybrid retrieval to combine:

- Embeddings
- Keywords
- Metadata filters

---

## Analogy

> Splitting legal or technical documents naïvely is like cutting a cake in random shapes and hoping each slice still tells the whole recipe.
>
> Instead, cut **by the layers**—so every slice contains the sponge, filling, and icing.

---

## Further Reading

- pdfplumber → [https://github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)
- Grobid → [https://github.com/kermitt2/grobid](https://github.com/kermitt2/grobid)
- TextTiling → [TextTiling Paper](https://www.aclweb.org/anthology/J97-1003/)
- LexNLP → [https://github.com/LexPredict/lexpredict-lexnlp](https://github.com/LexPredict/lexpredict-lexnlp)
- LangChain Text Splitters → [Docs](https://python.langchain.com/docs/concepts/text_splitters/#approaches)

---

**Key Takeaway:**
→ **Don’t just chunk by size — chunk by meaning.**
→ Preserve context, objects, and legal/technical logic for reliable vector search.

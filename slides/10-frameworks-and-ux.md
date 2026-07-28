---
title: "**Beyond Raw SQL**"
sub_title: Frameworks & UX for Production RAG
author: Kevin Cunningham
---

## Opening scenario

Your capstone support-ticket search is working. A colleague on another team
says: "Nice — but why didn't you just use LangChain? We built the same thing
in an afternoon."

**Type in chat: they're right / they're missing something / depends**

We'll come back to this at the end.

<!--
speaker_note: |
  Expect a split. Some will say frameworks are strictly faster to build with.
  Some will point out they just spent two days learning what's underneath the
  framework for a reason. Don't resolve it yet - park it and move on.
-->

<!-- end_slide -->

<!-- jump_to_middle -->

Part 1 — What Frameworks Actually Abstract
===

<!-- end_slide -->

## What you built by hand

Over the last two days, every one of these was a line of SQL or Python you
wrote yourself:

<!-- incremental_lists: true -->

- Calling Ollama to get an embedding
- Storing it in a `vector` column
- Writing the `<=>` distance query
- Chunking a PDF into overlapping windows
- Combining vector search with `WHERE` clauses and JSONB
- Passing retrieved context into a prompt

<!-- incremental_lists: false -->

**A framework's entire pitch is: stop writing this by hand.**

<!-- end_slide -->

## The abstraction, concretely

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

**What you wrote (Module 05/08)**

```python
resp = requests.post(
    "http://localhost:11434/api/embeddings",
    json={"model": "bge-m3", "prompt": query}
)
vec = resp.json()["embedding"]

cur.execute("""
    SELECT name FROM items
    ORDER BY embedding <=> %s
    LIMIT 5
""", (vec,))
```

<!-- column: 1 -->

**Same thing, framework-wrapped**

```python
from langchain_postgres import PGVector

store = PGVector(
    embeddings=embedding_model,
    connection=conn_string,
)

store.similarity_search(query, k=5)
```

<!-- reset_layout -->

**Type in chat: this is a fair trade / this is hiding too much**

<!--
speaker_note: |
  Push on this: the right side hides the embedding call, the HTTP round trip,
  and the SQL entirely. That's the whole debate - convenience vs. control.
-->

<!-- end_slide -->

## Two frameworks, two different bets

| | LangChain | LlamaIndex |
|---|---|---|
| Core bet | Orchestration - chains, agents, tools | Retrieval - ingestion, indexing, query engines |
| Vector store abstraction | `VectorStore` interface (pgvector, Chroma, Pinecone...) | `VectorStoreIndex` over the same backends |
| Chunking | You configure a splitter | Built-in node parsers, auto-chunking |
| Where pgvector fits | One of ~40 interchangeable backends | First-class integration, same pattern |
| Common 2026 pattern | Orchestration layer on top | Retrieval layer underneath |

**Which column would you reach for first for the capstone you just built?**

<!-- speaker_note: |
  Most production 2026 stacks actually run both - LangChain for the outer
  chain/agent logic, LlamaIndex underneath for the retrieval-specific
  primitives (nodes, indexes, query engines). Neither replaces the other.
-->

<!-- end_slide -->

## What you gain

<!-- incremental_lists: true -->

- Swap pgvector for Pinecone, Chroma, or Weaviate by changing one constructor call
- Built-in chunking strategies (semantic, recursive, sentence-window) without writing your own splitter
- Retrievers compose directly into chains, agents, and query engines
- A large ecosystem of loaders (PDF, Notion, Slack, S3...) instead of writing `pdfplumber` code by hand

<!-- end_slide -->

## What you lose

<!-- incremental_lists: true -->

- The `<=>` operator, the `EXPLAIN ANALYZE` plan, the actual SQL your query runs as - all one layer further away
- Framework-specific failure modes (dependency churn, breaking API changes between versions) replace SQL's stability
- Debugging "why is this result ranked here" now means stepping through framework internals, not reading a WHERE clause
- The hybrid-query patterns from Module 08 (JSONB extraction, weighted score fusion) don't map cleanly onto a generic `VectorStore` interface - you often drop back to raw SQL for exactly this kind of business logic

**The trade isn't free in either direction.**

<!-- end_slide -->

## Decision point

<!-- column_layout: [1, 3, 1] -->

<!-- column: 1 -->

**Rule of thumb:** reach for a framework when retrieval logic is generic
(embed, store, fetch top-k). Drop to raw SQL when the business logic is
specific to your schema - exactly the JSONB filtering and score fusion from
Module 08.

<!-- reset_layout -->

<!-- end_slide -->

<!-- jump_to_middle -->

Part 2 — UX Considerations
===

<!-- end_slide -->

## The gap nobody's query plan shows

A cosine distance of 0.31 vs. 0.34 means nothing to the person using your
support-ticket search. What they see is: an answer, and whether they trust it.

**Everything correct at the SQL level can still fail as a product.**

<!-- end_slide -->

## Latency is a UX problem, not just a performance one

<!-- incremental_lists: true -->

- Embedding call (Ollama/API round trip) + vector search + LLM generation = three sequential network hops, not one
- Users tolerate ~200ms for "search," but expect seconds for "generate an answer" - mismatched expectations break trust
- Streaming the generation token-by-token changes the perceived wait even when total time is identical

<!-- incremental_lists: false -->

**Type in chat: would you show a loading spinner, streamed tokens, or intermediate "searching tickets..." status?**

<!-- speaker_note: |
  There's no single right answer - the point is that this is a UI decision,
  not something pgvector or the framework decides for you.
-->

<!-- end_slide -->

## Show your work, or don't be trusted

<!-- column_layout: [2, 1] -->

<!-- column: 0 -->

A RAG answer with no visible source is indistinguishable from a hallucination
to the end user - even when it's fully grounded.

Production UIs typically surface:

<!-- incremental_lists: true -->

- Which retrieved chunk/ticket backed each claim
- A confidence or similarity signal, in plain language rather than a raw distance
- An expandable "source" the user can click into

<!-- column: 1 -->

```
Suggested fix (from ticket #4231,
similarity: high):

"Restart the sync service after
clearing the cache directory."

[View original ticket ->]
```

<!-- reset_layout -->

<!-- end_slide -->

## When retrieval comes back empty, or wrong

<!-- incremental_lists: true -->

- If nothing clears a relevance bar, say so - don't force the LLM to generate an answer from weak context anyway
- A wrong-but-fluent answer is worse for trust than "I couldn't find anything relevant"
- This is exactly the failure mode reranking (cross-encoder) targets: a bi-encoder's top-5 can look plausible and still be the wrong 5

<!-- incremental_lists: false -->


<!-- speaker_note: |
  Push rooms toward a concrete UI string, not just "handle the error." E.g.
  "No resolved ticket closely matches this issue - escalate to a human" vs.
  silently returning the best-available (but poor) match.
-->

<!-- end_slide -->

## Summary

<!-- incremental_lists: true -->

1. **Frameworks abstract the generic parts** (embed, store, fetch) but the business-specific hybrid logic from Module 08 often still needs raw SQL
2. **Latency across three sequential hops** (embed -> search -> generate) is a UI decision, not just an infra one
3. **Trust is built through visible sourcing** - show what was retrieved, not just the generated answer
4. **A confident wrong answer is worse than an honest "not found"** - especially without reranking to catch weak matches

<!-- end_slide -->

## Back to the opening scenario

Your colleague said "we built the same thing in an afternoon with LangChain."

**Now: what's actually different between your capstone and theirs?**

<!-- speaker_note: |
  Land the point: probably nothing at the demo level. The difference shows
  up the moment they need the JSONB-filtered, weighted-fusion hybrid query
  from Module 08 - the part a generic VectorStore interface doesn't express,
  and the part they now understand well enough to debug when the framework
  gets it wrong.
-->

<!-- end_slide -->

<!-- jump_to_middle -->

Questions?
===

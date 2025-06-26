# Building AI-Powered Search with PostgreSQL and Large Language Models

- **Dates**: 30th June & 1st July, 2025 (2 Days)
- **Instructor**: Kevin Cunningham
  - [Email](mailto:kevin@kevincunningham.co.uk)
  - [Website](https://kevincunningham.co.uk)
- **Repo**: [Link to this repository](https://github.com/doingandlearning/postgres-and-pgvector)
- **Miro Board**: [Link to course Miro board]()
- **Feedback Form**: [Link to feedback form]()

---

## Timings

- **9:30 - 11:00**: Session 1
- **11:00 - 11:15**: Coffee Break
- **11:15 - 12:45**: Session 2
- **12:45 - 1:45**: Lunch Break
- **1:45 - 3:15**: Session 3
- **3:15 - 3:30**: Tea Break
- **3:30 - 4:30**: Session 4

---

## Course Overview

This two-day course offers a practical, hands-on journey into building modern AI search applications. We'll explore how to leverage the power of vector embeddings and Large Language Models (LLMs) directly within a PostgreSQL database using the `pgvector` extension.

Our labs will progressively build your skills, starting with the fundamentals of generating and storing embeddings, and culminating in a final project where you'll build a complete AI-powered search and question-answering system for customer support tickets. By the end, you'll have the confidence to design and implement sophisticated, efficient, and scalable RAG (Retrieval Augmented Generation) pipelines.

---

## Course Modules

This course is divided into modules, each corresponding to a numbered directory in this repository.

- **02: Getting Setup**: An introduction to the core concepts of vector embeddings, `pgvector`, and the RAG pipeline. We'll also get our local Docker development environment up and running.

- **03: Generating & Storing Vectors**: We'll use a local Ollama model to generate high-quality embeddings and learn how to store them efficiently in our PostgreSQL database.

- **04: Chunking PDFs**: This module covers the critical process of chunking large documents. We'll build a Python pipeline to ingest PDFs, split them into manageable chunks, and store them with page metadata.

- **05: Querying with Vectors**: Learn the fundamentals of vector similarity search. We'll use `pgvector` operators (like Cosine Similarity and L2 Distance) to find the most semantically relevant documents for a user's query.

- **06: Querying with LLMs (RAG)**: We'll build a complete Retrieval Augmented Generation (RAG) pipeline to enhance search results and answer questions using an LLM, based on the context retrieved from our database.

- **07: JSON and JSONB**: Explore how to leverage PostgreSQL's powerful JSONB capabilities to store and query semi-structured metadata alongside vector embeddings for more precise, filtered searches.

- **08: Hybrid Querying**: Go beyond pure vector search by implementing hybrid techniques. We'll combine traditional keyword-based full-text search with semantic vector search for the best of both worlds.

- **09: Final Lab - AI Ticket Support System**: In this capstone project, we'll bring everything together to build a complete AI-powered search application that suggests solutions to new support tickets based on historical data.

# Non-Python Starter Guide

## Overview

This guide is for participants who want to focus on **understanding vector concepts and AI search principles** without getting deep into Python programming. Each lab module includes alternative approaches that minimize coding while maximizing learning.

## Philosophy

The key insight is that **the learning objectives remain the same** regardless of implementation approach:
- Understanding how text becomes vectors
- Learning similarity search concepts
- Grasping chunking strategies
- Building AI-powered applications

**The techniques transfer to any programming language or platform!**

## Available Approaches

Each lab offers multiple paths based on your comfort level:

### 🟢 Level 1: Configuration-Based (No Coding)
- Edit JSON configuration files
- Run pre-built Python scripts
- Focus entirely on concepts and SQL

### 🟡 Level 2: Template-Based (Minimal Coding)
- Fill in blanks in Python templates
- Modify parameters and settings
- Light programming practice

### 🔵 Level 3: CLI Tools (Command-Line)
- Use command-line interfaces
- No Python knowledge required
- Professional tool-like experience

## Lab-by-Lab Guide

### Module 03: Generating & Storing Vectors
**Location**: `03-generating-and-storing/lab/non-python-starter/`

**Key Learning**: How text becomes vectors and gets stored in databases

**Approaches Available**:
- **Config-based**: Edit `data_config.json` to specify what books to load
- **CLI tool**: `python book_loader.py --source open_library --categories "ai,programming"`
- **SQL-focused**: Pre-generated data with SQL exploration exercises

**Success Criteria**: Understand the text→embedding→database pipeline

---

### Module 04: Chunking PDFs
**Location**: `04-chunking-pdfs/lab/non-python-starter/`

**Key Learning**: How to break large documents into searchable pieces

**Approaches Available**:
- **Config-based**: Edit `config.json` and run `python ingest_configured.py`
- **Template-based**: Fill in blanks in `ingest_template.py`
- **CLI tool**: `python pdf_processor.py ingest --file alice.pdf --id alice`

**Success Criteria**: Understand chunking strategies and their impact on search quality

---

### Module 05: Querying with Vectors
**Key Learning**: How similarity search actually works

**Approaches Available**:
- **SQL-focused**: Direct PostgreSQL queries with pgvector operators
- **Helper scripts**: Generate embeddings, copy into SQL queries
- **CLI exploration**: Interactive similarity search commands

**Success Criteria**: Understand cosine similarity, distance metrics, and result ranking

---

### Module 06: Querying with LLMs (RAG)
**Key Learning**: How to enhance search results with AI-generated responses

**Approaches Available**:
- **Template-based**: Modify prompts and parameters in pre-built scripts
- **CLI tool**: Interactive RAG pipeline with different LLM settings
- **Prompt engineering**: Focus on crafting effective prompts

**Success Criteria**: Understand the retrieve→augment→generate pipeline

---

### Module 09: Final Lab - AI Ticket Support
**Key Learning**: Building a complete AI-powered application

**Approaches Available**:
- **Config-based**: JSON configuration for ticket categories and search parameters
- **CLI workflow**: Step-by-step commands to build the complete system
- **SQL-focused**: Complex queries combining vector, relational, and JSONB data

**Success Criteria**: Build a working AI support system using learned concepts

## Common Tools Across All Labs

### 1. Configuration Files
Most labs include `config.json` files that let you modify behavior without coding:

```json
{
  "database": {
    "host": "localhost",
    "port": "5050",
    "database": "pgvector"
  },
  "embedding": {
    "model": "bge-m3",
    "ollama_url": "http://localhost:11434/api/embed"
  },
  "chunk_size": 300,
  "chunk_overlap": 50
}
```

### 2. Helper Scripts
Each module includes utilities like:
- `generate_query_embedding.py "Your question"` - Convert text to vectors
- `check_database.py` - Verify data and connections
- `experiment_runner.py --experiment chunk_sizes` - Run learning experiments

### 3. SQL Templates
Pre-written queries you can copy and modify:
```sql
-- Find similar items
SELECT text, similarity_score
FROM docs
WHERE embedding <=> '[EMBEDDING_HERE]' 
ORDER BY similarity_score
LIMIT 5;
```

## Learning Strategy

### 1. Start with Configuration-Based Approaches
- Focus on understanding concepts first
- See immediate results without coding barriers
- Build confidence with the technology

### 2. Progress to Template-Based When Ready
- Practice light programming skills
- Understand the code structure
- Prepare for potential customization needs

### 3. Use CLI Tools for Professional Experience
- Experience tool-like interfaces
- Understand real-world workflows
- Build transferable skills

## Transferring Knowledge

The concepts you learn transfer directly to:

### Other Programming Languages
- **JavaScript/Node.js**: Same vector concepts, different syntax
- **Java/C#**: Same database patterns, different libraries
- **Go/Rust**: Same API principles, different implementations

### Cloud Platforms
- **AWS**: Bedrock embeddings, RDS with pgvector
- **Azure**: OpenAI embeddings, PostgreSQL Flexible Server
- **GCP**: Vertex AI embeddings, Cloud SQL

### AI Platforms
- **LangChain**: Higher-level abstractions of the same concepts
- **LlamaIndex**: Document processing with the same chunking principles
- **Pinecone/Weaviate**: Managed vector databases with similar query patterns

## Success Metrics

You're succeeding with this approach when you can:

1. **Explain the Concepts**: Describe how vector search works to a colleague
2. **Adapt to New Domains**: Apply chunking strategies to your own documents
3. **Debug Issues**: Understand why search results might be poor and how to improve them
4. **Design Systems**: Plan how to implement vector search in your own applications
5. **Choose Tools**: Evaluate different embedding models, databases, and approaches

## Getting Help

### Troubleshooting
Each lab includes comprehensive troubleshooting sections:
- Docker service issues
- Database connection problems
- Embedding generation failures
- Common SQL errors

### Experimentation Guides
Structured experiments to deepen understanding:
- "What happens if I change the chunk size?"
- "How do different embedding models compare?"
- "What makes a good vs bad search query?"

### Real-World Applications
Every concept includes examples of how it applies to different industries and use cases.

## Remember

**You don't need to be a Python expert to understand and apply AI search concepts!**

The goal is to understand:
- How text becomes searchable vectors
- How to structure data for AI applications  
- How to evaluate and improve search quality
- How to build complete AI-powered systems

These skills are valuable regardless of your eventual implementation technology. 
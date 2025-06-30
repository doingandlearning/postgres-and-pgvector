# Lab: Chunking and Querying "Alice in Wonderland" (Non-Python Starter)

## Objective
This lab focuses on understanding **vector concepts and chunking strategies** without requiring extensive Python programming. You'll use pre-built scripts with guided modifications and SQL-focused approaches.

## The Question
What is Alice's sister's name?

*Hint: The answer is in the first paragraph of the book.*

## Approach Options

You can choose from three different approaches based on your comfort level:

### Option A: Configuration-Based Approach (Recommended for Non-Python Users)

Use pre-built scripts where you only need to modify configuration files.

#### Step 1: Configure the Ingestion
1. **Edit `config.json`:**
   ```json
   {
     "pdf_path": "../data/alice.pdf",
     "pdf_id": "alice_in_wonderland",
     "chunk_size": 300,
     "chunk_overlap": 50,
     "database": {
       "host": "localhost",
       "port": "5050",
       "database": "pgvector",
       "user": "postgres",
       "password": "postgres"
     }
   }
   ```

2. **Run the pre-built ingestion script:**
   ```bash
   python ingest_configured.py
   ```

#### Step 2: Query Using SQL
1. **Generate query embedding using the helper script:**
   ```bash
   python generate_query_embedding.py "What is the name of Alice's sister?"
   ```
   
   This will output an embedding that you can copy.

2. **Run SQL query directly in PostgreSQL:**
   ```sql
   -- Connect to your database first
   -- docker exec -it pgvector-db psql -U postgres -d pgvector
   
   SELECT 
     text,
     page,
     embedding <=> '[YOUR_EMBEDDING_HERE]' as similarity
   FROM docs 
   WHERE pdf_id = 'alice_in_wonderland'
   ORDER BY similarity ASC 
   LIMIT 3;
   ```

### Option B: Guided Python with Templates

Use Python templates where you fill in specific values rather than writing code from scratch.

#### Step 1: Complete the Template
1. **Edit `ingest_template.py`:**
   - Fill in the blanks marked with `# TODO: FILL IN`
   - Most code is provided, you just need to specify:
     - File paths
     - Database connection details
     - Chunk parameters

#### Step 2: Run and Query
1. **Execute the completed template:**
   ```bash
   python ingest_template.py
   ```

2. **Use the query template:**
   ```bash
   python query_template.py
   ```

### Option C: Command-Line Interface

Use a command-line tool that handles all the Python complexity for you.

#### Step 1: Use CLI Tool
```bash
# Ingest the PDF
python pdf_processor.py ingest \
  --file ../data/alice.pdf \
  --id alice_in_wonderland \
  --chunk-size 300 \
  --overlap 50

# Query for similar text
python pdf_processor.py query \
  --question "What is the name of Alice's sister?" \
  --limit 3
```

## Learning Focus

Regardless of which approach you choose, focus on understanding:

1. **Chunking Strategy**: How does chunk size affect the results?
2. **Overlap Importance**: What happens if you change the overlap parameter?
3. **Vector Similarity**: How do the similarity scores relate to the relevance of results?
4. **Metadata Usage**: How does storing page numbers help with context?

## Experimentation Prompts

Try these modifications to deepen your understanding:

### Experiment 1: Chunk Size Impact
- Run the ingestion with chunk_size = 100, then 500
- Query the same question with both datasets
- **Question**: How do the results differ? Which gives better context?

### Experiment 2: Query Variations
Try these different queries and compare results:
- "What is Alice's sister's name?"
- "Who was sitting with Alice?"
- "What was Alice's sister doing?"
- **Question**: Do more specific queries work better?

### Experiment 3: Similarity Thresholds
- Look at the similarity scores in your results
- **Question**: What similarity score seems to indicate relevant vs irrelevant results?

## Expected Results

You should find text similar to:
> "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do..."

The sister's name is not explicitly mentioned in the first paragraph, but this demonstrates how vector search can find contextually relevant passages even when exact terms don't match.

## Troubleshooting

### If the database connection fails:
```bash
# Check if Docker is running
docker ps

# Restart services if needed
cd ../../environment
docker compose restart
```

### If embeddings seem wrong:
```bash
# Check if Ollama model is loaded
docker exec ollama-service ollama list
```

### If no results are found:
```sql
-- Check if data was inserted
SELECT COUNT(*) FROM docs WHERE pdf_id = 'alice_in_wonderland';
```

## Success Criteria

You've completed the lab when you can:
1. ✅ Successfully ingest the Alice PDF into chunks
2. ✅ Query for Alice's sister and get relevant results
3. ✅ Understand how chunk size affects result quality
4. ✅ Explain why vector similarity found the relevant passage

## Bonus: Adapt to Your Domain

Once you understand the concepts, try adapting this to your own use case:

- **Legal Documents**: Chunk contracts to find relevant clauses
- **Technical Manuals**: Search documentation for troubleshooting steps  
- **Research Papers**: Find related methodologies across papers
- **Customer Support**: Search past tickets for similar issues

The key insight is that **the techniques remain the same**, only the content and domain change! 
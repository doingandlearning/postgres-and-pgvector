# Lab: Generating & Storing Vectors (Non-Python Starter)

## Objective
This lab focuses on understanding **vector embeddings and database storage** without requiring extensive Python programming. You'll use pre-built scripts and configuration-based approaches to learn the core concepts.

## Learning Goals
- Understand how text gets converted to vector embeddings
- Learn how to store embeddings in PostgreSQL with pgvector
- Experiment with different data sources and embedding models
- See how batch processing works for efficiency

## Approach Options

### Option A: Configuration-Based Data Loading (Recommended)

Use a configuration file to specify what data to load and how to process it.

#### Step 1: Configure Your Data Source
**Edit `data_config.json`:**
```json
{
  "data_source": "open_library",
  "categories": ["programming", "ai", "web_development"],
  "books_per_category": 5,
  "database": {
    "host": "localhost",
    "port": "5050",
    "database": "pgvector",
    "user": "postgres",
    "password": "postgres"
  },
  "embedding": {
    "model": "bge-m3",
    "ollama_url": "http://localhost:11434/api/embed"
  }
}
```

#### Step 2: Run the Data Loader
```bash
python load_configured.py
```

This will:
- Fetch books from Open Library API
- Generate embeddings for each book description
- Store everything in your PostgreSQL database

### Option B: SQL-Focused Approach

Use pre-generated data and focus on the SQL/database aspects.

#### Step 1: Load Sample Data
```bash
# Load pre-generated sample data
python load_sample_data.py
```

#### Step 2: Explore with SQL
```sql
-- Connect to your database
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- See what data was loaded
SELECT name, item_data->>'subject' as subject 
FROM items 
LIMIT 10;

-- Check embedding dimensions
SELECT name, array_length(embedding, 1) as embedding_dimension
FROM items 
LIMIT 5;

-- Find books by subject
SELECT name, item_data->>'authors' as authors
FROM items 
WHERE item_data->>'subject' = 'programming';
```

### Option C: Interactive CLI Tool

Use a command-line interface that handles all the complexity.

#### Step 1: Use the CLI
```bash
# Load data from different sources
python book_loader.py --source open_library --categories "ai,programming" --limit 10

# Or load from a CSV file
python book_loader.py --source csv --file sample_books.csv

# Check what's in the database
python book_loader.py --status
```

## Learning Experiments

Try these experiments to understand the concepts better:

### Experiment 1: Different Data Sources
- Load books about "artificial intelligence"
- Load books about "cooking"
- **Question**: Do you think the embeddings will be similar or different? Why?

### Experiment 2: Embedding Dimensions
```sql
-- Check embedding dimensions
SELECT DISTINCT array_length(embedding, 1) as dimension_count
FROM items;
```
- **Question**: Why do all embeddings have the same number of dimensions?

### Experiment 3: Batch vs Individual Processing
- Load 5 books individually
- Load 50 books in batch
- **Question**: Which approach is faster? Why might this matter for real applications?

## Understanding the Process

Even without writing Python, you should understand what's happening:

1. **Text Input**: Book titles, authors, descriptions
2. **API Call**: Send text to Ollama embedding model
3. **Vector Output**: Receive array of numbers (embeddings)
4. **Database Storage**: Store text + vector in PostgreSQL
5. **Indexing**: PostgreSQL can now search by similarity

## Verification Steps

Check your understanding with these queries:

### 1. Count Your Data
```sql
SELECT COUNT(*) as total_books FROM items;
```

### 2. Sample the Data
```sql
SELECT 
  name,
  item_data->>'subject' as subject,
  item_data->>'authors' as authors,
  embedding[1:5] as first_5_dimensions
FROM items 
LIMIT 3;
```

### 3. Find Similar Books (Preview)
```sql
-- Find books similar to a specific one
SELECT 
  name,
  embedding <=> (
    SELECT embedding 
    FROM items 
    WHERE name LIKE '%Python%' 
    LIMIT 1
  ) as similarity
FROM items
ORDER BY similarity
LIMIT 5;
```

## Troubleshooting

### If the API calls fail:
```bash
# Check if Ollama is running
docker ps | grep ollama

# Check if the model is loaded
docker exec ollama-service ollama list
```

### If database connections fail:
```bash
# Check PostgreSQL
docker ps | grep postgres

# Test connection
docker exec -it pgvector-db psql -U postgres -d pgvector -c "SELECT 1;"
```

### If no data appears:
```sql
-- Check if table exists
\dt

-- Check table structure
\d items
```

## Success Criteria

You've completed the lab when you can:
1. ✅ Successfully load book data from an external API
2. ✅ Generate embeddings for text descriptions
3. ✅ Store both text and vectors in PostgreSQL
4. ✅ Understand the relationship between text and its embedding
5. ✅ Explain why we need vector databases for AI applications

## Real-World Applications

Think about how this applies to your domain:

- **E-commerce**: Product descriptions → recommendations
- **Documentation**: Help articles → smart search
- **Legal**: Contract clauses → similar case finding
- **Research**: Paper abstracts → related work discovery
- **Customer Support**: Ticket descriptions → solution suggestions

The key insight: **Any text can become a vector, and similar text produces similar vectors!**

## Next Steps

Once you understand this foundation:
1. You can chunk longer documents (next lab)
2. You can query for similar content (upcoming labs)
3. You can build AI-powered search applications

The techniques remain the same regardless of your specific domain or data source. 
# Lab: Querying LLMs with Retrieved Data (Non-Python Starter)

## Objective
This lab focuses on understanding **Retrieval Augmented Generation (RAG)** concepts without requiring extensive Python programming. You'll learn how to enhance LLM responses with relevant context retrieved from vector databases.

## Learning Goals
- Understand the RAG (Retrieval Augmented Generation) pattern
- Learn how to structure data for LLM consumption
- Experiment with different prompt engineering techniques
- Compare LLM responses with and without context
- Understand the impact of different LLM parameters
- Build intuition for when RAG works well vs poorly

## Prerequisites

### 1. Database Setup
Make sure you have data loaded in your database. If not, run one of these first:
```bash
# Option 1: From previous lab
cd ../../../03-generating-and-storing/lab/non-python-starter
python load_configured.py

# Option 2: Quick sample data
cd ../../../03-generating-and-storing/lab/non-python-starter  
python load_sample_data.py
```

### 2. OpenAI API Key Setup
You'll need an OpenAI API key to use ChatGPT for generating responses.

**Option A: Environment Variable (Recommended)**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Option B: .env File**
Create a `.env` file in this directory:
```
OPENAI_API_KEY=your-api-key-here
```

**Option C: System Environment**
Add to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
export OPENAI_API_KEY="your-api-key-here"
```


## RAG Overview

**RAG (Retrieval Augmented Generation)** combines:
1. **Retrieval**: Find relevant information from your database
2. **Augmentation**: Structure the retrieved data as context
3. **Generation**: Use an LLM to generate responses with this context

This approach helps LLMs provide more accurate, up-to-date, and domain-specific responses.

## Approach Options

### Option A: SQL + Manual Prompt Building (Recommended for Non-Python Users)

Build RAG systems using SQL queries and manual prompt construction.

#### Step 1: Retrieve Relevant Context with SQL
```sql
-- Connect to your database first
-- docker exec -it pgvector-db psql -U postgres -d pgvector

-- Find books similar to a user query about "machine learning"
-- (You would normally generate an embedding for "machine learning" first)
WITH user_query AS (
  SELECT embedding FROM items WHERE name ILIKE '%machine learning%' LIMIT 1
)
SELECT 
  name,
  item_data->>'subject' as subject,
  item_data->>'authors' as authors,
  ROUND((embedding <=> (SELECT embedding FROM user_query))::numeric, 4) as similarity
FROM items
WHERE embedding <=> (SELECT embedding FROM user_query) < 0.7
ORDER BY similarity ASC
LIMIT 5;
```

#### Step 2: Structure Data for LLM Context
Take the SQL results and format them into a structured prompt, for example:

```
User Question: What are the best books for learning machine learning?

Relevant Books from Database:
- "Machine Learning Fundamentals" by John Smith (Subject: ai, Similarity: 0.12)
- "Python for Data Science" by Jane Doe (Subject: programming, Similarity: 0.34)
- "Deep Learning Basics" by Mike Johnson (Subject: ai, Similarity: 0.45)
- "Statistical Methods" by Sarah Wilson (Subject: mathematics, Similarity: 0.52)
- "Neural Networks Guide" by Tom Brown (Subject: ai, Similarity: 0.61)

Please provide a structured recommendation categorizing these books by difficulty level (beginner, intermediate, advanced) and explain why each book would be useful for learning machine learning.
```

### Option B: Interactive RAG Assistant

Use a helper script that automates the RAG pipeline for you using ChatGPT.

#### Step 1: Generate RAG Responses
```bash
python rag_assistant.py --query "What are the best books for web development?" --context-limit 5
```

#### Step 2: Compare Different Approaches
```bash
# Without context (just ChatGPT)
python rag_assistant.py --query "Recommend AI books" --no-context

# With context (RAG with ChatGPT)
python rag_assistant.py --query "Recommend AI books" --context-limit 5

# With filtered context
python rag_assistant.py --query "Recommend AI books" --subject ai --context-limit 3

# Different creativity levels
python rag_assistant.py --query "Explain machine learning" --temperature 0.2  # More focused
python rag_assistant.py --query "Explain machine learning" --temperature 0.8  # More creative
```

### Option C: Configuration-Based RAG

Use JSON configuration to define different RAG scenarios.

#### Step 1: Configure RAG Scenarios
**Edit `rag_config.json`:**
```json
{
  "scenarios": [
    {
      "name": "Book Recommendations",
      "query": "What are the best programming books for beginners?",
      "context_limit": 5,
      "filter_subject": "programming",
      "llm_temperature": 0.7,
      "prompt_template": "beginner_recommendations"
    },
    {
      "name": "Technical Deep Dive",
      "query": "Explain advanced machine learning concepts",
      "context_limit": 3,
      "filter_subject": "ai",
      "llm_temperature": 0.3,
      "prompt_template": "technical_explanation"
    }
  ]
}
```

#### Step 2: Run Configured Scenarios
```bash
python run_rag_scenarios.py
```

## Understanding RAG Components

### Component 1: Retrieval Quality
The quality of your RAG system depends heavily on retrieving the right context.

**Test different retrieval strategies:**

```sql
-- Strategy 1: Pure similarity
SELECT name, embedding <=> '[your_query_embedding]' as similarity
FROM items ORDER BY similarity LIMIT 5;

-- Strategy 2: Subject-filtered similarity
SELECT name, embedding <=> '[your_query_embedding]' as similarity
FROM items 
WHERE item_data->>'subject' = 'programming'
ORDER BY similarity LIMIT 5;

-- Strategy 3: Hybrid (text + vector)
SELECT name, 
       CASE WHEN name ILIKE '%python%' THEN 0.1 ELSE 0.5 END + 
       (embedding <=> '[your_query_embedding]') as combined_score
FROM items 
ORDER BY combined_score LIMIT 5;
```

**Question**: Which strategy gives you the most relevant results for different types of queries?

### Component 2: Context Structuring
How you format retrieved data affects LLM performance.

**Template A: Simple List**
```
Books found:
- Book 1
- Book 2  
- Book 3

Question: [user question]
```

**Template B: Structured Context**
```
Context: Based on similarity search, here are relevant books:

1. "Book Title" by Author Name
   - Subject: programming
   - Relevance: High (similarity: 0.12)

2. "Another Book" by Another Author
   - Subject: web development  
   - Relevance: Medium (similarity: 0.34)

User Question: [user question]

Please provide recommendations based on this context.
```

**Template C: Role-Based Context**
```
You are a librarian with expertise in technical books. 

A user is asking: "[user question]"

Your available books include:
[formatted book list]

Provide personalized recommendations based on the user's question and explain your reasoning.
```

**Question**: Which template produces better LLM responses for your use cases?

### Component 3: LLM Parameter Tuning
Different parameters affect response quality.

**Temperature Comparison (ChatGPT):**
- **Low (0.1-0.3)**: Focused, consistent, factual responses - great for technical explanations
- **Medium (0.4-0.7)**: Balanced creativity and accuracy - good for recommendations  
- **High (0.8-1.0)**: Creative, varied, but potentially less accurate - useful for brainstorming

**Max Tokens Impact:**
- **Short (50-100)**: Concise summaries
- **Medium (200-400)**: Detailed explanations
- **Long (500+)**: Comprehensive analysis

## Experiments and Learning Activities

### Experiment 1: Context vs No Context
Compare LLM responses with and without retrieved context.

**Without Context:**
```
Query: "What programming books should I read?"
ChatGPT Response: [Generic programming book recommendations from training data]
```

**With Context (RAG):**
```
Query: "What programming books should I read?"
Context: [5 specific books from your database]
ChatGPT Response: [Specific recommendations based on your actual data]
```

**Question**: How do the responses differ in specificity and relevance?

### Experiment 2: Context Quality Impact
Test how different amounts and quality of context affect responses.

```sql
-- High quality context (very similar books)
SELECT name FROM items 
WHERE embedding <=> '[query_embedding]' < 0.3
ORDER BY similarity LIMIT 3;

-- Lower quality context (less similar books)  
SELECT name FROM items
WHERE embedding <=> '[query_embedding]' BETWEEN 0.5 AND 0.8
ORDER BY similarity LIMIT 3;
```

**Question**: Does more context always lead to better responses?

### Experiment 3: Prompt Engineering
Test different ways of structuring the same information.

**Approach A: Direct Question**
```
Books: [list]
Question: Which book is best for beginners?
```

**Approach B: Role Playing**
```
You are an expert teacher. A student asks which book is best for beginners.
Available books: [list]
Provide educational guidance.
```

**Approach C: Structured Output**
```
Books: [list]
Question: Which book is best for beginners?
Format your response as:
1. Recommendation: [book name]
2. Reasoning: [why this book]
3. Alternatives: [other options]
```

**Question**: Which approach gives you the most useful responses?

### Experiment 4: Domain Adaptation
Test how RAG performs across different domains.

```bash
# Technical domain
python rag_assistant.py --query "Explain neural networks" --subject ai

# Creative domain  
python rag_assistant.py --query "Recommend fiction books" --subject literature

# Business domain
python rag_assistant.py --query "Books on management" --subject business
```

**Question**: Does RAG work equally well across all domains in your dataset?

## Advanced RAG Patterns

### Pattern 1: Multi-Step RAG
1. Initial query retrieves broad context
2. Follow-up query focuses on specific aspect
3. Final response combines both contexts

### Pattern 2: Conversational RAG
1. Maintain conversation history
2. Retrieve context relevant to entire conversation
3. Generate responses that build on previous exchanges

### Pattern 3: Fact-Checking RAG
1. Generate initial response
2. Retrieve context to verify claims
3. Revise response based on verification

### Pattern 4: Hybrid RAG
1. Combine multiple retrieval strategies
2. Use different LLMs for different tasks
3. Post-process responses for consistency

## Common RAG Challenges and Solutions

### Challenge 1: Irrelevant Context
**Problem**: Retrieved context doesn't match user intent
**Solutions**:
- Improve query understanding
- Use hybrid retrieval (text + vector)
- Filter by metadata (subject, date, etc.)

### Challenge 2: Context Overload
**Problem**: Too much context confuses the LLM
**Solutions**:
- Limit context to most relevant items
- Summarize context before sending to LLM
- Use hierarchical context (overview + details)

### Challenge 3: Inconsistent Responses
**Problem**: Same query produces different responses
**Solutions**:
- Lower temperature for consistency
- Use system prompts to enforce style
- Post-process responses for standardization

### Challenge 4: Outdated Information
**Problem**: Context contains old or incorrect information
**Solutions**:
- Regular data updates
- Timestamp-based filtering
- Source credibility weighting

## Real-World RAG Applications

### Customer Support
- **Retrieval**: Find similar support tickets and solutions
- **Augmentation**: Structure ticket history and knowledge base articles
- **Generation**: Provide personalized support responses

### Content Creation
- **Retrieval**: Find relevant research papers and sources
- **Augmentation**: Organize sources by topic and credibility
- **Generation**: Create well-researched content with citations

### Educational Tutoring
- **Retrieval**: Find relevant learning materials and examples
- **Augmentation**: Structure by difficulty level and learning style
- **Generation**: Provide personalized explanations and exercises

### Business Intelligence
- **Retrieval**: Find relevant reports and data points
- **Augmentation**: Structure by business context and metrics
- **Generation**: Create executive summaries and recommendations

## Evaluation and Metrics

### Retrieval Quality Metrics
- **Precision**: How many retrieved items are relevant?
- **Recall**: How many relevant items were retrieved?
- **Diversity**: How varied are the retrieved items?

### Generation Quality Metrics
- **Relevance**: Does the response address the query?
- **Accuracy**: Is the information factually correct?
- **Completeness**: Does the response cover all important aspects?
- **Coherence**: Is the response well-structured and logical?

### User Experience Metrics
- **Response Time**: How quickly does the system respond?
- **User Satisfaction**: Do users find responses helpful?
- **Task Completion**: Can users accomplish their goals?

## Success Criteria

You've completed the lab when you can:
1. ✅ Understand the RAG pipeline (Retrieve → Augment → Generate)
2. ✅ Structure database results for effective LLM consumption
3. ✅ Compare responses with and without context
4. ✅ Experiment with different prompt engineering techniques
5. ✅ Identify when RAG helps vs hurts response quality
6. ✅ Apply RAG patterns to your own domain and use cases

## Next Steps

Once you understand these concepts:
1. Try RAG with your own domain-specific data
2. Experiment with different LLM models and parameters
3. Build evaluation frameworks for your RAG systems
4. Explore advanced patterns like conversational RAG
5. Consider production deployment challenges (latency, cost, scaling)

## Key Insights

After completing this lab, you should understand:

1. **RAG bridges the gap** between static LLM training and dynamic, current information
2. **Context quality matters more than quantity** - relevant context beats more context
3. **Prompt engineering is crucial** - how you structure context affects response quality
4. **Different domains require different approaches** - one size doesn't fit all
5. **Evaluation is essential** - you need metrics to improve your RAG system
6. **RAG is not magic** - it requires careful engineering and tuning

## Troubleshooting

### Common Issues and Solutions

#### "OPENAI_API_KEY environment variable not set"
- Make sure you've set your API key as described in Prerequisites
- Restart your terminal after setting environment variables
- Check that the API key is valid and has sufficient credits

#### "OpenAI API Error: 401"
- Your API key is invalid or expired
- Double-check the API key value
- Ensure there are no extra spaces or characters

#### "OpenAI API Error: 429"
- You've hit rate limits or quota limits
- Wait a few minutes and try again
- Check your OpenAI account usage and billing

#### "OpenAI API Error: 400"
- Usually a malformed request
- Try reducing the context size with `--context-limit 3`
- Check that your query isn't too long

#### Slow responses
- ChatGPT API calls take 2-10 seconds depending on response length
- Use `--temperature 0.1` for faster, more focused responses
- Reduce `max_tokens` in the config for shorter responses

#### Database connection issues
- Make sure your PostgreSQL container is running
- Check that you have data loaded (see Prerequisites)
- Verify database connection settings in `rag_config.json`

## Cost Considerations

- **gpt-4o-mini** is very cost-effective (~$0.15 per 1M input tokens)
- Each query typically uses 200-1000 tokens depending on context size
- 1000 queries ≈ $0.50-2.00 in API costs
- Monitor usage at https://platform.openai.com/usage

## Alternative Models

You can change the model in `rag_config.json`:
- **gpt-4o-mini**: Fast, cost-effective, good quality (recommended)
- **gpt-4o**: Higher quality, more expensive
- **gpt-3.5-turbo**: Cheaper but lower quality

Remember: **These RAG concepts apply to any LLM and vector database combination!** 
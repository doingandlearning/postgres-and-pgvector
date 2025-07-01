# Flask Backend for PDF Query System

This Flask server provides API endpoints to query documents using vector similarity search and OpenAI LLM enhancement.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file contains:
```
OPENAI_API_KEY=your_openai_api_key_here
```

3. Ensure PostgreSQL with pgvector is running and the database is populated with document chunks.

## Running the Server

```bash
python app.py
```

The server will run on `http://localhost:5100`

## API Endpoints

### Health Check
- **GET** `/health`
- Returns server status

**Response:**
```json
{
  "status": "healthy",
  "message": "Server is running"
}
```

### Query with LLM Enhancement
- **POST** `/query`
- Searches for similar chunks and returns an AI-generated response

**Request:**
```json
{
  "query": "What are the frequency allocations for VHF FM broadcasting?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What are the frequency allocations for VHF FM broadcasting?",
  "answer": "AI-generated response based on relevant chunks...",
  "chunks": [
    {
      "id": "chunk-uuid",
      "page": 15,
      "text": "Relevant text chunk...",
      "similarity_score": 0.8421,
      "metadata": {
        "chunk_length": 245,
        "type": "rule_or_definition"
      }
    }
  ],
  "chunk_count": 5
}
```

### Search Chunks Only
- **POST** `/search`
- Returns similar chunks without LLM enhancement

**Request:**
```json
{
  "query": "frequency allocation",
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "frequency allocation",
  "chunks": [
    {
      "id": "chunk-uuid",
      "page": 15,
      "text": "Full text of the chunk...",
      "similarity_score": 0.8421,
      "metadata": {
        "chunk_length": 245,
        "type": "rule_or_definition"
      }
    }
  ],
  "chunk_count": 3
}
```

## Testing with curl

### Health check:
```bash
curl http://localhost:5000/health
```

### Query with LLM:
```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the frequency allocations?"}'
```

### Search chunks only:
```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "frequency allocation", "top_k": 3}'
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400` - Bad Request (missing or invalid query)
- `500` - Internal Server Error (database connection issues, etc.)

All error responses include an `error` field with a descriptive message. 
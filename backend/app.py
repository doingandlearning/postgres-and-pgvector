import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add the z-possible-final-workflow directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'z-possible-final-workflow'))

# Import functions from the existing query processing file
from utils import get_db_connection, get_embedding
import dotenv
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load environment variables
dotenv.load_dotenv()

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = dotenv.get_key(dotenv.find_dotenv(), "OPENAI_API_KEY", None) 

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def fetch_similar_chunks(user_embedding, top_k=5):
    """Query the docs table for similar chunks based on vector similarity."""
    query = """
        SELECT id, text, embedding <=> %s::vector AS distance, page, metadata
        FROM docs
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_embedding, user_embedding, top_k))
            results = cur.fetchall()
    return results

def enhance_with_openai(chunks, user_query=None):
    """Send retrieved chunks to OpenAI LLM for enhancement."""
    
    if len(chunks) == 0:
        return "No relevant chunks found."

    # Prepare the context from the chunks
    context = []
    for chunk in chunks:
        chunk_id, text, distance, page, metadata = chunk
        context.append({
            "id": str(chunk_id),
            "text": text,
            "distance": distance,
            "page": page,
            "metadata": metadata
        })

    # OpenAI prompt for the Geneva 1984 Regional Agreement
    prompt = f"""
You are an expert on the Geneva 1984 Regional Agreement for VHF FM Broadcasting.

Using just the context below, answer the user's question precisely and cite any relevant Article or Annex number.

<context>
{    "\n".join(
        [f"Page {chunk['page']}: {chunk['text']}" for chunk in context]
    )}
</context>

<question>
{user_query if user_query else 'No specific query provided'}
</question>

Answer:
    """

    # Payload for OpenAI request
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a chatbot based in the ITU. You are an expert in communication technologies"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    # Send request to OpenAI API
    response = requests.post(OPENAI_URL, headers=HEADERS, json=payload)

    # Parse response
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Server is running"})

@app.route('/query', methods=['POST'])
def process_query():
    """Main endpoint to process user queries."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Invalid request. Please provide a 'query' field."
            }), 400
        
        user_query = data['query']
        top_k = data.get('top_k', 5)  # Default to 5 similar chunks
        
        # Generate embedding for user query
        user_embedding = get_embedding(user_query)
        
        # Fetch similar chunks
        similar_chunks = fetch_similar_chunks(user_embedding, top_k)
        
        if not similar_chunks:
            return jsonify({
                "query": user_query,
                "answer": "No relevant information found in the database.",
                "chunks": [],
                "chunk_count": 0
            })
        
        # Get LLM response
        llm_response = enhance_with_openai(similar_chunks, user_query)
        
        # Structure the response with chunk details
        chunk_details = []
        for chunk in similar_chunks:
            chunk_id, text, distance, page, metadata = chunk
            chunk_details.append({
                "id": str(chunk_id),
                "page": page,
                "text": text[:200] + "..." if len(text) > 200 else text,  # Truncate for API response
                "similarity_score": round(1 - distance, 4),  # Convert distance to similarity
                "metadata": metadata
            })
        
        return jsonify({
            "query": user_query,
            "answer": llm_response,
            "chunks": chunk_details,
            "chunk_count": len(similar_chunks)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"An error occurred: {str(e)}"
        }), 500

@app.route('/search', methods=['POST'])
def search_chunks():
    """Endpoint to search for similar chunks without LLM enhancement."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Invalid request. Please provide a 'query' field."
            }), 400
        
        user_query = data['query']
        top_k = data.get('top_k', 5)
        
        # Generate embedding for user query
        user_embedding = get_embedding(user_query)
        
        # Fetch similar chunks
        similar_chunks = fetch_similar_chunks(user_embedding, top_k)
        
        # Structure the response
        chunk_details = []
        for chunk in similar_chunks:
            chunk_id, text, distance, page, metadata = chunk
            chunk_details.append({
                "id": str(chunk_id),
                "page": page,
                "text": text,
                "similarity_score": round(1 - distance, 4),
                "metadata": metadata
            })
        
        return jsonify({
            "query": user_query,
            "chunks": chunk_details,
            "chunk_count": len(similar_chunks)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"An error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5100) 
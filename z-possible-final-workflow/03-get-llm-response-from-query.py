# Accept the user query
# Vector similarity search with the user query
# Get the LLM response based on the query and the similar chunks
from utils import get_db_connection, get_embedding

# The schema.sql file defines the docs table with the following columns:
  # docs (
  #   id UUID PRIMARY KEY,
  #   pdf_id TEXT,
  #   page INTEGER,
  #   text TEXT,
  #   embedding VECTOR(1024)
  # ); 

def get_user_input():
    return input("Enter your query: ")

def fetch_similar_chunks(user_embedding, top_k=5):
  # Query the docs table as per schema.sql
  query = """
    SELECT id, text, embedding <=> %s::vector AS distance, page
    FROM docs
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
  """
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute(query, (user_embedding, user_embedding, top_k))
      results = cur.fetchall()
  print(f"inside the fetch_similar_chunks function: {results}")
  return results

import dotenv
import requests
dotenv.load_dotenv()

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = dotenv.get_key(dotenv.find_dotenv(), "OPENAI_API_KEY", None) 

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# Query OpenAI to answer the user query based on the similar chunks
def enhance_with_openai(chunks, user_query=None):
    """Send retrieved book data to OpenAI LLM for enhancement."""

    if len(chunks) == 0:
        return "No relevant chunks found."

    # Prepare the context from the chunks
    context = []
    for chunk in chunks:
        chunk_id, text, distance, page = chunk
        context.append({
            "id": str(chunk_id),
            "text": text,
            "distance": distance,
            "page": page
        })

    # OpenAI prompt - prompt engineering is a practice of crafting effective prompts
    # to get the best results from LLMs. Here we ask the model to summarize
    # the list of books and recommend the best ones for different skill levels.
    # This is a simple example of prompt engineering.
    # You can modify the prompt to suit your needs.
    prompt = f"""
You are an expert on the Geneva 1984 Regional Agreement for VHF FM Broadcasting.

Using just the context below, answer the user’s question precisely and cite any relevant Article or Annex number.

<context>
{    "\n".join(
        [f"Article {chunk['page']}: {chunk['text']}" for chunk in context]
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

def main():
    user_query = get_user_input()
    user_embedding = get_embedding(user_query)
    print("User Query Embedding:", user_embedding)
    similar_chunks = fetch_similar_chunks(user_embedding, 1)
    print(f"Similar Chunks Found: {similar_chunks}")
    if not similar_chunks:
        print("No similar chunks found.")
        return
    llm_response = enhance_with_openai(similar_chunks, user_query)
    print("LLM Response:")
    print(llm_response)

if __name__ == "__main__":
    main()
    

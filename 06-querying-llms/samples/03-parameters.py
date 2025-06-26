import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Key (Replace with actual key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI API endpoint
url = "https://api.openai.com/v1/chat/completions"

# Request headers
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def query_openai(prompt, temperature, top_p):
    """Send a query to OpenAI with adjustable temperature and top_p parameters."""
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a knowledgeable assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 100
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"

# Test different parameter settings
prompt = "Tell me an interesting fact about space."

print("\n🔹 Temperature = 0.0, Top-p = 0.5 (Factual Response)")
print(query_openai(prompt, temperature=0.0, top_p=0.5))

print("\n🔹 Temperature = 0.9, Top-p = 1.0 (Creative Response)")
print(query_openai(prompt, temperature=0.9, top_p=1.0))

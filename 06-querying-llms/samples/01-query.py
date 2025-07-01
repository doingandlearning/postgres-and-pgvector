import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI API endpoint
url = "https://api.openai.com/v1/chat/completions"

# Request headers
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# Request payload
payload = {
    "model": "gpt-4.1-mini-2025-04-14",
    "messages": [ # System message to set the context - this is important for the model to understand its role
        {"role": "system", "content": "You are a helpful assistant. You are knowledgeable about vector databases and their applications. You are coach and trainer for developers."},
        {"role": "user", "content": input("Enter your query: ")}  # User input for the query
    ],
    "temperature": 0.7,
    "max_tokens": 150
}

# Send the request
response = requests.post(url, headers=headers, data=json.dumps(payload))  # json=payload can also be used here, but data=json.dumps(payload) is more explicit

# Print the response
if response.status_code == 200:  # or response.ok -> works for other 2xx codes
    data = response.json()
    print(data)
    print(data["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}, {response.text}")

import os
import requests
import json
import psycopg
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Configuration
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

def enhance_with_openai(tickets, user_issue):
    """Send retrieved support tickets to OpenAI to generate a structured response."""

    if not tickets or isinstance(tickets, str):
        return f"LLM skipped: {tickets}"

    ticket_text = "\n".join(
        [f"- {ticket['issue_description']} (Resolution: {ticket['resolution_steps']})" for ticket in tickets]
    )

    prompt = f"""
    A customer support agent received this issue:
    "{user_issue}"

    Here are similar past tickets:
    {ticket_text}

    Generate a structured response summarizing the best resolution steps.
    """

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a customer support assistant providing clear troubleshooting steps."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    response = requests.post(OPENAI_URL, headers=HEADERS, data=json.dumps(payload))
    return response.json()["choices"][0]["message"]["content"]

# Example Usage
if __name__ == "__main__":
    from search_tickets import find_similar_tickets

    user_query = "User cannot log in due to authentication failure."
    tickets = find_similar_tickets(user_query)
    enhanced_response = enhance_with_openai(tickets, user_query)
    
    print("\n🔹 **Enhanced LLM Response:**")
    print(enhanced_response)

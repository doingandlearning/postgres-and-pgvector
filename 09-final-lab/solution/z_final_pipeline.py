import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from search_tickets import find_similar_tickets
from enhance_response import enhance_with_openai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    """Search for similar tickets and enhance response with LLM."""
    data = request.json
    user_issue = data.get("query", "")
    top_n = data.get("top_n", 5)

    if not user_issue:
        return jsonify({"error": "Query cannot be empty"}), 400

    tickets = find_similar_tickets(user_issue, top_n)
    enhanced_response = enhance_with_openai(tickets, user_issue)

    return jsonify({
        "query": user_issue,
        "similar_tickets": tickets,
        "enhanced_response": enhanced_response
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)

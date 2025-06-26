from step1 import get_embedding_ollama
from step2 import search_similar_books

def format_books_for_prompt(books):
    """Format book data for use in LLM queries."""
    book_text = "\n".join(
        [
            f"- {book[0]} ({book[1].get('subject', 'Unknown Subject')})"
            for book in books
        ]
    )

    prompt = f"""
    The user asked about books related to artificial intelligence.

    Based on vector search, here are relevant books:
    {book_text}

    Provide a structured summary and categorize these books for beginners, intermediate, and advanced learners.
    """

    return prompt

if __name__ == "__main__":
    # Retrieve relevant books
  user_query = "What are the best books on artificial intelligence?"
  query_embedding = get_embedding_ollama(user_query)
  books = search_similar_books(query_embedding)
  # Generate structured prompt
  structured_prompt = format_books_for_prompt(books)
  print("\n🔹 Structured Prompt for LLM:")
  print(structured_prompt)
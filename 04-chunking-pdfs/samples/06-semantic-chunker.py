import os

import nltk
import PyPDF2
from nltk.tokenize import sent_tokenize

from utils import get_embedding

# Download NLTK's sentence tokenizer models if not already present
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Plain-Python cosine similarity between two vectors, so this sample
    doesn't need numpy as an extra dependency.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def sentences_from_pdf(path, max_sentences=None):
    """
    Extracts text from a PDF and splits it into sentences, tracking which
    page each sentence came from. `max_sentences` caps the amount of text
    processed, since embedding every sentence individually is a lot of
    Ollama round-trips for a live demo.
    """
    reader = PyPDF2.PdfReader(path)

    sentences_with_pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        for sentence in sent_tokenize(text):
            sentence = sentence.strip()
            if sentence:
                sentences_with_pages.append((sentence, i + 1))

        if max_sentences and len(sentences_with_pages) >= max_sentences:
            return sentences_with_pages[:max_sentences]

    return sentences_with_pages


def semantic_chunks(sentences_with_pages, similarity_threshold=0.5, max_chunk_sentences=8):
    """
    Groups consecutive sentences into chunks based on *meaning*, not size.

    Rather than cutting every N words/tokens, this compares the embedding
    of each new sentence to the embedding of the sentence before it. A big
    drop in cosine similarity signals a topic shift, which is where we
    start a new chunk. `max_chunk_sentences` is a safety valve so a very
    "samey" passage doesn't grow into one giant chunk.

    Yields (start_page, chunk_text, break_reason, similarity_score).
    """
    if not sentences_with_pages:
        return

    current_chunk = [sentences_with_pages[0]]
    prev_embedding = get_embedding(sentences_with_pages[0][0])

    for sentence, page in sentences_with_pages[1:]:
        embedding = get_embedding(sentence)
        similarity = cosine_similarity(prev_embedding, embedding)

        topic_shifted = similarity < similarity_threshold
        chunk_full = len(current_chunk) >= max_chunk_sentences

        if topic_shifted or chunk_full:
            chunk_text = " ".join(s for s, _ in current_chunk)
            start_page = current_chunk[0][1]
            reason = "topic shift" if topic_shifted else "max size reached"
            yield (start_page, chunk_text, reason, similarity)
            current_chunk = []

        current_chunk.append((sentence, page))
        prev_embedding = embedding

    if current_chunk:
        chunk_text = " ".join(s for s, _ in current_chunk)
        start_page = current_chunk[0][1]
        yield (start_page, chunk_text, "end of document", None)


if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), "data", "alice.pdf")

    print("This script demonstrates chunking by comparing sentence *meaning*")
    print("(embedding similarity) instead of a fixed word/token count.\n")

    # Capped for a snappy demo -- remove max_sentences to process the whole book.
    sentences = sentences_from_pdf(pdf_path, max_sentences=60)
    print(f"Extracted {len(sentences)} sentences. Comparing meaning between them...\n")

    chunk_count = 0
    for page_num, chunk, reason, similarity in semantic_chunks(sentences):
        chunk_count += 1
        similarity_str = f"{similarity:.3f}" if similarity is not None else "n/a"
        print(f"--- Chunk {chunk_count} (starts page {page_num}, broke on: {reason}, similarity: {similarity_str}) ---")
        print(f"'{chunk[:160]}...'\n")

    print(f"Produced {chunk_count} meaning-based chunks from {len(sentences)} sentences.")
    print("\nCompare this to 01-simple-chunker.py's fixed-size chunks over the same")
    print("text -- notice how chunk boundaries here land on topic changes rather")
    print("than an arbitrary word count.")

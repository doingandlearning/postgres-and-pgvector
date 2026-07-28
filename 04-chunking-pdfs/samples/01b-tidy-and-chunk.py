"""
01b-tidy-and-chunk.py

Takes the raw (word, page_number) output that 01 produces from a scanned
PDF and turns it into clean, chunk-ready text.

Real-world PDF extraction (like the Alice in Wonderland scan) interleaves
running headers, footers, and navigation labels into the word stream on
almost every page - e.g. "Digital Interface by BookVirtual Corp. U.S.
Patent Pending." and "Fit Page Full Screen On/Off Close Book". These
break sentences apart and pollute anything you'd embed.

This script:
    1. Groups the (word, page) tuples by page.
    2. Detects repeated boilerplate phrases automatically (rather than
       hardcoding them) by finding word sequences that recur, verbatim,
       across a suspiciously large fraction of pages - genuine narrative
       text essentially never repeats itself that way.
    3. Strips those phrases out and joins what's left into readable text
       per page.
    4. Splits the cleaned text into fixed-size, overlapping chunks, each
       tagged with its source page number - ready to embed.

Adjust extract_words_with_pages() below if 01 uses a different PDF
library; this assumes pdfplumber's page.extract_words(), which is what
produces (word_text, page_number) pairs in that shape.

Known limitation: this only strips n-grams that repeat *verbatim* across
pages. The last few words of a boilerplate run often butt up against
page-specific content (a page number, a chapter title), so that trailing
fragment never repeats exactly and slips through - e.g. cleaned text may
still start with something like "On/Off Close Book 84 PIG AND PEPPER".
Real scans can also render the same boilerplate two different ways (e.g.
garbled, overlapping characters on some pages) - those variants won't
match each other and won't be caught either. Both are worth pointing out
to students as "why automatic cleanup isn't magic," rather than bugs to
silently fix.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Configuration - tune these for your document and embedding model
# ---------------------------------------------------------------------------

PDF_PATH = Path(__file__).parent / "data" / "alice.pdf"

BOILERPLATE_NGRAM_SIZE = 4          # length of word sequence used to detect repeats
BOILERPLATE_PAGE_THRESHOLD = 0.15   # a sequence repeating on >15% of pages is noise
CHUNK_SIZE_WORDS = 150
CHUNK_OVERLAP_WORDS = 30


# ---------------------------------------------------------------------------
# Step 1: extraction (reuses whatever 01 does - swap this if needed)
# ---------------------------------------------------------------------------

def extract_words_with_pages(pdf_path: Path) -> list[tuple[str, int]]:
    """Return [(word, page_number), ...] for every word in the PDF."""
    import pdfplumber

    words_with_pages: list[tuple[str, int]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for word in page.extract_words():
                words_with_pages.append((word["text"], page_number))
    return words_with_pages


# ---------------------------------------------------------------------------
# Step 2: group by page
# ---------------------------------------------------------------------------

def group_words_by_page(
    words_with_pages: Iterable[tuple[str, int]]
) -> dict[int, list[str]]:
    pages: dict[int, list[str]] = {}
    for word, page_number in words_with_pages:
        pages.setdefault(page_number, []).append(word)
    return pages


# ---------------------------------------------------------------------------
# Step 3: detect and strip repeated boilerplate
# ---------------------------------------------------------------------------

def find_boilerplate_ngrams(
    pages: dict[int, list[str]],
    ngram_size: int = BOILERPLATE_NGRAM_SIZE,
    page_threshold: float = BOILERPLATE_PAGE_THRESHOLD,
) -> set[tuple[str, ...]]:
    """
    Find word n-grams that appear, verbatim, on an unusually large share
    of pages. Real prose essentially never repeats a 4-word sequence
    across many different pages - running headers, footers, and nav
    labels do.
    """
    ngram_page_counts: Counter[tuple[str, ...]] = Counter()
    for page_number, words in pages.items():
        seen_this_page: set[tuple[str, ...]] = set()
        for i in range(len(words) - ngram_size + 1):
            ngram = tuple(words[i : i + ngram_size])
            seen_this_page.add(ngram)
        # count each ngram once per page, not once per occurrence
        for ngram in seen_this_page:
            ngram_page_counts[ngram] += 1

    total_pages = len(pages)
    threshold_count = max(2, int(total_pages * page_threshold))
    return {
        ngram
        for ngram, page_count in ngram_page_counts.items()
        if page_count >= threshold_count
    }


def strip_boilerplate(
    words: list[str], boilerplate_ngrams: set[tuple[str, ...]], ngram_size: int
) -> list[str]:
    """Remove every occurrence of any boilerplate n-gram from a word list."""
    result: list[str] = []
    i = 0
    while i < len(words):
        window = tuple(words[i : i + ngram_size])
        if window in boilerplate_ngrams:
            i += ngram_size  # skip the whole matched phrase
        else:
            result.append(words[i])
            i += 1
    return result


# ---------------------------------------------------------------------------
# Step 4: join into readable text
# ---------------------------------------------------------------------------

_NO_SPACE_BEFORE = {".", ",", ";", ":", "!", "?", "'s", "'", ")", "”"}
_NO_SPACE_AFTER = {"(", "“"}


def join_words(words: list[str]) -> str:
    """Join extracted words back into readable-ish text, fixing common
    spacing artefacts around punctuation."""
    pieces: list[str] = []
    for word in words:
        if pieces and (word in _NO_SPACE_BEFORE or pieces[-1] in _NO_SPACE_AFTER):
            pieces[-1] = pieces[-1] + word
        else:
            pieces.append(word)
    text = " ".join(pieces)
    # collapse any accidental double spaces left over
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Step 5: chunk for embedding
# ---------------------------------------------------------------------------

def chunk_page_words(
    words: list[str],
    page_number: int,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS,
) -> list[dict]:
    """Split one page's cleaned words into overlapping chunks."""
    if not words:
        return []

    chunks: list[dict] = []
    start = 0
    chunk_index = 0
    step = max(1, chunk_size - overlap)

    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(
            {
                "text": join_words(chunk_words),
                "page": page_number,
                "chunk_index": chunk_index,
            }
        )
        chunk_index += 1
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def build_chunks(pdf_path: Path) -> list[dict]:
    words_with_pages = extract_words_with_pages(pdf_path)
    pages = group_words_by_page(words_with_pages)

    boilerplate = find_boilerplate_ngrams(pages)
    print(f"Detected {len(boilerplate)} boilerplate phrase(s):")
    for ngram in sorted(boilerplate, key=lambda g: -len(" ".join(g))):
        print("  -", " ".join(ngram))

    all_chunks: list[dict] = []
    for page_number in sorted(pages):
        cleaned_words = strip_boilerplate(
            pages[page_number], boilerplate, BOILERPLATE_NGRAM_SIZE
        )
        all_chunks.extend(chunk_page_words(cleaned_words, page_number))

    return all_chunks


if __name__ == "__main__":
    chunks = build_chunks(PDF_PATH)

    print(f"\nProduced {len(chunks)} chunks from {PDF_PATH.name}\n")
    for chunk in chunks[:10]:
        print(f"[page {chunk['page']}, chunk {chunk['chunk_index']}]")
        print(chunk["text"])
        print("-" * 60)

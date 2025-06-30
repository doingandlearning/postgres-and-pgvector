import re

text = r"""
This is inline math $E = mc^2$.

And this is display math:
\[
\alpha = \frac{a + b}{c}
\]
"""


def chunk_by_headings(text: str):
    """
    Splits text into chunks based on headings.
    Assumes headings are ALL CAPS on their own lines.
    """

    # Split into sections
    sections = re.split(r"\n([A-Z0-9 \-\.]+)\n", text)



    chunks = []
    for i in range(1, len(sections), 2):
        heading = sections[i].strip()
        body = sections[i + 1].strip()
        chunk = f"{heading}\n{body}"
        chunks.append(chunk)

    return chunks


if __name__ == "__main__":
    text = """
INTRODUCTION
This is the introduction text.

METHODS
These are the methods.

RESULTS
These are the results.
"""

    chunks = chunk_by_headings(text)

    for idx, chunk in enumerate(chunks, 1):
        print(f"---- Chunk {idx} ----")
        print(chunk)
        print()

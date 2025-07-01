import pdfplumber
import re
from uuid import uuid4
import os
from utils import get_db_connection, get_embedding


# ---------- CONFIG ----------

LEGAL_CLAUSE_SPLITTERS = [
    r"Provided however",
    r"Except as",
    r"Notwithstanding",
]

# Dummy embedding generator
def embed_text(text):
    return [len(text) % 10] * 5

# ---------- GRAPHICS DETECTION ----------

def page_has_diagram(page, threshold=20, area_ratio=0.05):
    """
    Heuristic to guess if a page contains diagrams.
    - threshold → minimum number of graphical objects
    - area_ratio → minimum fraction of page area covered by shapes
    """
    num_graphical_objects = (
        len(page.rects) + len(page.curves) + len(page.lines)
    )
    page_area = page.width * page.height
    shape_area = sum(
        rect["width"] * rect["height"]
        for rect in page.rects
    )
    ratio = shape_area / page_area if page_area else 0

    has_bitmap_images = len(page.images) > 0

    if (
        num_graphical_objects > threshold
        or ratio > area_ratio
        or has_bitmap_images
    ):
        return True
    else:
        return False


# ---------- RENDER PAGE IMAGE ----------

def render_page_as_image(page, page_num, output_dir="extracted_pages"):
    """
    Renders an entire PDF page as a PNG image.
    """
    os.makedirs(output_dir, exist_ok=True)

    im = page.to_image(resolution=300)
    image_path = os.path.join(
        output_dir, f"page_{page_num}.png"
    )
    im.save(image_path, format="PNG")

    placeholder = f"{{{{ PAGE_IMAGE_{page_num} }}}}"

    return {
        "type": "page_image",
        "page": page_num,
        "path": image_path,
        "placeholder": placeholder,
    }

# ---------- STEP 1: PARSE PDF ----------

def parse_pdf(path):
    """
    Extracts text, tables, and rendered page images from PDF pages.
    """
    document_objects = []

    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Check if page likely contains a diagram
            if page_has_diagram(page):
                print(f"Page {page_num}: diagram detected, rendering image.")
                page_image_metadata = render_page_as_image(page, page_num)
                document_objects.append(page_image_metadata)
            else:
                print(f"Page {page_num}: no diagram detected.")

            text = page.extract_text() or ""
            tables = page.extract_tables()

            for i, table in enumerate(tables, start=1):
                placeholder = f"{{{{ TABLE_PAGE_{page_num}_{i} }}}}"
                text += f"\n\n{placeholder}"
                document_objects.append({
                    "type": "table",
                    "page": page_num,
                    "content": table,
                    "placeholder": placeholder,
                })

            document_objects.append({
                "type": "text",
                "page": page_num,
                "content": text
            })

    return document_objects

# ---------- STEP 2: REPLACE OBJECTS WITH PLACEHOLDERS ----------

def replace_objects_with_placeholders(text, objects, page_number):
    """
    Ensures tables and page images are replaced by placeholders in text.
    """
    for obj in objects:
        if obj["page"] != page_number:
            continue

        if obj["type"] == "table":
            text = text.replace(str(obj["content"]), obj["placeholder"])
        elif obj["type"] == "page_image":
            if obj["placeholder"] not in text:
                text += f"\n\n{obj['placeholder']}"
    return text

# ---------- STEP 3: CHUNK TEXT ----------

def chunk_text(text, page_number):
    """
    Splits text on:
    - Legal clause signals
    - Paragraph breaks
    """
    for signal in LEGAL_CLAUSE_SPLITTERS:
        text = re.sub(
            f"({signal})",
            r"\n\n### LEGAL_SPLIT_POINT ### \1",
            text,
            flags=re.IGNORECASE
        )

    paragraphs = re.split(r"\n\s*\n", text.strip())

    chunks = []
    current_chunk = []

    for para in paragraphs:
        if para.strip().startswith("### LEGAL_SPLIT_POINT ###"):
            if current_chunk:
                chunks.append({
                    "id": str(uuid4()),
                    "page": page_number,
                    "text": "\n\n".join(current_chunk),
                })
                current_chunk = []
            para = para.replace("### LEGAL_SPLIT_POINT ###", "").strip()
            current_chunk = [para]
        else:
            current_chunk.append(para)

    if current_chunk:
        chunks.append({
            "id": str(uuid4()),
            "page": page_number,
            "text": "\n\n".join(current_chunk),
        })

    return chunks

# ---------- STEP 4: TAG CHUNKS WITH METADATA + EMBED ----------

def process_chunks(chunks):
    """
    Adds embeddings and metadata to each chunk.
    """
    processed = []
    for chunk in chunks:
        embedding = get_embedding(chunk["text"])
        processed.append({
            "id": chunk["id"],
            "page": chunk["page"],
            "text": chunk["text"],
            "embedding": embedding,
            "metadata": {
                "chunk_length": len(chunk["text"]),
                "type": classify_chunk(chunk["text"]),
            }
        })
    return processed



def persist_chunks_to_db(chunks, pdf_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO docs (id, pdf_id, page, text, embedding)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        for chunk in chunks:
            cur.execute(
                insert_query,
                (
                    chunk["id"],
                    pdf_id,
                    chunk["page"],
                    chunk["text"],
                    chunk["embedding"],
                )
            )
    conn.commit()
    conn.close()


def classify_chunk(text):
    if any(signal.lower() in text.lower() for signal in LEGAL_CLAUSE_SPLITTERS):
        return "exception_clause"
    elif "{{ TABLE" in text:
        return "table_reference"
    elif "{{ PAGE_IMAGE" in text:
        return "page_image_reference"
    else:
        return "rule_or_definition"

# ---------- MAIN WORKFLOW ----------

if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), "data", "data.pdf")

    document_objects = parse_pdf(pdf_path)

    all_chunks = []
    for obj in document_objects:
        if obj["type"] == "text":
            clean_text = replace_objects_with_placeholders(
                obj["content"], document_objects, obj["page"]
            )
            chunks = chunk_text(clean_text, obj["page"])
            all_chunks.extend(chunks)

    processed_chunks = process_chunks(all_chunks)
    persist_chunks_to_db(processed_chunks, pdf_id="data.pdf")

    for chunk in processed_chunks:
        print(f"--- Chunk ID: {chunk['id']} ---")
        print(f"Page: {chunk['page']}")
        print(f"Type: {chunk['metadata']['type']}")
        print(f"Length: {chunk['metadata']['chunk_length']} characters")
        print(f"Embedding (first 10 dims): {chunk['embedding'][:10]}")
        print(f"Content preview:\n{chunk['text'][:300]}")
        print()

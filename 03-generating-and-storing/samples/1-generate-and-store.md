# Create a new container for our Python script

- Create the Dockerfile at `scripts/Dockerfile`

```
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/load_data.py .
```

- Create a load_data.py file at `scripts/load_data.py`

```
print("Up and running")
```

- Create a requirements.txt file at the project root

- Update the compose.yml to create a new service that will run this script

# Generate embedding from string

- Test over HTTP
- Create function, restart docker container

```python
def get_embedding(text: str):
    response = requests.post(OLLAMA_URL, json={"model": "bge-m3", "input": text})
    data = response.json()

    return data["embeddings"][0]
```

- Verify that the embeddings match

# Store embedding

- Install psycopg by updating the requirements.txt

```
annotated-types==0.7.0
anyio==4.8.0
certifi==2024.12.14
h11==0.14.0
httpcore==1.0.7
httpx==0.27.2
idna==3.10
ollama==0.4.5
psycopg[binary]==3.2.3
pydantic==2.10.5
pydantic_core==2.27.2
sniffio==1.3.1
typing_extensions==4.12.2
```

- Create a function

```python
def load_data_db():
  sleep(5)
  conn = psycopg.connect(os.getenv("DATABASE_URL"))
  cur = conn.cursor()

  book = {
    "title": "The Great Gatsby",
    "authors": ["F. Scott Fitzgerald"],
    "fist_publish_year": 1925,
    "subject": "Fiction",
  }

  description = (
    f"Book titled '{book['title']}' written by {''.join(book['authors'])}"
    f"Published in {book['fist_publish_year']}."
    f"This is a book about {book['subject']}"
  )

  embedding = get_embedding(description)
  cur.execute(
    """
    INSERT INTO items (name, item_data, embedding)
    VALUES (%s, %s, %s)
    """,
    (book["title"], json.dumps(book), embedding)
  )
  conn.commit()
  cur.close()
  conn.close()
  print("Record added")
```

- Verify the record is there

```bash
docker exec -it pgvector-db psql -U postgres -d pgvector
```

```sql
SELECT * FROM items;
```

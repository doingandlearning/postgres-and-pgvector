### **Quick Lab: Verifying Database and Ollama Setup**

#### **Pre-step: Creating the Docker setup**

We will be building this directory structure up during the course together. Some things to note:

- You'll need to have Docker and Docker Compose installed on your local system. I believe these are tools you use regularly already but if not you can find installation instructions for them here: [Docker Compose](https://docs.docker.com/compose/install/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/). As an aside, I use [Orbstack](https://orbstack.dev/) instead of Docker desktop. They both work the same way but OrbStack is lighter and more memory efficient.

- Docker will need to be running.

- In this directory, you'll run `docker-compose up --build`

- You'll download a PostgreSQL image with pgvector preinstalled and run a schema creation process.

- You'll then be free to run through the lab below. Part of the lab downloads a model to the local Docker container. You'll need to make sure you have enough disc space for this.

- The intention is for everything below this to be the lab for the second section rather than pre-setup. That would mean everyone downloading the model at the same time which might be prohibitive but would give an opportunity to shine a light on the moving parts. 


#### **Step 1: Checking on the Database**

1. **Verify Both Instances Are Running**
   - Use the following command to ensure both `pgvector-db` and `ollama-service` containers are running:
     ```bash
     docker ps
     ```

2. **Connect to the Database**
   - Access the Postgres instance:
     ```bash
     docker exec -it pgvector-db psql -U postgres -d pgvector
     ```

3. **Verify the Table Exists**
   - Inside the `psql` prompt, check for the `items` table:
     ```sql
     \dt
     ```

4. **Verify the Vector Extension**
   - Confirm that the `vector` extension is installed:
     ```sql
     \dx
     ```

---

#### **Step 2: Checking on the Ollama Instance**

1. **Pull the Embedding Model**
   - Download the `bge-m3` model (approximately 1.2GB):
     ```bash
     docker exec -it ollama-service ollama pull bge-m3
     ```

2. **Send a Test Request**
   - Use a tool like `curl` or Postman to test the embedding generation. For `curl`, run:
     ```bash
     curl -X POST http://localhost:11434/api/embed \
          -H "Content-Type: application/json" \
          -d '{
                "model": "bge-m3",
                "input": "Hello world"
              }'
     ```

3. **Verify the Response**
   - You should receive a JSON response containing the embedding for the input text. If there is an error, check the container logs for troubleshooting:
     ```bash
     docker logs ollama-service
     ```

---

#### **Expected Results**
- **Postgres Verification:**
  - The `pgvector-db` container is running.
  - The `items` table and `vector` extension are present.
  
- **Ollama Verification:**
  - The `bge-m3` model is successfully pulled.
  - A valid embedding is returned for the input `"Hello world"`.
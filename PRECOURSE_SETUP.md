# Pre-Course Setup Guide

Welcome! This guide will help you set up your local environment for the course. Following these steps before the first session will ensure you can hit the ground running.

If you run into any issues, please don't hesitate to reach out.

## Prerequisites

You will need the following software installed on your machine:

1.  **Python (3.13 or older)**: The course materials are compatible with Python versions up to 3.13.

    - **To check your version**: `python3 --version`
    - **To install**: Visit the official [Python website](https://www.python.org/downloads/).

2.  **Docker Desktop**: We will use Docker to run a PostgreSQL database (with the `pgvector` extension) and an Ollama server for local embeddings.
    - **To install**: Visit the [Docker website](https://www.docker.com/products/docker-desktop/).

## Setup Instructions

### Step 1: Get the Course Materials

If you have `git` installed, you can clone the repository. Otherwise, you can download the materials as a ZIP file.

```bash
# Clone the repository (recommended)
git clone https://github.com/doingandlearning/postgres-and-pgvector
cd postgres-and-pgvector
```

### Step 2: Install Python Dependencies

It is highly recommended to use a Python virtual environment to avoid conflicts with other projects.

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
# On macOS and Linux:
source .venv/bin/activate
# On Windows:
# .\.venv\Scripts\activate

# 3. Install the required packages
pip install -r requirements.txt
```

### Step 3: Start the Docker Services

The services (database and embedding model server) are defined in a `docker-compose.yml` file located in the `environment/` directory.

```bash
# Navigate to the environment directory
cd environment

# Start the services in the background
docker compose up -d
```

This command will download the necessary Docker images and start the containers. This may take a few minutes the first time.

### Step 4: Download the Embedding Model

The Ollama service needs to download the `bge-m3` embedding model, which we'll use throughout the course.

First, find the name of your Ollama container:

```bash
docker ps
```

Look for a name that ends with `-ollama-1`. It will likely be `environment-ollama-1`.

Now, run the following command, replacing `<container_name>` with the name you found:

```bash
# Example: docker exec environment-ollama-1 ollama pull bge-m3
docker exec <container_name> ollama pull bge-m3
```

This download is a few gigabytes and may take some time depending on your internet connection.

### Step 5: Verify Your Setup

To make sure everything is working correctly, run the provided verification script from the root directory of the project.

```bash
# Make sure you are in the root directory of the project
# and your virtual environment is activated.

python verify_setup.py
```

The script will check your Python version, database connection, and the Ollama embedding service. If all checks pass, you'll see a success message. If not, it will provide error messages to help you troubleshoot.

---

You're all set! We look forward to seeing you in the course.

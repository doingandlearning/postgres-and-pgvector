import sys
import os
import psycopg
import requests
import json
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- Configuration ---
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "pgvector"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5050"),
}
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embed")
OLLAMA_MODEL = "bge-m3"

def check_python_version():
    """Checks if the Python version is 3.13 or lower."""
    print("--- 1. Checking Python Version ---")
    is_ok = sys.version_info < (3, 14)
    if is_ok:
        print(f"✅ Success: Your Python version is {sys.version.split()[0]}, which is compatible.")
    else:
        print(f"❌ Error: Your Python version is {sys.version.split()[0]}. This course requires Python 3.13 or older.")
    return is_ok

def check_db_connection():
    """Checks if a connection can be established with the PostgreSQL database."""
    print("\n--- 2. Checking Database Connection ---")
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Test a simple query
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        print(f"✅ Success: Connected to PostgreSQL.")
        print(f"   Version: {db_version.split(',')[0]}")
        cur.close()
        conn.close()
        return True
    except psycopg.OperationalError as e:
        print(f"❌ Error: Could not connect to the database.")
        print("   Please ensure the Docker services are running (`docker compose up -d`).")
        print(f"   Details: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

def check_ollama_service():
    """Checks if the Ollama embedding service is running and the model is available."""
    print("\n--- 3. Checking Ollama Embedding Service ---")
    try:
        # Test embedding a simple string
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "input": "test"},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        if data.get("embeddings"):
             print(f"✅ Success: Ollama service is running and model '{OLLAMA_MODEL}' is responding.")
             return True
        else:
            print("❌ Error: Ollama service responded but did not return an embedding.")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to Ollama at {OLLAMA_URL}.")
        print("   Please ensure the Docker services are running.")
        return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"❌ Error: Ollama service is running, but the model '{OLLAMA_MODEL}' was not found.")
            print(f"   Please pull the model with: `docker exec <container_name> ollama pull {OLLAMA_MODEL}`")
        else:
            print(f"❌ Error: An HTTP error occurred: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

def main():
    print("🚀 Starting Pre-Course Setup Verification...\n")
    
    # Run all checks
    py_ok = check_python_version()
    db_ok = check_db_connection()
    ollama_ok = check_ollama_service()
    
    print("\n--- Summary ---")
    if all([py_ok, db_ok, ollama_ok]):
        print("🎉 Congratulations! Your environment is set up correctly.")
        print("You are ready for the course.")
    else:
        print("⚠️ Your environment has one or more issues. Please review the errors above and follow the setup guide.")

if __name__ == "__main__":
    main() 
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/load_data.py .
COPY scripts/csv_data.py .

# Ensure the output directory exists for storing data
RUN mkdir -p /app/data
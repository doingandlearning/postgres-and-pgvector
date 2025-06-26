# Use a slim Python image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask application files
COPY server/flask_app.py .

# Set the Flask app environment variables (optional)
ENV FLASK_APP=flask_app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose Flask's default port
EXPOSE 5000

# Command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]

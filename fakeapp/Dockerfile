FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=src/api/main.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "src/api/main.py"]

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for python-magic (libmagic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (includes agents/, rules/, templates/, main.py)
COPY . .

# Expose port
EXPOSE 8000

# Run backend
CMD ["python", "main.py"]

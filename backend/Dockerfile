FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (includes agents/, rules/, templates/, main.py)
COPY . .

# Expose port
EXPOSE 8000

# Run backend
CMD ["python", "main.py"]

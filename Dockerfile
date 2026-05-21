FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python packages - install uvicorn explicitly first
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uvicorn==0.24.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure uvicorn is in PATH
RUN which uvicorn

# Expose port
EXPOSE 8000

# Run the application using python -m uvicorn (more reliable)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
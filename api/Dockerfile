FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port (Render provides PORT env var, default 10000)
EXPOSE 10000

# Run with uvicorn -- use $PORT for Render compatibility
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 2

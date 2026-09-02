FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for asyncpg, psycopg, and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Render exposes the dynamic port via $PORT (defaults to 10000 if unset)
ENV PORT=10000

EXPOSE $PORT

# Start application using production uvicorn workers
CMD ["sh", "-c", "gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30"]
FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2 / asyncpg / bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --default-timeout=1000 --no-cache-dir -e ".[dev]"

# Bake the sentence-transformer model into the image at build time.
# This caches the weights in a Docker layer so encode() never downloads
# at runtime — critical for containers with restricted egress or slow cold starts.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Force offline mode at runtime — model is baked in above, no network calls needed.
# This eliminates the ~50s HuggingFace Hub metadata check on every cold start.
ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

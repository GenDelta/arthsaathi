# ── ArthSaathi Backend Dockerfile ──────────────────────────────────────────
# Builds a production-ready image with:
#   • Python 3.11 slim base
#   • Tesseract OCR (for scam-scanner PDF/image processing)
#   • uv for fast dependency installation
#   • HuggingFace embedding model pre-downloaded at build time
#   • SQLite DB + LanceDB seeded at build time (avoids 512MB OOM on free tier)
# ───────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps: Tesseract OCR + build tools for pikepdf / lancedb
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
ENV PYTHONPATH="/app"
ENV CUDA_VISIBLE_DEVICES=""
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false

# Pre-install CPU-only PyTorch (avoids 2.5GB+ of NVIDIA CUDA libraries, drops RAM to ~100MB)
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/cpu

# Copy dependency manifest first (better layer caching)
COPY pyproject.toml ./

# Install all production dependencies
RUN uv pip install --system --no-cache -e .

# Copy full application source (including data/ and scripts/)
COPY . .

# ── Build-time setup (runs with ~4GB build RAM, not 512MB runtime RAM) ──────

# 1. Pre-download the HuggingFace embedding model into the image layer
RUN python -c "\
from langchain_huggingface import HuggingFaceEmbeddings; \
HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'); \
print('Embedding model downloaded.')"

# 2. Run DB migrations
# JWT_SECRET is required by pydantic Settings — use a build-time placeholder.
# Render's real JWT_SECRET env var overrides this at runtime.
RUN JWT_SECRET=build-time-placeholder python -m app.db.init_db

# 3. Init LanceDB tables
RUN JWT_SECRET=build-time-placeholder python -m app.db.init_lancedb

# 4. Seed schemes + predatory clauses into SQLite and LanceDB
#    This is the memory-heavy step — safe here, OOM-safe at runtime
RUN JWT_SECRET=build-time-placeholder PYTHONPATH=/app python scripts/seed_schemes.py && \
    JWT_SECRET=build-time-placeholder PYTHONPATH=/app python scripts/seed_clauses.py

# ───────────────────────────────────────────────────────────────────────────

EXPOSE 8000

# start.sh only runs idempotent migration checks then launches uvicorn
CMD ["bash", "start.sh"]

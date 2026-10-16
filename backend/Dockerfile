# ── ArthSaathi Backend Dockerfile ──────────────────────────────────────────
# Builds a production-ready image with:
#   • Python 3.11 slim base
#   • Tesseract OCR (for scam-scanner PDF/image processing)
#   • uv for fast dependency installation
#   • HuggingFace embedding model pre-downloaded at build time
# ───────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps: Tesseract OCR + build tools for pikepdf / lancedb
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency manifest first (better layer caching)
COPY pyproject.toml ./

# Install all production dependencies
RUN uv pip install --system --no-cache -e .

# Pre-download the HuggingFace embedding model so it's baked into the image
# This avoids a 2-3 min cold-start download on Render
RUN python -c "\
from langchain_huggingface import HuggingFaceEmbeddings; \
HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'); \
print('Embedding model downloaded.')"

# Copy application source
COPY . .

# Expose FastAPI port (Render injects $PORT at runtime)
EXPOSE 8000

# Startup: run DB + LanceDB init, seed schemes, then launch server
CMD ["bash", "start.sh"]

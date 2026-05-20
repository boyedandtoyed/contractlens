FROM python:3.11-slim

WORKDIR /app

# System deps — cached unless this block changes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies BEFORE copying source
# This layer is cached as long as pyproject.toml doesn't change
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "fastapi>=0.111.0" \
    "uvicorn[standard]>=0.29.0" \
    "pydantic>=2.7.0" \
    "transformers>=4.40.0" \
    "torch>=2.3.0" \
    "spacy>=3.7.0" \
    "streamlit>=1.35.0" \
    "python-multipart>=0.0.9" \
    "pypdf>=4.2.0" \
    "numpy>=1.26.0" \
    "requests"

# Download models — cached as long as layer above is cached
RUN python -m spacy download en_core_web_sm
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='typeform/distilbert-base-uncased-mnli', device=-1)"

# Copy source last — changes here only invalidate this one fast layer
COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8000 8501

CMD ["streamlit", "run", "src/contractlens/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

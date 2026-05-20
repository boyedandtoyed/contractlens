FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir -e .

RUN python -m spacy download en_core_web_sm

RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='typeform/distilbert-base-uncased-mnli', device=-1)"

ENV PYTHONPATH=/app/src

EXPOSE 8000 8501

CMD ["streamlit", "run", "src/contractlens/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

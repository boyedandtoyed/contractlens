FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

RUN python -m spacy download en_core_web_sm

COPY src/ ./src/

EXPOSE 8000 8501

CMD ["streamlit", "run", "src/contractlens/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

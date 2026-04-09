# ContractLens

AI-powered legal contract analysis. Identifies and risk-scores clauses (termination, indemnification, IP, etc.) using BERT zero-shot classification with a keyword fallback.

## Quick Start

```bash
pip install -e .
# Streamlit UI
streamlit run src/contractlens/app.py
# API server
uvicorn contractlens.api:app --reload
```

## API

POST `/analyze/text` — analyze contract text
POST `/analyze/file` — analyze PDF or text file upload

## Tech Stack

BERT (transformers), SpaCy, Streamlit, FastAPI, Pydantic v2, PyPDF

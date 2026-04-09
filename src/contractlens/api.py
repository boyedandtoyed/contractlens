"""FastAPI endpoints for ContractLens."""
from __future__ import annotations
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from .extractor import ClauseExtractor
from .risk_scorer import score_contract

app = FastAPI(title="ContractLens API", version="0.1.0")
_extractor = ClauseExtractor()


class TextRequest(BaseModel):
    text: str
    threshold: float = 0.4


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze/text")
def analyze_text(req: TextRequest):
    if len(req.text) < 50:
        raise HTTPException(400, "Text too short")
    clauses = _extractor.extract(req.text, req.threshold)
    return score_contract(clauses)


@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    content = await file.read()
    if file.filename and file.filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:
            raise HTTPException(400, f"PDF parse error: {e}")
    else:
        text = content.decode("utf-8", errors="replace")
    clauses = _extractor.extract(text)
    return score_contract(clauses)

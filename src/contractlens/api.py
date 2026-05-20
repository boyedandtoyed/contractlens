"""FastAPI server for ContractLens."""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .analyzer import ContractAnalyzer
from .models import AnalyzeTextRequest, ContractAnalysis
from .utils import extract_text_from_pdf

app = FastAPI(
    title="ContractLens API",
    description="AI-powered legal contract analysis using BERT zero-shot classification.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_analyzer = ContractAnalyzer()


@app.get("/")
def root():
    return {
        "name": "ContractLens API",
        "version": "0.1.0",
        "endpoints": {
            "POST /analyze/text": "Analyze contract text (JSON body)",
            "POST /analyze/file": "Analyze uploaded PDF or TXT file",
            "GET /health": "Health check",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze/text", response_model=ContractAnalysis)
def analyze_text(req: AnalyzeTextRequest) -> ContractAnalysis:
    if len(req.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short — provide at least 50 characters.")
    filename = req.filename or "contract.txt"
    return _analyzer.analyze(req.text, filename=filename)


@app.post("/analyze/file", response_model=ContractAnalysis)
async def analyze_file(file: UploadFile = File(...)) -> ContractAnalysis:
    content = await file.read()
    filename = file.filename or "upload"

    if filename.lower().endswith(".pdf"):
        try:
            text = extract_text_from_pdf(content)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"PDF parse error: {exc}") from exc
    elif filename.lower().endswith(".txt"):
        text = content.decode("utf-8", errors="replace")
    else:
        raise HTTPException(status_code=415, detail="Only PDF and TXT files are supported.")

    if len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Extracted text too short — check file content.")

    return _analyzer.analyze(text, filename=filename)

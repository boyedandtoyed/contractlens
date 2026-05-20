"""BERT zero-shot clause analyzer with keyword fallback."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import ClauseAnalysis, ClauseType, ContractAnalysis, RiskLevel
from .utils import clean_text, split_paragraphs

CLAUSE_LABELS: list[str] = [
    "termination",
    "indemnification",
    "intellectual property",
    "liability limitation",
    "confidentiality",
    "dispute resolution",
    "payment terms",
    "warranty",
    "force majeure",
    "governing law",
]

_LABEL_TO_TYPE: dict[str, ClauseType] = {
    "termination": "termination",
    "indemnification": "indemnification",
    "intellectual property": "intellectual_property",
    "liability limitation": "liability_limitation",
    "confidentiality": "confidentiality",
    "dispute resolution": "dispute_resolution",
    "payment terms": "payment_terms",
    "warranty": "warranty",
    "force majeure": "force_majeure",
    "governing law": "governing_law",
}

_RISK_BASE: dict[ClauseType, float] = {
    "termination": 0.65,
    "indemnification": 0.90,
    "intellectual_property": 0.85,
    "liability_limitation": 0.80,
    "confidentiality": 0.60,
    "dispute_resolution": 0.65,
    "payment_terms": 0.50,
    "warranty": 0.55,
    "force_majeure": 0.35,
    "governing_law": 0.40,
}

_KEYWORDS: dict[ClauseType, list[str]] = {
    "termination": ["terminat", "cancel", "expir"],
    "indemnification": ["indemnif", "hold harmless", "defend and indemnify"],
    "intellectual_property": ["intellectual property", "patent", "copyright", "trademark", "ip rights", "work product"],
    "liability_limitation": ["limitation of liability", "liable for", "damages", "cap on liability", "in no event"],
    "confidentiality": ["confidential", "non-disclosure", "nda", "proprietary information"],
    "dispute_resolution": ["arbitration", "dispute resolution", "mediation", "litigation", "binding arbitration"],
    "payment_terms": ["payment", "invoice", "fee schedule", "pricing", "billing", "net 30"],
    "warranty": ["warrant", "represent and warrant", "guarantee", "disclaim", "as-is"],
    "force_majeure": ["force majeure", "act of god", "unforeseen circumstances", "beyond reasonable control"],
    "governing_law": ["governing law", "jurisdiction", "applicable law", "venue", "choice of law"],
}


def _risk_level(score: float) -> RiskLevel:
    if score >= 0.70:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _keyword_classify(text: str) -> tuple[ClauseType, float] | None:
    lower = text.lower()
    for clause_type, kws in _KEYWORDS.items():
        if any(kw in lower for kw in kws):
            return clause_type, 0.60
    return None


class ContractAnalyzer:
    def __init__(self) -> None:
        self._pipeline: Any = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        try:
            from transformers import pipeline
            self._pipeline = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
                device=-1,
            )
        except Exception:
            self._pipeline = None

    def _classify(self, text: str) -> tuple[ClauseType, float, float]:
        """Return (clause_type, risk_score, confidence)."""
        self._load()
        if self._pipeline is not None:
            result = self._pipeline(text, CLAUSE_LABELS, multi_label=False)
            raw_label: str = result["labels"][0]
            confidence: float = float(result["scores"][0])
            if confidence >= 0.3:
                clause_type = _LABEL_TO_TYPE.get(raw_label, "governing_law")
                base = _RISK_BASE[clause_type]
                risk_score = round(min(1.0, base * (0.6 + confidence * 0.5)), 3)
                return clause_type, risk_score, round(confidence, 4)

        match = _keyword_classify(text)
        if match:
            clause_type, confidence = match
            base = _RISK_BASE[clause_type]
            risk_score = round(min(1.0, base * 0.85), 3)
            return clause_type, risk_score, round(confidence, 4)

        return "governing_law", 0.20, 0.10

    def analyze(self, text: str, filename: str = "contract.txt") -> ContractAnalysis:
        text = clean_text(text)
        paragraphs = split_paragraphs(text)
        clauses: list[ClauseAnalysis] = []
        seen: set[str] = set()

        for para in paragraphs:
            clause_type, risk_score, confidence = self._classify(para)
            if confidence < 0.25:
                continue
            key = f"{clause_type}:{para[:80]}"
            if key in seen:
                continue
            seen.add(key)
            clauses.append(ClauseAnalysis(
                clause_type=clause_type,
                text_excerpt=para[:500],
                risk_score=risk_score,
                risk_level=_risk_level(risk_score),
                confidence=confidence,
            ))

        overall = round(sum(c.risk_score for c in clauses) / len(clauses), 3) if clauses else 0.0
        return ContractAnalysis(
            filename=filename,
            total_clauses=len(clauses),
            high_risk_count=sum(1 for c in clauses if c.risk_level == "high"),
            medium_risk_count=sum(1 for c in clauses if c.risk_level == "medium"),
            low_risk_count=sum(1 for c in clauses if c.risk_level == "low"),
            clauses=clauses,
            overall_risk_score=overall,
            analyzed_at=datetime.now(timezone.utc),
        )

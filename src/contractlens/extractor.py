"""Clause extraction using BERT zero-shot classification."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any


CLAUSE_LABELS = [
    "termination",
    "indemnification",
    "limitation of liability",
    "confidentiality",
    "intellectual property",
    "payment terms",
    "governing law",
    "dispute resolution",
    "force majeure",
    "non-compete",
]


@dataclass
class ExtractedClause:
    label: str
    text: str
    start: int
    end: int
    score: float


def split_sentences(text: str) -> list[tuple[str, int, int]]:
    """Split text into (sentence, start, end) tuples."""
    sentences = []
    pattern = re.compile(r'(?<=[.!?])\s+')
    prev = 0
    for m in pattern.finditer(text):
        end = m.start()
        s = text[prev:end].strip()
        if len(s) > 20:
            sentences.append((s, prev, end))
        prev = m.end()
    tail = text[prev:].strip()
    if len(tail) > 20:
        sentences.append((tail, prev, len(text)))
    return sentences


class ClauseExtractor:
    """Extract and classify legal clauses from contract text."""

    def __init__(self) -> None:
        self._classifier: Any = None

    def _load(self) -> None:
        if self._classifier is not None:
            return
        try:
            from transformers import pipeline
            self._classifier = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
                device=-1,
            )
        except Exception:
            self._classifier = None

    def extract(self, text: str, threshold: float = 0.4) -> list[ExtractedClause]:
        self._load()
        sentences = split_sentences(text)
        clauses: list[ExtractedClause] = []
        for sent, start, end in sentences:
            if self._classifier is not None:
                result = self._classifier(sent, CLAUSE_LABELS, multi_label=False)
                best_label = result["labels"][0]
                best_score = result["scores"][0]
            else:
                # Keyword fallback
                best_label, best_score = _keyword_classify(sent)
            if best_score >= threshold:
                clauses.append(ExtractedClause(
                    label=best_label,
                    text=sent,
                    start=start,
                    end=end,
                    score=round(best_score, 4),
                ))
        return clauses


def _keyword_classify(text: str) -> tuple[str, float]:
    lower = text.lower()
    mapping = {
        "termination": ["terminat", "cancel", "expire"],
        "indemnification": ["indemnif", "hold harmless"],
        "limitation of liability": ["liability", "damages", "liable"],
        "confidentiality": ["confidential", "non-disclosure", "nda"],
        "intellectual property": ["intellectual property", "patent", "copyright", "trademark"],
        "payment terms": ["payment", "invoice", "fee", "price"],
        "governing law": ["governing law", "jurisdiction", "applicable law"],
        "dispute resolution": ["arbitration", "dispute", "mediation"],
        "force majeure": ["force majeure", "act of god", "unforeseen"],
        "non-compete": ["non-compete", "non compete", "competing"],
    }
    for label, keywords in mapping.items():
        if any(kw in lower for kw in keywords):
            return label, 0.6
    return "other", 0.1

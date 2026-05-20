"""Pydantic models for ContractLens."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high"]

ClauseType = Literal[
    "termination",
    "indemnification",
    "intellectual_property",
    "liability_limitation",
    "confidentiality",
    "dispute_resolution",
    "payment_terms",
    "warranty",
    "force_majeure",
    "governing_law",
]


class ClauseAnalysis(BaseModel):
    clause_type: ClauseType
    text_excerpt: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)


class ContractAnalysis(BaseModel):
    filename: str
    total_clauses: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    clauses: list[ClauseAnalysis]
    overall_risk_score: float = Field(ge=0.0, le=1.0)
    analyzed_at: datetime


class AnalyzeTextRequest(BaseModel):
    text: str
    filename: str | None = None

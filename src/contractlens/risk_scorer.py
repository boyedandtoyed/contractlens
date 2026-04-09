"""Risk scoring for extracted clauses."""
from __future__ import annotations
from .extractor import ExtractedClause

RISK_WEIGHTS: dict[str, float] = {
    "termination": 0.7,
    "indemnification": 0.9,
    "limitation of liability": 0.8,
    "confidentiality": 0.6,
    "intellectual property": 0.85,
    "payment terms": 0.5,
    "governing law": 0.4,
    "dispute resolution": 0.65,
    "force majeure": 0.3,
    "non-compete": 0.75,
}

RISK_EXPLANATIONS: dict[str, str] = {
    "termination": "Unclear termination rights may lock you into unfavorable terms.",
    "indemnification": "Broad indemnification clauses can create significant financial exposure.",
    "limitation of liability": "Caps on liability may be insufficient to cover potential losses.",
    "confidentiality": "Broad confidentiality obligations may restrict future business activities.",
    "intellectual property": "IP assignment clauses may transfer ownership of work product.",
    "payment terms": "Review payment schedules and late-payment penalties carefully.",
    "governing law": "Non-local jurisdiction may increase legal costs in disputes.",
    "dispute resolution": "Mandatory arbitration may waive your right to a jury trial.",
    "force majeure": "Vague force majeure terms may allow unilateral contract suspension.",
    "non-compete": "Non-compete clauses may restrict future employment or business opportunities.",
}


def score_clause(clause: ExtractedClause) -> dict:
    base_risk = RISK_WEIGHTS.get(clause.label, 0.5)
    adjusted = min(1.0, base_risk * (0.5 + clause.score))
    level = "high" if adjusted >= 0.7 else "medium" if adjusted >= 0.45 else "low"
    return {
        "label": clause.label,
        "risk_score": round(adjusted, 3),
        "risk_level": level,
        "explanation": RISK_EXPLANATIONS.get(clause.label, "Review this clause carefully."),
        "text_preview": clause.text[:200],
    }


def score_contract(clauses: list[ExtractedClause]) -> dict:
    if not clauses:
        return {"overall_score": 0.0, "level": "unknown", "clause_risks": []}
    scored = [score_clause(c) for c in clauses]
    overall = sum(s["risk_score"] for s in scored) / len(scored)
    level = "high" if overall >= 0.7 else "medium" if overall >= 0.45 else "low"
    return {
        "overall_score": round(overall, 3),
        "level": level,
        "clause_count": len(clauses),
        "clause_risks": scored,
    }

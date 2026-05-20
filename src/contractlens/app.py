"""Streamlit UI for ContractLens."""
from __future__ import annotations

import io

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="ContractLens",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  /* Dark background to match portfolio aesthetic */
  .stApp { background-color: #0d0d1f; }
  section[data-testid="stSidebar"] { background-color: #0d0d1f; }

  /* Hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* Typography */
  h1, h2, h3, p, label, .stMarkdown { color: #e2e8f0 !important; }

  /* Risk badge helpers */
  .risk-high  { background: rgba(239,68,68,0.15);  border: 1px solid rgba(239,68,68,0.4);  color: #fca5a5; border-radius: 6px; padding: 2px 10px; font-size: 0.75rem; }
  .risk-medium{ background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #fde68a; border-radius: 6px; padding: 2px 10px; font-size: 0.75rem; }
  .risk-low   { background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.4); color: #6ee7b7; border-radius: 6px; padding: 2px 10px; font-size: 0.75rem; }

  /* Stat cards */
  .stat-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem 1.25rem; text-align: center; }
  .stat-number { font-size: 2rem; font-weight: 700; margin: 0; }
  .stat-label  { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(226,232,240,0.55) !important; margin: 0; }

  /* Clause card */
  .clause-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 1rem; margin-bottom: 0.75rem; }
  .clause-type { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.14em; color: rgba(226,232,240,0.5) !important; }
  .clause-excerpt { font-size: 0.8rem; color: rgba(226,232,240,0.7) !important; font-style: italic; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)


def _risk_badge(level: str) -> str:
    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    return f'<span class="risk-{level}">{icons.get(level, "⚪")} {level.upper()}</span>'


def _score_color(score: float) -> str:
    if score >= 0.70:
        return "#ef4444"
    if score >= 0.45:
        return "#f59e0b"
    return "#34d399"


def _call_analyze_text(text: str, filename: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/analyze/text",
        json={"text": text, "filename": filename},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _call_analyze_file(file_bytes: bytes, filename: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/analyze/file",
        files={"file": (filename, io.BytesIO(file_bytes), "application/octet-stream")},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _render_results(result: dict) -> None:
    overall = result["overall_risk_score"]
    total = result["total_clauses"]
    high = result["high_risk_count"]
    medium = result["medium_risk_count"]
    low = result["low_risk_count"]
    color = _score_color(overall)

    st.markdown("---")
    st.markdown("### Analysis Results")

    # Overall score + stats row
    c0, c1, c2, c3, c4 = st.columns([2, 1, 1, 1, 1])
    with c0:
        st.markdown(
            f'<div class="stat-card">'
            f'<p class="stat-number" style="color:{color}">{overall:.0%}</p>'
            f'<p class="stat-label">Overall Risk</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c1:
        st.markdown(
            f'<div class="stat-card"><p class="stat-number" style="color:#94a3b8">{total}</p>'
            f'<p class="stat-label">Clauses</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-card"><p class="stat-number" style="color:#ef4444">{high}</p>'
            f'<p class="stat-label">High Risk</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-card"><p class="stat-number" style="color:#f59e0b">{medium}</p>'
            f'<p class="stat-label">Medium</p></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="stat-card"><p class="stat-number" style="color:#34d399">{low}</p>'
            f'<p class="stat-label">Low Risk</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if not result["clauses"]:
        st.info("No clauses detected. Try lowering the classification threshold or check the input text.")
        return

    # Sort: high → medium → low
    order = {"high": 0, "medium": 1, "low": 2}
    sorted_clauses = sorted(result["clauses"], key=lambda c: order.get(c["risk_level"], 3))

    for clause in sorted_clauses:
        ctype = clause["clause_type"].replace("_", " ").title()
        level = clause["risk_level"]
        score = clause["risk_score"]
        conf = clause["confidence"]
        excerpt = clause["text_excerpt"][:300]

        with st.expander(f"{ctype}  —  risk {score:.0%}", expanded=(level == "high")):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown(f"**Risk Level:** {_risk_badge(level)}", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**Confidence:** `{conf:.0%}`")
            st.markdown(f"*{excerpt}{'…' if len(clause['text_excerpt']) > 300 else ''}*")


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    '<h1 style="font-size:1.8rem;margin-bottom:0.25rem;">⚖️ ContractLens</h1>'
    '<p style="color:rgba(226,232,240,0.55);margin-top:0;font-size:0.9rem;">'
    "AI-powered legal contract analysis · BERT zero-shot classification with keyword fallback"
    "</p>",
    unsafe_allow_html=True,
)

tab_upload, tab_paste = st.tabs(["📄 Upload Contract", "✏️ Paste Text"])

# ── Tab: Upload ──────────────────────────────────────────────────────────────
with tab_upload:
    uploaded = st.file_uploader(
        "Upload a contract (PDF or TXT)",
        type=["pdf", "txt"],
        help="Maximum recommended size: 10 MB",
    )
    if uploaded and st.button("Analyze Contract", type="primary", key="btn_upload"):
        with st.spinner("Analyzing — this may take a moment on first run while the model loads…"):
            try:
                result = _call_analyze_file(uploaded.read(), uploaded.name)
                _render_results(result)
            except requests.HTTPError as exc:
                st.error(f"API error {exc.response.status_code}: {exc.response.text}")
            except requests.ConnectionError:
                st.error("Cannot reach the API server. Make sure the FastAPI backend is running on port 8000.")

# ── Tab: Paste Text ──────────────────────────────────────────────────────────
with tab_paste:
    contract_text = st.text_area(
        "Paste contract text",
        height=320,
        placeholder="Paste the full text of a legal contract here…",
    )
    filename = st.text_input("Document name (optional)", value="contract.txt")
    if st.button("Analyze Contract", type="primary", key="btn_paste", disabled=not contract_text):
        with st.spinner("Analyzing — this may take a moment on first run while the model loads…"):
            try:
                result = _call_analyze_text(contract_text, filename)
                _render_results(result)
            except requests.HTTPError as exc:
                st.error(f"API error {exc.response.status_code}: {exc.response.text}")
            except requests.ConnectionError:
                st.error("Cannot reach the API server. Make sure the FastAPI backend is running on port 8000.")

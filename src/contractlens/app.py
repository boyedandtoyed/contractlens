"""Streamlit interface for ContractLens."""
import streamlit as st
from contractlens.extractor import ClauseExtractor
from contractlens.risk_scorer import score_contract

st.set_page_config(page_title="ContractLens", page_icon="⚖️", layout="wide")
st.title("⚖️ ContractLens — AI Contract Analysis")
st.caption("Paste contract text or upload a PDF to identify risky clauses.")

extractor = ClauseExtractor()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input")
    mode = st.radio("Input mode", ["Paste text", "Upload PDF"], horizontal=True)
    text = ""
    if mode == "Paste text":
        text = st.text_area("Contract text", height=400, placeholder="Paste contract text here...")
    else:
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded:
            try:
                from pypdf import PdfReader
                import io
                reader = PdfReader(io.BytesIO(uploaded.read()))
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
                st.success(f"Extracted {len(text)} characters from {len(reader.pages)} pages")
            except Exception as e:
                st.error(f"PDF error: {e}")

    threshold = st.slider("Classification threshold", 0.1, 0.9, 0.4, 0.05)
    analyze = st.button("Analyze Contract", type="primary", disabled=not text)

with col2:
    st.subheader("Results")
    if analyze and text:
        with st.spinner("Analyzing..."):
            clauses = extractor.extract(text, threshold)
            report = score_contract(clauses)

        score = report["overall_score"]
        level = report["level"]
        color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
        st.metric("Overall Risk Score", f"{score:.0%}", delta=None)
        st.markdown(f"**Risk Level:** {color} {level.upper()}")
        st.divider()

        for item in report.get("clause_risks", []):
            risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["risk_level"], "⚪")
            with st.expander(f"{risk_color} {item['label'].title()} — {item['risk_score']:.0%}"):
                st.markdown(f"**Explanation:** {item['explanation']}")
                st.markdown(f"**Clause excerpt:** _{item['text_preview']}..._")
    else:
        st.info("Enter contract text and click Analyze to see results.")

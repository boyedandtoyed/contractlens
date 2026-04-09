from contractlens.extractor import split_sentences, _keyword_classify

def test_split_sentences():
    text = "This is sentence one. This is sentence two. And a third sentence here."
    results = split_sentences(text)
    assert len(results) >= 2

def test_keyword_classify_termination():
    label, score = _keyword_classify("Either party may terminate this agreement with 30 days notice.")
    assert label == "termination"
    assert score > 0

def test_keyword_classify_fallback():
    label, score = _keyword_classify("This is a generic clause about something.")
    assert label == "other"

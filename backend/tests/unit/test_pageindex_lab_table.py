from app.documents.pageindex import build_pageindex, retrieve_pageindex
from app.documents.query_policy import wants_document_summary
from app.documents.extraction import ExtractedPage

LAB_PAGE = "\n".join(
    [
        "Sample Diagnostics Laboratory",
        "Test Result Unit Reference range",
        "Vitamin D 25-OH 18 ng/mL 30 - 100",
        "LDL Cholesterol 152 mg/dL 0 - 100",
        "HDL Cholesterol 48 mg/dL 40 - 60",
    ]
)


def test_lab_table_rows_are_not_headings():
    tree = build_pageindex("doc", [ExtractedPage(page_number=1, text=LAB_PAGE, character_count=len(LAB_PAGE))])
    assert any("LDL Cholesterol 152" in node.text for node in tree.nodes)
    assert all(node.text.strip() for node in tree.nodes)


def test_real_headings_still_split():
    page = "FINDINGS\nMild fatty change.\nIMPRESSION\nNo acute disease."
    tree = build_pageindex("doc", [ExtractedPage(page_number=1, text=page, character_count=len(page))])
    assert [node.title for node in tree.nodes] == ["FINDINGS", "IMPRESSION"]


def test_overview_question_retrieves_text():
    tree = build_pageindex("doc", [ExtractedPage(page_number=1, text=LAB_PAGE, character_count=len(LAB_PAGE))])
    assert retrieve_pageindex(tree, "Explain this document in simple words")


def test_explain_this_document_is_a_summary_request():
    for text in ("Explain this document in simple words", "what is in this pdf", "Explain this report"):
        assert wants_document_summary(text)


def test_page_numbers_are_removed_from_document_replies():
    from app.pipeline.document_answer import _evidence_for_model, strip_page_mentions

    assert strip_page_mentions("HbA1c is 5%, within 4.2% to 5.7% on page 1.") == "HbA1c is 5%, within 4.2% to 5.7%."
    assert "page" not in strip_page_mentions("LDL is 152 (page 2). See page 3 for details.").lower()
    evidence = "HbA1c 5 % page 1\nConflicting values for X: 5.7, 15%\nLDL 152 mg/dL page 1"
    cleaned = _evidence_for_model(evidence)
    assert "page" not in cleaned and "Conflicting" not in cleaned

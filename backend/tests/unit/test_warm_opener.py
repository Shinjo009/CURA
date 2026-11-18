from app.pipeline.markdown_tidy import tidy_markdown
from app.pipeline.answer_polish import incomplete_segments


def test_friendly_opener_line_survives_tidy_and_is_not_flagged():
    text = (
        "Good news first, your vitamin D is easy to work on.\n\n"
        "- **Vitamin D: 14 ng/mL** is a bit under the range on your report.\n"
        "- Try a bowl of curd with breakfast this week."
    )
    out = tidy_markdown(text)
    assert out.startswith("Good news first, your vitamin D is easy to work on.")
    assert out.count("\n- ") == 2
    assert not incomplete_segments(out)


def test_dropping_an_unsupported_sentence_keeps_the_opener_and_bullets_on_their_own_lines():
    from app.pipeline.validator import _drop_unsupported

    answer = (
        "Good news first, I can explain this one simply.\n\n"
        "- Your HbA1c is 6.3%, a little above the range on your report.\n"
        "- Try a short walk after dinner this week.\n"
        "- Small steady changes add up."
    )
    out = _drop_unsupported(answer, [("- Your HbA1c is 6.3%, a little above the range on your report.", "6.3")])
    assert out == (
        "Good news first, I can explain this one simply.\n\n"
        "- Try a short walk after dinner this week.\n"
        "- Small steady changes add up."
    )

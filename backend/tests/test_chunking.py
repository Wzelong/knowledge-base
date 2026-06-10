from app.pipeline.chunking import split_text


def test_short_text_single_chunk():
    text = "one paragraph"
    assert split_text(text, chunk_chars=100) == [text]


def test_splits_on_paragraph_boundaries():
    paragraphs = [f"paragraph {i} " + "x" * 40 for i in range(6)]
    text = "\n\n".join(paragraphs)

    chunks = split_text(text, chunk_chars=120)

    assert len(chunks) > 1
    for paragraph in paragraphs:
        assert any(paragraph in chunk for chunk in chunks)
    assert "\n\n".join(chunks) == text


def test_oversized_paragraph_kept_whole():
    big = "y" * 500
    chunks = split_text(f"small\n\n{big}\n\nsmall again", chunk_chars=100)

    assert any(big in chunk for chunk in chunks)

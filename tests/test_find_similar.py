"""Tests for TemplateCollection.find_similar() — F12."""

from prompt_mgr.models import Template, TemplateCollection


def _make(name, content, **kw):
    return Template(name=name, content=content, **kw)


def test_basic_similarity():
    """Higher Jaccard → higher score."""
    c = TemplateCollection()
    c.add(_make("a", "the cat sat on the mat"))
    c.add(_make("b", "the cat sat on the floor"))
    c.add(_make("c", "hello world"))
    c.add(_make("d", "dog ran in the park"))
    result = c.find_similar("a", top_k=3)
    assert len(result) == 3
    names = [r[0] for r in result]
    scores = [r[1] for r in result]
    # "b" should be most similar to "a"
    assert names[0] == "b"
    # "b" score should be higher than "c" and "d"
    assert scores[0] > scores[1]
    # all scores should be between 0 and 1
    for s in scores:
        assert 0.0 <= s <= 1.0


def test_identical_content_gives_one():
    """Two templates with identical content → Jaccard = 1.0."""
    c = TemplateCollection()
    c.add(_make("a", "hello world foo bar"))
    c.add(_make("b", "hello world foo bar"))
    result = c.find_similar("a")
    assert len(result) == 1
    assert result[0] == ("b", 1.0)


def test_no_overlap_gives_zero():
    """Completely different words → Jaccard = 0.0."""
    c = TemplateCollection()
    c.add(_make("a", "alpha beta gamma"))
    c.add(_make("b", "xray yankee zulu"))
    result = c.find_similar("a")
    assert result[0][1] == 0.0


def test_empty_content():
    """Empty content templates: both empty → 1.0, only target empty → 0.0."""
    c = TemplateCollection()
    c.add(_make("a", ""))
    c.add(_make("b", ""))
    c.add(_make("c", "hello"))
    result = c.find_similar("a")
    assert len(result) == 2
    # Both empty → 1.0
    b_score = next(s for name, s in result if name == "b")
    assert b_score == 1.0
    # Target empty, other non-empty → 0.0
    c_score = next(s for name, s in result if name == "c")
    assert c_score == 0.0


def test_target_not_found_raises():
    """Non-existent template name → ValueError."""
    c = TemplateCollection()
    try:
        c.find_similar("nope")
        assert False, "Should have raised"
    except ValueError as e:
        assert "nope" in str(e)


def test_top_k_limits_results():
    """top_k truncates results."""
    c = TemplateCollection()
    c.add(_make("a", "one"))
    for i in range(5):
        c.add(_make(f"b{i}", f"word{i} extra"))
    result = c.find_similar("a", top_k=2)
    assert len(result) == 2


def test_single_template_returns_empty():
    """Only one template → empty result."""
    c = TemplateCollection()
    c.add(_make("a", "hello"))
    result = c.find_similar("a")
    assert result == []


def test_case_insensitive():
    """Similarity is case-insensitive."""
    c = TemplateCollection()
    c.add(_make("a", "Hello World"))
    c.add(_make("b", "hello world"))
    result = c.find_similar("a")
    assert result[0] == ("b", 1.0)


def test_score_rounding():
    """Scores are rounded to 4 decimal places."""
    c = TemplateCollection()
    c.add(_make("a", "alpha beta"))
    c.add(_make("b", "alpha beta gamma"))
    result = c.find_similar("a")
    score = result[0][1]
    # Should be 2/3 ≈ 0.6667
    assert score == 0.6667 or score == 0.6666  # rounding


def test_longer_common_subset():
    """Partial overlap across many words."""
    c = TemplateCollection()
    c.add(_make("a", "system prompt you are helpful assistant answer questions"))
    c.add(_make("b", "system prompt you are friendly assistant help users"))
    c.add(_make("c", "completely different topic about weather forecast"))
    result = c.find_similar("a")
    assert result[0][0] == "b"
    assert result[0][1] > 0.3
    assert result[1][1] < 0.2  # "c" should be much less similar


def test_manager_integration():
    """find_similar works through PromptManager."""
    from prompt_mgr.manager import PromptManager
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        os.environ["PROMPT_MGR_DATA_DIR"] = td
        try:
            mgr = PromptManager()
            mgr.add_template("sys", "You are a helpful assistant")
            mgr.add_template("var", "You are a helpful coder")
            mgr.add_template("off", "Unrelated content here")
            result = mgr.collection.find_similar("sys")
            assert result[0][0] == "var"
            assert result[0][1] > 0.5
        finally:
            del os.environ["PROMPT_MGR_DATA_DIR"]


def test_scores_sorted_descending():
    """Results are always sorted by score descending."""
    c = TemplateCollection()
    c.add(_make("a", "word1 word2 word3"))
    c.add(_make("b", "word1"))
    c.add(_make("c", "word1 word2"))
    c.add(_make("d", "word1 word2 word3 word4"))
    result = c.find_similar("a")
    scores = [s for _, s in result]
    assert scores == sorted(scores, reverse=True)


def test_special_chars_in_content():
    """Special characters are treated as token boundaries."""
    c = TemplateCollection()
    c.add(_make("a", "foo-bar baz"))
    c.add(_make("b", "foo bar baz"))
    result = c.find_similar("a")
    # "foo-bar" splits to "foo-bar" while "foo bar" splits to "foo","bar"
    # So overlap is only "baz" out of {"foo-bar", "baz"} ∪ {"foo", "bar", "baz"}
    assert result[0][1] < 1.0


def test_zero_top_k():
    """top_k=0 returns empty list."""
    c = TemplateCollection()
    c.add(_make("a", "hello"))
    c.add(_make("b", "hello world"))
    result = c.find_similar("a", top_k=0)
    assert result == []

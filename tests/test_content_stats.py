"""Tests for TemplateCollection.content_stats() — F14."""

from prompt_mgr.models import Template, TemplateCollection


def _make(name, content, **kw):
    return Template(name=name, content=content, **kw)


def test_empty_collection():
    """Empty collection returns zeros."""
    c = TemplateCollection()
    s = c.content_stats()
    assert s["total_chars"] == 0
    assert s["total_tokens"] == 0
    assert s["longest"] is None
    assert s["shortest"] is None


def test_single_template():
    """Single template stats are correct."""
    c = TemplateCollection()
    c.add(_make("a", "hello world"))
    s = c.content_stats()
    assert s["total_chars"] == 11
    assert s["total_tokens"] == 2
    assert s["avg_chars"] == 11
    assert s["avg_tokens"] == 2
    assert s["longest"] == "a"
    assert s["shortest"] == "a"


def test_multiple_templates():
    """Multiple templates aggregate correctly."""
    c = TemplateCollection()
    c.add(_make("a", "hello"))           # 5 chars, 1 token
    c.add(_make("b", "hello world"))     # 11 chars, 2 tokens
    s = c.content_stats()
    assert s["total_chars"] == 16
    assert s["total_tokens"] == 3
    assert s["avg_chars"] == 8   # 16/2
    assert s["avg_tokens"] == 1  # 3/2 integer division
    assert s["longest"] == "b"
    assert s["shortest"] == "a"


def test_total_variables():
    """total_variables counts variable slots."""
    c = TemplateCollection()
    c.add(_make("a", "{{x}} {{y}}"))
    c.add(_make("b", "{{z}}"))
    s = c.content_stats()
    # extract_variables returns unique vars per template
    assert s["total_variables"] == 3  # 2 + 1


def test_longest_and_shortest():
    """Longest/shortest correctly identified."""
    c = TemplateCollection()
    c.add(_make("big", "a" * 100))
    c.add(_make("mid", "b" * 50))
    c.add(_make("tiny", "c"))
    s = c.content_stats()
    assert s["longest"] == "big"
    assert s["shortest"] == "tiny"


def test_empty_content_template():
    """Empty content template counted (0 chars, 0 tokens)."""
    c = TemplateCollection()
    c.add(_make("empty", ""))
    s = c.content_stats()
    assert s["total_chars"] == 0
    assert s["total_tokens"] == 0
    assert s["longest"] == "empty"
    assert s["shortest"] == "empty"


def test_manager_integration():
    """content_stats works through PromptManager."""
    from prompt_mgr.manager import PromptManager
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        os.environ["PROMPT_MGR_DATA_DIR"] = td
        try:
            mgr = PromptManager()
            mgr.add_template("a", "Hello {{name}}")
            mgr.add_template("b", "You are {{role}}, do {{task}}")
            s = mgr.collection.content_stats()
            assert s["total_chars"] > 0
            assert s["total_variables"] == 3  # name + role + task
            assert s["longest"] == "b"
        finally:
            del os.environ["PROMPT_MGR_DATA_DIR"]


def test_keys_complete():
    """All expected keys present in result."""
    c = TemplateCollection()
    c.add(_make("a", "x"))
    s = c.content_stats()
    expected = {"total_chars", "total_tokens", "avg_chars", "avg_tokens",
                "longest", "shortest", "total_variables"}
    assert set(s.keys()) == expected

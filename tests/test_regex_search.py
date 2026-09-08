"""Tests for F19: TemplateCollection.search(regex=True)."""

import pytest

from prompt_mgr.models import Template, TemplateCollection


@pytest.fixture
def col():
    c = TemplateCollection()
    c.add(Template(name="greet-user", content="Hello {{name}}!", tags=["a"]))
    c.add(Template(name="farewell", content="Goodbye {{name}}", description="bye bye", tags=["a", "b"]))
    c.add(Template(name="code-review", content="Review this \\d+ patch", tags=["b"]))
    return c


def test_regex_default_off_unchanged(col):
    """Default behavior: substring match, regex chars literal."""
    # "review" as substring matches code-review via name AND content of others? No — literal.
    results = col.search("{{name}}")
    names = {t.name for t in results}
    assert names == {"greet-user", "farewell"}


def test_regex_basic(col):
    """regex=True interprets the query as a pattern."""
    results = col.search(r"\{\{name\}\}", regex=True)
    assert {t.name for t in results} == {"greet-user", "farewell"}


def test_regex_word_boundary(col):
    """Patterns like word boundaries work."""
    results = col.search(r"\bbye\b", regex=True)
    # 'bye bye' in description matches; 'Goodbye' does not (\b fails between d/b... 
    # actually 'Goodbye' — 'bye' at end: boundary between 'd' and 'b'? No, both word chars.
    assert {t.name for t in results} == {"farewell"}


def test_regex_matches_content(col):
    """Regex applied to content too."""
    results = col.search(r"\\d\+", regex=True)
    assert {t.name for t in results} == {"code-review"}


def test_regex_matches_name(col):
    """Regex applied to name."""
    results = col.search(r"^greet-", regex=True)
    assert {t.name for t in results} == {"greet-user"}


def test_regex_case_sensitive(col):
    """regex=True is case-sensitive (documented difference from substring mode)."""
    results = col.search(r"HELLO", regex=True)
    assert results == []
    results = col.search(r"Hello", regex=True)
    assert {t.name for t in results} == {"greet-user"}


def test_regex_combined_with_tags(col):
    """regex combines with tag filter (AND semantics preserved)."""
    results = col.search(r"\{\{name\}\}", tags=["b"], regex=True)
    assert {t.name for t in results} == {"farewell"}


def test_regex_invalid_pattern_raises(col):
    """Invalid regex raises ValueError with a clear message."""
    with pytest.raises(ValueError, match="Invalid regex"):
        col.search(r"([unclosed", regex=True)


def test_regex_empty_query_returns_all(col):
    """Empty regex query matches everything (matches search() contract)."""
    results = col.search("", regex=True)
    assert len(results) == 3

"""Tests for Template.render() literal-substitution bugfix + F15 export_markdown()."""

from datetime import datetime

from prompt_mgr.models import Template, TemplateCollection


def _make(name, content, **kw):
    return Template(name=name, content=content, **kw)


# ── render() backslash bugfix (was: re.sub interpreted replacement escapes) ──

def test_render_backslash_group_reference():
    """Regression: r'\\1' in a value must not raise invalid group reference."""
    t = _make("t", "value: {{v}}")
    assert t.render({"v": r"\1group"}) == "value: \\1group"


def test_render_backslash_escape_corruption():
    """Regression: '\\f'/'\\n' in a value must be kept literally, not converted."""
    t = _make("t", "path: {{p}}")
    out = t.render({"p": "C:\\new\\folder"})
    assert out == "path: C:\\new\\folder"
    assert "\x0c" not in out  # form-feed that '\f' used to become


def test_render_literal_backslash_roundtrip():
    """Values with mixed backslash content round-trip unchanged."""
    val = r"a\b\g<1>\\n"
    t = _make("t", "{{x}}")
    assert t.render({"x": val}) == val


def test_render_multiple_variables_with_escapes():
    """Each substitution stays literal when earlier values contain escapes."""
    t = _make("t", "{{a}}-{{b}}")
    assert t.render({"a": r"\1", "b": r"\2"}) == "\\1-\\2"


# ── F15: TemplateCollection.export_markdown() ──

def test_export_markdown_empty():
    """Empty collection produces header + placeholder."""
    doc = TemplateCollection().export_markdown()
    assert doc.startswith("# Prompt Library")
    assert "_No templates._" in doc
    assert "## Contents" not in doc


def test_export_markdown_basic():
    """Single template exports header, TOC entry and section body."""
    c = TemplateCollection()
    c.add(_make("greet", "hello {{name}}", tags=["chat"]))
    doc = c.export_markdown()
    assert doc.startswith("# Prompt Library")
    assert "_Generated:" in doc
    assert "## Contents" in doc
    assert "- [greet](#greet)" in doc
    assert "## greet" in doc
    assert "hello {{name}}" in doc
    assert "**Tags:** chat" in doc


def test_export_markdown_multiple_templates():
    """All templates appear, TOC links each one."""
    c = TemplateCollection()
    for name in ("beta", "alpha", "gamma"):
        c.add(_make(name, f"content of {name}"))
    doc = c.export_markdown()
    for name in ("beta", "alpha", "gamma"):
        assert f"[{name}](#{name})" in doc
        assert f"content of {name}" in doc


def test_export_markdown_sorted_by_name():
    """Default sort is alphabetical by name."""
    c = TemplateCollection()
    c.add(_make("zeta", "z"))
    c.add(_make("alpha", "a"))
    doc = c.export_markdown()
    assert doc.index("[alpha]") < doc.index("[zeta]")


def test_export_markdown_sort_by_created():
    """sort_by='created' orders by creation timestamp (oldest first)."""
    c = TemplateCollection()
    c.add(_make("newer", "n", created_at="2026-01-02T00:00:00"))
    c.add(_make("older", "o", created_at="2026-01-01T00:00:00"))
    doc = c.export_markdown(sort_by="created")
    assert doc.index("[older]") < doc.index("[newer]")


def test_export_markdown_sort_by_updated():
    """sort_by='updated' orders by update timestamp."""
    c = TemplateCollection()
    c.add(_make("stale", "s", updated_at="2026-01-01T00:00:00"))
    c.add(_make("fresh", "f", updated_at="2026-02-01T00:00:00"))
    doc = c.export_markdown(sort_by="updated")
    assert doc.index("[stale]") < doc.index("[fresh]")


def test_export_markdown_unknown_sort_falls_back_to_name():
    """Unknown sort_by value falls back to name ordering (no crash)."""
    c = TemplateCollection()
    c.add(_make("b", "1"))
    c.add(_make("a", "2"))
    doc = c.export_markdown(sort_by="bogus")
    assert doc.index("[a]") < doc.index("[b]")


def test_export_markdown_tag_filter():
    """tags filter exports only templates carrying all given tags."""
    c = TemplateCollection()
    c.add(_make("a", "1", tags=["chat"]))
    c.add(_make("b", "2", tags=["code"]))
    c.add(_make("c", "3", tags=["chat", "prod"]))
    doc = c.export_markdown(tags=["chat"])
    assert "[a]" in doc and "[c]" in doc
    assert "[b]" not in doc


def test_export_markdown_tag_filter_all_semantics():
    """Multi-tag filter requires ALL tags (has_tags semantics)."""
    c = TemplateCollection()
    c.add(_make("a", "1", tags=["chat"]))
    c.add(_make("b", "2", tags=["chat", "prod"]))
    doc = c.export_markdown(tags=["chat", "prod"])
    assert "[b]" in doc
    assert "[a]" not in doc


def test_export_markdown_tag_filter_no_match():
    """Tag filter matching nothing yields the empty placeholder."""
    c = TemplateCollection()
    c.add(_make("a", "1", tags=["chat"]))
    doc = c.export_markdown(tags=["missing"])
    assert "_No templates._" in doc
    assert "[a]" not in doc


def test_export_markdown_anchor_generation():
    """Names with spaces produce hyphenated anchors."""
    c = TemplateCollection()
    c.add(_make("code review", "x"))
    doc = c.export_markdown()
    assert "- [code review](#code-review)" in doc


def test_export_markdown_includes_variables_and_description():
    """Sections carry metadata from to_markdown()."""
    c = TemplateCollection()
    c.add(_make("t", "hi {{user}}", description="says hi"))
    doc = c.export_markdown()
    assert "**Variables:** user" in doc
    assert "*says hi*" in doc

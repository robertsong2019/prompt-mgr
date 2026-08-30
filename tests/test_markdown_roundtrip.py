"""Tests for F16: Template.from_markdown() + TemplateCollection.import_markdown().

Round-trip contract: t.to_markdown() → from_markdown → equal template;
collection.export_markdown() → import_markdown → templates recovered.
"""

import pytest

from prompt_mgr.models import Template, TemplateCollection


def make_template(**overrides):
    defaults = dict(
        name="code-review",
        content="Review {{language}} code for {{focus}}.\nCheck error handling.",
        tags=["review", "quality"],
        created_at="2026-08-01T10:00:00",
        updated_at="2026-08-02T12:30:00",
        description="Structured code review prompt",
    )
    defaults.update(overrides)
    return Template(**defaults)


# --- from_markdown: round-trip fidelity ---

def test_roundtrip_full_template():
    t = make_template()
    t2 = Template.from_markdown(t.to_markdown())
    assert t2.name == t.name
    assert t2.content == t.content
    assert t2.tags == t.tags
    assert t2.description == t.description
    assert t2.created_at == t.created_at
    assert t2.updated_at == t.updated_at


def test_roundtrip_minimal_template():
    t = make_template(tags=[], description=None, created_at=None, updated_at=None)
    t2 = Template.from_markdown(t.to_markdown())
    assert t2.name == t.name
    assert t2.content == t.content
    assert t2.tags == []
    assert t2.description is None


def test_content_with_blank_lines_preserved():
    content = "line1\n\nline3\n"
    t = make_template(content=content)
    t2 = Template.from_markdown(t.to_markdown())
    assert t2.content == content


def test_content_with_hash_lines_preserved():
    content = "# not a header\n## neither is this\nbody"
    t = make_template(content=content)
    t2 = Template.from_markdown(t.to_markdown())
    assert t2.content == content


def test_variables_line_ignored_derived_from_content():
    t = make_template()
    exported = t.to_markdown()
    assert "**Variables:**" in exported
    t2 = Template.from_markdown(exported)
    assert set(t2.extract_variables()) == {"language", "focus"}


# --- from_markdown: error paths ---

def test_missing_name_header_raises():
    with pytest.raises(ValueError, match="## "):
        Template.from_markdown("just some text\nno header here")


def test_unterminated_fence_raises():
    text = "## broken\n\n```\ncontent without closing fence"
    with pytest.raises(ValueError, match="Unterminated"):
        Template.from_markdown(text)


# --- from_markdown: tolerance ---

def test_tolerates_extra_blank_lines_and_tags_formatting():
    text = (
        "## spaced\n"
        "\n"
        "**Tags:**  alpha , beta \n"
        "\n"
        "**Created:** 2026-01-01T00:00:00  \n"
        "**Updated:** 2026-01-02T00:00:00\n"
        "\n"
        "```\n"
        "hello {{who}}\n"
        "```\n"
    )
    t = Template.from_markdown(text)
    assert t.name == "spaced"
    assert t.tags == ["alpha", "beta"]
    assert t.content == "hello {{who}}"
    assert t.created_at == "2026-01-01T00:00:00"


def test_single_tag_no_comma():
    t = Template.from_markdown(
        "## solo\n\n**Tags:** onetag\n\n```\nbody\n```"
    )
    assert t.tags == ["onetag"]


# --- import_markdown: document level ---

def build_export_doc(collection):
    collection.add(make_template())
    collection.add(make_template(name="summarize", content="Summarize {{text}}",
                                 tags=["writing"], description=None))
    return collection.export_markdown()


def test_import_full_export_document():
    c = TemplateCollection()
    doc = build_export_doc(c)
    imported = c.import_markdown(doc)
    assert [t.name for t in imported] == ["code-review", "summarize"]
    assert imported[0].content == make_template().content
    assert imported[1].tags == ["writing"]


def test_import_skips_contents_section():
    c = TemplateCollection()
    doc = build_export_doc(c)
    assert "## Contents" in doc  # H2 header must not become a template
    imported = c.import_markdown(doc)
    assert "Contents" not in [t.name for t in imported]


def test_import_empty_collection_document():
    c = TemplateCollection()
    doc = c.export_markdown()
    assert "_No templates._" in doc
    assert c.import_markdown(doc) == []


def test_import_plain_text_returns_empty():
    c = TemplateCollection()
    assert c.import_markdown("nothing here at all") == []


def test_import_does_not_mutate_collection():
    c = TemplateCollection()
    doc = build_export_doc(c)
    before = set(c.templates.keys())
    c.import_markdown(doc)
    assert set(c.templates.keys()) == before


def test_imported_templates_re_add_to_fresh_collection():
    src = TemplateCollection()
    doc = build_export_doc(src)
    dst = TemplateCollection()
    for t in dst.import_markdown(doc):
        dst.add(t)
    assert dst.get("code-review") is not None
    assert dst.get("code-review").render({"language": "py", "focus": "perf"}).startswith("Review py")

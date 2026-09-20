"""Tests for prompt_mgr.models — Template and TemplateCollection."""

import pytest
from datetime import datetime

from prompt_mgr.models import Template, TemplateCollection


# --- Template ---

def test_template_defaults():
    """Template sets sensible defaults."""
    t = Template(name="test", content="hello")
    assert t.tags == []
    assert t.description is None
    assert t.created_at is not None
    assert t.updated_at is not None


def test_template_to_dict_roundtrip():
    """Template.to_dict / from_dict are symmetric."""
    t = Template(name="test", content="hi", tags=["a"], description="desc")
    d = t.to_dict()
    t2 = Template.from_dict(d)
    assert t2.name == "test"
    assert t2.content == "hi"
    assert t2.tags == ["a"]
    assert t2.description == "desc"


def test_template_from_dict_missing_optional_fields():
    """Template.from_dict handles missing optional fields."""
    d = {"name": "t", "content": "c"}
    t = Template.from_dict(d)
    assert t.tags == []
    assert t.description is None


def test_template_update_timestamp():
    """update_timestamp changes updated_at."""
    t = Template(name="t", content="c")
    old = t.updated_at
    # Force a slightly different timestamp
    t.updated_at = "2020-01-01T00:00:00"
    t.update_timestamp()
    assert t.updated_at != "2020-01-01T00:00:00"


def test_template_matches_query_name():
    """matches_query matches name."""
    t = Template(name="greeting-template", content="hi")
    assert t.matches_query("greeting") is True
    assert t.matches_query("template") is True
    assert t.matches_query("xyz") is False


def test_template_matches_query_content():
    """matches_query matches content."""
    t = Template(name="t", content="Hello World")
    assert t.matches_query("world") is True


def test_template_matches_query_description():
    """matches_query matches description."""
    t = Template(name="t", content="c", description="A useful template")
    assert t.matches_query("useful") is True


def test_template_matches_query_no_description():
    """matches_query returns False for description query when description is None."""
    t = Template(name="t", content="c")
    # query that doesn't match name or content
    assert t.matches_query("something-random") is False


def test_template_has_tags_all():
    """has_tags requires all tags to be present."""
    t = Template(name="t", content="c", tags=["python", "web", "api"])
    assert t.has_tags(["python"]) is True
    assert t.has_tags(["python", "web"]) is True
    assert t.has_tags(["python", "rust"]) is False


def test_template_has_tags_empty():
    """has_tags returns True for empty tag list."""
    t = Template(name="t", content="c", tags=[])
    assert t.has_tags([]) is True


def test_template_extract_variables():
    """extract_variables finds all {{var}} placeholders."""
    t = Template(name="t", content="Hello {{name}}, you are {{role}}")
    variables = t.extract_variables()
    assert set(variables) == {"name", "role"}


def test_template_extract_variables_dedup():
    """extract_variables deduplicates."""
    t = Template(name="t", content="{{x}} and {{x}}")
    assert t.extract_variables() == ["x"]


def test_template_extract_variables_none():
    """extract_variables returns empty list when no placeholders."""
    t = Template(name="t", content="no variables here")
    assert t.extract_variables() == []


def test_template_str():
    """__str__ produces readable output."""
    t = Template(name="t", content="c", tags=["a", "b"])
    s = str(t)
    assert "Template" in s
    assert "t" in s
    assert "a" in s


def test_template_str_no_tags():
    """__str__ shows 'no tags' when tags empty."""
    t = Template(name="t", content="c")
    s = str(t)
    assert "no tags" in s


# --- TemplateCollection ---

def test_collection_add_get():
    """add and get work correctly."""
    col = TemplateCollection()
    t = Template(name="t1", content="c1")
    col.add(t)
    assert col.get("t1") is t


def test_collection_get_nonexistent():
    """get returns None for missing template."""
    col = TemplateCollection()
    assert col.get("missing") is None


def test_collection_delete():
    """delete removes a template."""
    col = TemplateCollection()
    col.add(Template(name="t1", content="c1"))
    assert col.delete("t1") is True
    assert col.get("t1") is None


def test_collection_delete_nonexistent():
    """delete returns False for missing template."""
    col = TemplateCollection()
    assert col.delete("missing") is False


def test_collection_list_all():
    """list_all returns all templates."""
    col = TemplateCollection()
    col.add(Template(name="t1", content="c1"))
    col.add(Template(name="t2", content="c2"))
    result = col.list_all()
    assert len(result) == 2


def test_collection_list_all_empty():
    """list_all returns empty list for empty collection."""
    col = TemplateCollection()
    assert col.list_all() == []


def test_collection_search_by_query():
    """search filters by query."""
    col = TemplateCollection()
    col.add(Template(name="greeting", content="Hello"))
    col.add(Template(name="farewell", content="Goodbye"))
    results = col.search(query="hello")
    assert len(results) == 1
    assert results[0].name == "greeting"


def test_collection_search_by_tags():
    """search filters by tags."""
    col = TemplateCollection()
    col.add(Template(name="t1", content="c", tags=["python"]))
    col.add(Template(name="t2", content="c", tags=["rust"]))
    results = col.search(tags=["python"])
    assert len(results) == 1
    assert results[0].name == "t1"


def test_collection_search_by_query_and_tags():
    """search filters by both query and tags."""
    col = TemplateCollection()
    col.add(Template(name="greet", content="hello world", tags=["social"]))
    col.add(Template(name="greet2", content="hello there", tags=["formal"]))
    results = col.search(query="hello", tags=["social"])
    assert len(results) == 1
    assert results[0].name == "greet"


def test_collection_search_no_filters():
    """search with no filters returns all."""
    col = TemplateCollection()
    col.add(Template(name="t1", content="c1"))
    col.add(Template(name="t2", content="c2"))
    results = col.search()
    assert len(results) == 2


def test_collection_to_json_from_json():
    """to_json / from_json are symmetric."""
    col = TemplateCollection()
    col.add(Template(name="t1", content="c1", tags=["a"]))
    col.add(Template(name="t2", content="c2", tags=["b"]))
    json_str = col.to_json()
    col2 = TemplateCollection.from_json(json_str)
    assert len(col2.list_all()) == 2
    assert col2.get("t1").tags == ["a"]


def test_collection_from_dict_empty():
    """from_dict handles empty templates dict."""
    col = TemplateCollection.from_dict({"templates": {}})
    assert len(col.list_all()) == 0


def test_collection_from_dict_missing_templates_key():
    """from_dict REJECTS a missing 'templates' key (contract tightened 2026-09-20).

    Previously {} silently produced an empty collection — which made
    restore() overwrite the store with an empty state when handed a
    valid-JSON foreign document. The legit way to express an empty
    store is {"templates": {}}, pinned below.
    """
    with pytest.raises(ValueError):
        TemplateCollection.from_dict({})
    col = TemplateCollection.from_dict({"templates": {}})
    assert len(col.list_all()) == 0

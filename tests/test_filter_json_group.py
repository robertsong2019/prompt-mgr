"""Tests for F9 filter, F10 to_json/from_json, F11 group_by_tag."""

import json
import pytest
from prompt_mgr.models import Template, TemplateCollection


# ---------------------------------------------------------------------------
# F9: TemplateCollection.filter(predicate)
# ---------------------------------------------------------------------------

class TestFilter:
    def _make_collection(self):
        col = TemplateCollection()
        col.add(Template(name="alpha", content="Hello {{name}}", tags=["greeting", "en"]))
        col.add(Template(name="beta", content="Hola {{name}}", tags=["greeting", "es"]))
        col.add(Template(name="gamma", content="Long content " * 50, tags=["draft"]))
        return col

    def test_filter_by_tag_length(self):
        col = self._make_collection()
        result = col.filter(lambda t: len(t.tags) >= 2)
        names = sorted(t.name for t in result)
        assert names == ["alpha", "beta"]

    def test_filter_by_content_length(self):
        col = self._make_collection()
        result = col.filter(lambda t: len(t.content) > 100)
        assert len(result) == 1
        assert result[0].name == "gamma"

    def test_filter_returns_empty(self):
        col = self._make_collection()
        result = col.filter(lambda t: "nonexistent" in t.name)
        assert result == []

    def test_filter_all_match(self):
        col = self._make_collection()
        result = col.filter(lambda t: True)
        assert len(result) == 3

    def test_filter_empty_collection(self):
        col = TemplateCollection()
        result = col.filter(lambda t: True)
        assert result == []

    def test_filter_by_has_variable(self):
        col = self._make_collection()
        result = col.filter(lambda t: "name" in t.extract_variables())
        names = sorted(t.name for t in result)
        assert names == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# F10: Template.to_json() / Template.from_json()
# ---------------------------------------------------------------------------

class TestTemplateJson:
    def test_to_json_basic(self):
        t = Template(name="greet", content="Hello {{name}}", tags=["en"], description="A greeting")
        data = json.loads(t.to_json())
        assert data["name"] == "greet"
        assert data["content"] == "Hello {{name}}"
        assert data["tags"] == ["en"]
        assert data["description"] == "A greeting"

    def test_to_json_minimal(self):
        t = Template(name="x", content="plain")
        data = json.loads(t.to_json())
        assert data["name"] == "x"
        assert data["tags"] == []
        assert data["description"] is None

    def test_from_json_round_trip(self):
        t1 = Template(name="rt", content="Hi {{who}}", tags=["a", "b"], description="desc")
        json_str = t1.to_json()
        t2 = Template.from_json(json_str)
        assert t2.name == t1.name
        assert t2.content == t1.content
        assert t2.tags == t1.tags
        assert t2.description == t1.description
        assert t2.created_at == t1.created_at
        assert t2.updated_at == t1.updated_at

    def test_from_json_invalid_raises(self):
        with pytest.raises(json.JSONDecodeError):
            Template.from_json("not valid json")

    def test_from_json_missing_name_raises(self):
        with pytest.raises(KeyError):
            Template.from_json('{"content": "no name"}')


# ---------------------------------------------------------------------------
# F11: TemplateCollection.group_by_tag()
# ---------------------------------------------------------------------------

class TestGroupByTag:
    def test_basic_grouping(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="x", tags=["python", "web"]))
        col.add(Template(name="b", content="y", tags=["python", "cli"]))
        col.add(Template(name="c", content="z", tags=["web"]))
        groups = col.group_by_tag()
        assert sorted(groups["python"]) == ["a", "b"]
        assert sorted(groups["web"]) == ["a", "c"]
        assert groups["cli"] == ["b"]

    def test_untagged_templates(self):
        col = TemplateCollection()
        col.add(Template(name="tagged", content="x", tags=["foo"]))
        col.add(Template(name="bare", content="y"))
        groups = col.group_by_tag()
        assert groups["foo"] == ["tagged"]
        assert groups["__untagged__"] == ["bare"]

    def test_all_untagged(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="x"))
        col.add(Template(name="b", content="y"))
        groups = col.group_by_tag()
        assert sorted(groups["__untagged__"]) == ["a", "b"]
        assert len(groups) == 1

    def test_empty_collection(self):
        col = TemplateCollection()
        groups = col.group_by_tag()
        assert groups == {}

    def test_names_sorted_within_group(self):
        col = TemplateCollection()
        col.add(Template(name="zebra", content="x", tags=["animal"]))
        col.add(Template(name="apple", content="y", tags=["animal"]))
        col.add(Template(name="mango", content="z", tags=["animal"]))
        groups = col.group_by_tag()
        assert groups["animal"] == ["apple", "mango", "zebra"]

    def test_template_in_multiple_groups(self):
        col = TemplateCollection()
        col.add(Template(name="multi", content="x", tags=["a", "b", "c"]))
        groups = col.group_by_tag()
        assert groups["a"] == ["multi"]
        assert groups["b"] == ["multi"]
        assert groups["c"] == ["multi"]

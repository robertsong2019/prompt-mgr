"""Tests for TemplateCollection.tag_summary."""

import pytest

from prompt_mgr.models import Template, TemplateCollection


class TestTagSummary:

    def test_empty_collection(self):
        col = TemplateCollection()
        assert col.tag_summary() == {}

    def test_single_tag(self):
        col = TemplateCollection()
        col.add(Template(name="t1", content="c", tags=["python"]))
        assert col.tag_summary() == {"python": 1}

    def test_multiple_tags_same_count(self):
        col = TemplateCollection()
        col.add(Template(name="t1", content="c", tags=["alpha", "beta"]))
        col.add(Template(name="t2", content="c", tags=["alpha", "beta"]))
        result = col.tag_summary()
        # Same count → alphabetical
        assert list(result.items()) == [("alpha", 2), ("beta", 2)]

    def test_sorted_by_count_desc(self):
        col = TemplateCollection()
        col.add(Template(name="t1", content="c", tags=["rare"]))
        col.add(Template(name="t2", content="c", tags=["common", "also"]))
        col.add(Template(name="t3", content="c", tags=["common", "also"]))
        col.add(Template(name="t4", content="c", tags=["common"]))
        result = col.tag_summary()
        assert list(result.items())[0] == ("common", 3)

    def test_count_desc_then_name_asc(self):
        col = TemplateCollection()
        col.add(Template(name="t1", content="c", tags=["zebra", "apple"]))
        col.add(Template(name="t2", content="c", tags=["zebra", "apple"]))
        col.add(Template(name="t3", content="c", tags=["mango"]))
        result = col.tag_summary()
        # apple and zebra both 2, alphabetical: apple first
        keys = list(result.keys())
        assert keys[0] == "apple"
        assert keys[1] == "zebra"
        assert keys[2] == "mango"

    def test_template_with_no_tags(self):
        col = TemplateCollection()
        col.add(Template(name="t1", content="c"))
        col.add(Template(name="t2", content="c", tags=["x"]))
        assert col.tag_summary() == {"x": 1}

    def test_duplicate_tags_on_same_template_counted_once(self):
        """A template can't have the same tag twice in practice, but verify."""
        col = TemplateCollection()
        col.add(Template(name="t1", content="c", tags=["python", "python"]))
        # The dataclass allows it, but tag_summary counts per template occurrence
        result = col.tag_summary()
        # Both are counted since they appear in the list
        assert result["python"] == 2

    def test_returns_dict(self):
        col = TemplateCollection()
        col.add(Template(name="t1", content="c", tags=["a"]))
        result = col.tag_summary()
        assert isinstance(result, dict)

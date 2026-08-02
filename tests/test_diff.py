"""Tests for Template.diff(other) — F3: field-level template comparison."""

import pytest
from prompt_mgr.models import Template


class TestTemplateDiff:
    """Test Template.diff() method."""

    def test_identical_templates_empty_diff(self):
        t1 = Template(name="a", content="hello", tags=["x"], description="d")
        t2 = Template(name="a", content="hello", tags=["x"], description="d")
        assert t1.diff(t2) == {}

    def test_content_difference(self):
        t1 = Template(name="a", content="hello")
        t2 = Template(name="a", content="world")
        diff = t1.diff(t2)
        assert "content" in diff
        assert diff["content"]["self"] == "hello"
        assert diff["content"]["other"] == "world"

    def test_name_difference(self):
        t1 = Template(name="old", content="same")
        t2 = Template(name="new", content="same")
        diff = t1.diff(t2)
        assert diff["name"]["self"] == "old"
        assert diff["name"]["other"] == "new"

    def test_description_difference(self):
        t1 = Template(name="a", content="x", description="old desc")
        t2 = Template(name="a", content="x", description="new desc")
        diff = t1.diff(t2)
        assert diff["description"]["self"] == "old desc"
        assert diff["description"]["other"] == "new desc"

    def test_description_none_vs_set(self):
        t1 = Template(name="a", content="x")
        t2 = Template(name="a", content="x", description="now has one")
        diff = t1.diff(t2)
        assert diff["description"]["self"] is None
        assert diff["description"]["other"] == "now has one"

    def test_tags_added(self):
        t1 = Template(name="a", content="x", tags=["python"])
        t2 = Template(name="a", content="x", tags=["python", "ai", "ml"])
        diff = t1.diff(t2)
        assert diff["tags"]["added"] == ["ai", "ml"]
        assert diff["tags"]["removed"] == []

    def test_tags_removed(self):
        t1 = Template(name="a", content="x", tags=["python", "ai"])
        t2 = Template(name="a", content="x", tags=["python"])
        diff = t1.diff(t2)
        assert diff["tags"]["added"] == []
        assert diff["tags"]["removed"] == ["ai"]

    def test_tags_added_and_removed(self):
        t1 = Template(name="a", content="x", tags=["python", "old"])
        t2 = Template(name="a", content="x", tags=["python", "new"])
        diff = t1.diff(t2)
        assert diff["tags"]["added"] == ["new"]
        assert diff["tags"]["removed"] == ["old"]

    def test_tags_order_independent(self):
        t1 = Template(name="a", content="x", tags=["a", "b", "c"])
        t2 = Template(name="a", content="x", tags=["c", "b", "a"])
        diff = t1.diff(t2)
        assert "tags" not in diff

    def test_tags_both_empty(self):
        t1 = Template(name="a", content="x")
        t2 = Template(name="a", content="x")
        diff = t1.diff(t2)
        assert "tags" not in diff

    def test_multiple_field_differences(self):
        t1 = Template(name="old", content="hello", tags=["a"], description="d1")
        t2 = Template(name="new", content="world", tags=["b"], description="d2")
        diff = t1.diff(t2)
        assert set(diff.keys()) == {"name", "content", "description", "tags"}

    def test_empty_templates(self):
        t1 = Template(name="", content="")
        t2 = Template(name="", content="")
        assert t1.diff(t2) == {}

    def test_returns_dict_type(self):
        t1 = Template(name="a", content="x")
        t2 = Template(name="a", content="x")
        result = t1.diff(t2)
        assert isinstance(result, dict)

    def test_tags_sorted_in_result(self):
        t1 = Template(name="a", content="x", tags=["z", "y", "x"])
        t2 = Template(name="a", content="x", tags=[])
        diff = t1.diff(t2)
        assert diff["tags"]["removed"] == ["x", "y", "z"]

    def test_diff_does_not_modify_either_template(self):
        t1 = Template(name="a", content="x", tags=["python"])
        t2 = Template(name="a", content="y", tags=["java"])
        t1_tags_before = list(t1.tags)
        t2_tags_before = list(t2.tags)
        t1_content_before = t1.content
        t2_content_before = t2.content
        t1.diff(t2)
        assert t1.tags == t1_tags_before
        assert t2.tags == t2_tags_before
        assert t1.content == t1_content_before
        assert t2.content == t2_content_before

    def test_diff_is_directional(self):
        """diff(a, b) should mirror diff(b, a) for self/other."""
        t1 = Template(name="a", content="x", tags=["python"])
        t2 = Template(name="b", content="y", tags=["java"])
        d1 = t1.diff(t2)
        d2 = t2.diff(t1)
        assert d1["name"]["self"] == d2["name"]["other"]
        assert d1["name"]["other"] == d2["name"]["self"]
        assert d1["tags"]["added"] == d2["tags"]["removed"]
        assert d1["tags"]["removed"] == d2["tags"]["added"]

    def test_ignores_timestamps(self):
        """diff should not report timestamp differences (transient metadata)."""
        t1 = Template(name="a", content="x", created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00")
        t2 = Template(name="a", content="x", created_at="2026-06-01T12:00:00", updated_at="2026-06-01T12:00:00")
        diff = t1.diff(t2)
        assert diff == {}

    def test_only_timestamps_differ(self):
        """If only timestamps differ, diff is empty."""
        t1 = Template(name="a", content="x", created_at="2020-01-01", updated_at="2020-01-01")
        t2 = Template(name="a", content="x", created_at="2026-08-02", updated_at="2026-08-02")
        assert t1.diff(t2) == {}

    def test_content_whitespace_difference(self):
        t1 = Template(name="a", content="hello world")
        t2 = Template(name="a", content="hello  world")  # double space
        diff = t1.diff(t2)
        assert "content" in diff

    def test_large_content_difference(self):
        t1 = Template(name="a", content="x" * 10000)
        t2 = Template(name="a", content="y" * 10000)
        diff = t1.diff(t2)
        assert diff["content"]["self"] == "x" * 10000
        assert diff["content"]["other"] == "y" * 10000

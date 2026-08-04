"""Tests for TemplateCollection.sort_by and TemplateCollection.merge."""

import pytest
from prompt_mgr.models import Template, TemplateCollection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make(name, content="hello", tags=None, desc=None):
    """Quick template factory."""
    return Template(
        name=name,
        content=content,
        tags=tags or [],
        description=desc,
    )


def _filled_collection():
    """Collection with 3 templates for sorting tests."""
    col = TemplateCollection()
    col.add(_make("zebra", "aaa", tags=["x"]))
    col.add(_make("apple", "bb", tags=["x", "y"]))
    col.add(_make("mango", "cccc", tags=[]))
    return col


# ===========================================================================
# F5: sort_by
# ===========================================================================

class TestSortBy:

    def test_sort_by_name_asc(self):
        col = _filled_collection()
        result = col.sort_by("name")
        names = [t.name for t in result]
        assert names == ["apple", "mango", "zebra"]

    def test_sort_by_name_desc(self):
        col = _filled_collection()
        result = col.sort_by("name", reverse=True)
        names = [t.name for t in result]
        assert names == ["zebra", "mango", "apple"]

    def test_sort_by_content_length(self):
        col = _filled_collection()
        result = col.sort_by("content_length")
        lengths = [len(t.content) for t in result]
        assert lengths == sorted(lengths)
        # ascending: bb(2) < aaa(3) < cccc(4)
        assert [t.name for t in result] == ["apple", "zebra", "mango"]

    def test_sort_by_content_length_desc(self):
        col = _filled_collection()
        result = col.sort_by("content_length", reverse=True)
        lengths = [len(t.content) for t in result]
        assert lengths == sorted(lengths, reverse=True)

    def test_sort_by_tag_count(self):
        col = _filled_collection()
        result = col.sort_by("tag_count")
        counts = [len(t.tags) for t in result]
        assert counts == sorted(counts)
        # mango(0) < zebra(1) < apple(2)
        assert [t.name for t in result] == ["mango", "zebra", "apple"]

    def test_sort_by_created_at(self):
        col = TemplateCollection()
        t1 = _make("old")
        t1.created_at = "2020-01-01T00:00:00"
        t2 = _make("new")
        t2.created_at = "2025-01-01T00:00:00"
        col.add(t2)
        col.add(t1)
        result = col.sort_by("created_at")
        assert [t.name for t in result] == ["old", "new"]

    def test_sort_by_updated_at_desc(self):
        col = TemplateCollection()
        t1 = _make("a")
        t1.updated_at = "2020-01-01"
        t2 = _make("b")
        t2.updated_at = "2025-01-01"
        col.add(t1)
        col.add(t2)
        result = col.sort_by("updated_at", reverse=True)
        assert [t.name for t in result] == ["b", "a"]

    def test_sort_invalid_field_raises(self):
        col = _filled_collection()
        with pytest.raises(ValueError, match="Invalid sort field"):
            col.sort_by("nonexistent")

    def test_sort_empty_collection(self):
        col = TemplateCollection()
        assert col.sort_by("name") == []

    def test_sort_single_element(self):
        col = TemplateCollection()
        col.add(_make("only"))
        result = col.sort_by("name")
        assert len(result) == 1
        assert result[0].name == "only"

    def test_sort_does_not_mutate_original(self):
        col = _filled_collection()
        original_order = list(col.templates.keys())
        col.sort_by("name")
        # Internal dict order unchanged
        assert list(col.templates.keys()) == original_order

    def test_sort_by_name_with_duplicate_names_impossible(self):
        """Names are dict keys so duplicates can't exist — just verify stability."""
        col = _filled_collection()
        result = col.sort_by("name")
        assert len(result) == 3


# ===========================================================================
# F6: merge
# ===========================================================================

class TestMerge:

    def test_merge_adds_new_templates(self):
        col_a = TemplateCollection()
        col_a.add(_make("alpha"))
        col_a.add(_make("beta"))

        col_b = TemplateCollection()
        col_b.add(_make("gamma"))
        col_b.add(_make("delta"))

        result = col_a.merge(col_b)

        assert sorted(result["added"]) == ["delta", "gamma"]
        assert result["skipped"] == []
        assert col_a.get("gamma") is not None
        assert col_a.get("delta") is not None

    def test_merge_skips_existing(self):
        col_a = TemplateCollection()
        col_a.add(_make("shared", content="from_a"))

        col_b = TemplateCollection()
        col_b.add(_make("shared", content="from_b"))
        col_b.add(_make("new_one"))

        result = col_a.merge(col_b)

        assert result["added"] == ["new_one"]
        assert result["skipped"] == ["shared"]
        # Self's version preserved
        assert col_a.get("shared").content == "from_a"

    def test_merge_empty_other(self):
        col_a = _filled_collection()
        col_b = TemplateCollection()
        result = col_a.merge(col_b)
        assert result == {"added": [], "skipped": []}

    def test_merge_into_empty(self):
        col_a = TemplateCollection()
        col_b = TemplateCollection()
        col_b.add(_make("x"))
        col_b.add(_make("y"))
        result = col_a.merge(col_b)
        assert sorted(result["added"]) == ["x", "y"]
        assert result["skipped"] == []
        assert len(col_a.templates) == 2

    def test_merge_both_empty(self):
        result = TemplateCollection().merge(TemplateCollection())
        assert result == {"added": [], "skipped": []}

    def test_merge_preserves_template_data(self):
        col_a = TemplateCollection()
        col_b = TemplateCollection()
        col_b.add(_make("rich", content="{{var}}", tags=["a", "b"], desc="info"))

        col_a.merge(col_b)

        t = col_a.get("rich")
        assert t.content == "{{var}}"
        assert t.tags == ["a", "b"]
        assert t.description == "info"

    def test_merge_all_conflict(self):
        col_a = TemplateCollection()
        col_a.add(_make("x"))
        col_a.add(_make("y"))
        col_b = TemplateCollection()
        col_b.add(_make("x"))
        col_b.add(_make("y"))

        result = col_a.merge(col_b)
        assert result["added"] == []
        assert sorted(result["skipped"]) == ["x", "y"]

    def test_merge_partial_conflict(self):
        col_a = TemplateCollection()
        col_a.add(_make("keep"))
        col_a.add(_make("also_keep"))

        col_b = TemplateCollection()
        col_b.add(_make("keep", content="other"))  # conflict
        col_b.add(_make("new1"))                    # new
        col_b.add(_make("new2"))                    # new

        result = col_a.merge(col_b)
        assert sorted(result["added"]) == ["new1", "new2"]
        assert result["skipped"] == ["keep"]

    def test_merge_return_keys_always_sorted(self):
        col_a = TemplateCollection()
        col_b = TemplateCollection()
        for name in ["z", "a", "m", "b"]:
            col_b.add(_make(name))

        result = col_a.merge(col_b)
        assert result["added"] == ["a", "b", "m", "z"]

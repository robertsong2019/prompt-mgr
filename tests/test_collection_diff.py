"""Tests for TemplateCollection.diff (F17)."""

from prompt_mgr.models import Template, TemplateCollection


def _tpl(name, content="c", tags=None, description=None):
    return Template(name=name, content=content, tags=tags or [], description=description)


def test_diff_identical_collections():
    """Identical collections produce empty diff."""
    a = TemplateCollection()
    a.add(_tpl("t1", "same"))
    a.add(_tpl("t2", "same2", tags=["x"]))
    b = TemplateCollection()
    b.add(_tpl("t1", "same"))
    b.add(_tpl("t2", "same2", tags=["x"]))
    d = a.diff(b)
    assert d["added"] == []
    assert d["removed"] == []
    assert d["changed"] == {}


def test_diff_added_removed():
    """Names only in other = added; only in self = removed (sorted)."""
    a = TemplateCollection()
    a.add(_tpl("keep"))
    a.add(_tpl("gone"))
    b = TemplateCollection()
    b.add(_tpl("keep"))
    b.add(_tpl("new"))
    d = a.diff(b)
    assert d["added"] == ["new"]
    assert d["removed"] == ["gone"]
    assert d["changed"] == {}


def test_diff_changed_content():
    """Same name, different content reported under changed with Template.diff shape."""
    a = TemplateCollection()
    a.add(_tpl("t1", "old content"))
    b = TemplateCollection()
    b.add(_tpl("t1", "new content"))
    d = a.diff(b)
    assert d["changed"]["t1"]["content"] == {"self": "old content", "other": "new content"}


def test_diff_changed_tags():
    """Tag changes use added/removed shape."""
    a = TemplateCollection()
    a.add(_tpl("t1", "c", tags=["red", "blue"]))
    b = TemplateCollection()
    b.add(_tpl("t1", "c", tags=["red", "green"]))
    d = a.diff(b)
    assert d["changed"]["t1"]["tags"] == {"added": ["green"], "removed": ["blue"]}


def test_diff_added_and_changed_mixed():
    """Mixed diff: added + removed + changed all at once."""
    a = TemplateCollection()
    a.add(_tpl("same"))
    a.add(_tpl("mod", "v1"))
    a.add(_tpl("drop"))
    b = TemplateCollection()
    b.add(_tpl("same"))
    b.add(_tpl("mod", "v2"))
    b.add(_tpl("fresh"))
    d = a.diff(b)
    assert d["added"] == ["fresh"]
    assert d["removed"] == ["drop"]
    assert set(d["changed"].keys()) == {"mod"}


def test_diff_empty_self():
    """Empty self: everything in other is added."""
    a = TemplateCollection()
    b = TemplateCollection()
    b.add(_tpl("t1"))
    b.add(_tpl("t2"))
    d = a.diff(b)
    assert d["added"] == ["t1", "t2"]
    assert d["removed"] == []
    assert d["changed"] == {}


def test_diff_both_empty():
    """Two empty collections: empty diff."""
    d = TemplateCollection().diff(TemplateCollection())
    assert d == {"added": [], "removed": [], "changed": {}}


def test_diff_ignores_timestamps_and_description_none_vs_none():
    """Timestamps differ between fresh instances but must not count as changes."""
    a = TemplateCollection()
    a.add(_tpl("t1", "c"))
    b = TemplateCollection()
    b.add(_tpl("t1", "c"))
    d = a.diff(b)
    assert d["changed"] == {}


def test_diff_description_change():
    """Description-only change detected."""
    a = TemplateCollection()
    a.add(_tpl("t1", "c", description="old desc"))
    b = TemplateCollection()
    b.add(_tpl("t1", "c", description="new desc"))
    d = a.diff(b)
    assert d["changed"]["t1"]["description"] == {"self": "old desc", "other": "new desc"}


def test_diff_added_sorted():
    """added/removed lists are sorted for deterministic output."""
    a = TemplateCollection()
    a.add(_tpl("b"))
    a.add(_tpl("a"))
    b = TemplateCollection()
    b.add(_tpl("z"))
    b.add(_tpl("a"))
    b.add(_tpl("m"))
    d = a.diff(b)
    assert d["added"] == ["m", "z"]
    assert d["removed"] == ["b"]

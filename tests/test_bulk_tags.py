"""Tests for PromptManager.bulk_add_tags / bulk_remove_tags — F21."""

import pytest

from prompt_mgr.manager import PromptManager


@pytest.fixture
def mgr(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    m = PromptManager()
    m.add_template("a", "content a", tags=["core"])
    m.add_template("b", "content b", tags=[])
    m.add_template("c", "content c", tags=["old"])
    return m


# ---------- bulk_add_tags ----------

def test_bulk_add_basic(mgr):
    """Tags land on every existing template."""
    res = mgr.bulk_add_tags(["a", "b"], ["prod", "v2"])
    assert res == {"updated": ["a", "b"], "missing": []}
    assert mgr.get_template("a").tags == ["core", "prod", "v2"]
    assert mgr.get_template("b").tags == ["prod", "v2"]


def test_bulk_add_missing_reported_not_raised(mgr):
    """Unknown names go to `missing`; batch continues (no ValueError)."""
    res = mgr.bulk_add_tags(["a", "ghost"], ["x"])
    assert res["updated"] == ["a"]
    assert res["missing"] == ["ghost"]


def test_bulk_add_idempotent_no_updated(mgr):
    """Template that already has all tags is not listed as updated."""
    res = mgr.bulk_add_tags(["a"], ["core"])
    assert res == {"updated": [], "missing": []}


def test_bulk_add_idempotent_no_timestamp_touch(mgr):
    """No-op add must not bump updated_at."""
    before = mgr.get_template("a").updated_at
    mgr.bulk_add_tags(["a"], ["core"])
    assert mgr.get_template("a").updated_at == before


def test_bulk_add_mixed_new_and_existing_tags(mgr):
    """Template with one new + one existing tag counts as updated, no dup tag."""
    res = mgr.bulk_add_tags(["a"], ["core", "new"])
    assert res["updated"] == ["a"]
    assert mgr.get_template("a").tags.count("core") == 1


def test_bulk_add_persists(mgr, tmp_path):
    """Changes survive a fresh manager instance (save called once at end)."""
    mgr.bulk_add_tags(["b"], ["saved"])
    m2 = PromptManager()
    assert "saved" in m2.get_template("b").tags


# ---------- bulk_remove_tags ----------

def test_bulk_remove_basic(mgr):
    """Tags removed from every existing template."""
    mgr.bulk_add_tags(["a", "b"], ["junk"])
    res = mgr.bulk_remove_tags(["a", "b"], ["junk"])
    assert res == {"updated": ["a", "b"], "missing": []}
    assert "junk" not in mgr.get_template("a").tags
    assert mgr.get_template("b").tags == []


def test_bulk_remove_missing_template(mgr):
    """Unknown template reported, no raise."""
    res = mgr.bulk_remove_tags(["ghost"], ["core"])
    assert res == {"updated": [], "missing": ["ghost"]}


def test_bulk_remove_tag_not_present(mgr):
    """Removing a tag the template doesn't have is a no-op for it."""
    res = mgr.bulk_remove_tags(["b"], ["core"])
    assert res == {"updated": [], "missing": []}


def test_bulk_remove_no_timestamp_touch(mgr):
    """No-op remove must not bump updated_at."""
    before = mgr.get_template("b").updated_at
    mgr.bulk_remove_tags(["b"], ["core"])
    assert mgr.get_template("b").updated_at == before


def test_bulk_remove_persists(mgr):
    """Removal survives a fresh manager instance."""
    mgr.bulk_remove_tags(["a"], ["core"])
    m2 = PromptManager()
    assert "core" not in m2.get_template("a").tags

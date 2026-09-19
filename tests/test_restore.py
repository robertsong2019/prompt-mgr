"""Tests for F26 PromptManager.list_snapshots() + restore() + CLI.

Closes the F25 export-only gap: snapshot() produced backups nothing could
read back. list_snapshots() inventories them, restore() rolls the store
back — with an automatic safety snapshot so restore itself is reversible.
"""

import json
import os
import re
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from prompt_mgr.models import Template
from prompt_mgr.manager import PromptManager
from prompt_mgr.cli import main


@pytest.fixture
def manager(tmp_path):
    templates_file = tmp_path / "templates.json"
    with patch("prompt_mgr.manager.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_data_dir", return_value=tmp_path):
        mgr = PromptManager()
        mgr.templates_file = templates_file
        return mgr


@pytest.fixture
def runner(tmp_path):
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    yield CliRunner()
    del os.environ["PROMPT_MGR_DATA_DIR"]


# --- list_snapshots() ---

def test_list_snapshots_empty_when_no_dir(manager):
    """No snapshots directory at all -> empty list, not an error."""
    assert manager.list_snapshots() == []


def test_list_snapshots_returns_entry(manager):
    """One snapshot -> one entry with name/path/size/modified."""
    manager.add_template("greet", "Hello {{name}}!")
    dest = manager.snapshot()
    entries = manager.list_snapshots()
    assert len(entries) == 1
    e = entries[0]
    assert e["name"] == dest.name
    assert e["path"] == dest
    assert e["size_bytes"] == dest.stat().st_size
    assert e["modified"] is not None


def test_list_snapshots_ignores_foreign_files(manager, tmp_path):
    """Files not matching templates-*.json are not listed."""
    manager.add_template("greet", "Hi")
    manager.snapshot()
    snap_dir = tmp_path / "snapshots"
    (snap_dir / "notes.txt").write_text("not a snapshot")
    (snap_dir / "stray.json").write_text("{}")
    names = [e["name"] for e in manager.list_snapshots()]
    assert len(names) == 1
    assert names[0].startswith("templates-")


def test_list_snapshots_newest_first(manager, tmp_path):
    """Multiple snapshots ordered newest-first by mtime."""
    manager.add_template("a", "A")
    s1 = manager.snapshot()
    manager.add_template("b", "B")
    s2 = manager.snapshot()
    # Force distinct, reversed mtimes to prove ordering is mtime-driven
    old, new = 1_000_000, 2_000_000
    os.utime(s1, (new, new))
    os.utime(s2, (old, old))
    names = [e["name"] for e in manager.list_snapshots()]
    assert names == [s1.name, s2.name]


# --- restore() ---

def test_restore_rolls_back_store(manager):
    """snapshot -> mutate -> restore: mutation gone from memory AND disk."""
    manager.add_template("greet", "Hello {{name}}!")
    snap = manager.snapshot()
    manager.add_template("oops", "added after snapshot")
    report = manager.restore(snap.name)
    assert manager.collection.get("oops") is None
    assert manager.collection.get("greet") is not None
    on_disk = json.loads(manager.templates_file.read_text())
    assert "oops" not in on_disk["templates"]
    assert report["restored"] == 1


def test_restore_missing_snapshot_raises(manager):
    with pytest.raises(FileNotFoundError):
        manager.restore("templates-19990101-000000.json")


@pytest.mark.parametrize("bad", ["", "../evil.json", "sub/dir.json", ".."])
def test_restore_rejects_traversal_names(manager, bad):
    """Snapshot names must stay inside snapshots/ (path-traversal guard)."""
    with pytest.raises(ValueError):
        manager.restore(bad)


def test_restore_corrupt_snapshot_leaves_store_untouched(manager, tmp_path):
    """Corrupt JSON raises; in-memory collection and store file unchanged."""
    manager.add_template("greet", "Hello")
    snap = manager.snapshot()
    snap.write_text("{ not valid json")
    before = manager.templates_file.read_text()
    with pytest.raises(json.JSONDecodeError):
        manager.restore(snap.name)
    assert manager.collection.get("greet") is not None
    assert manager.templates_file.read_text() == before


def test_restore_takes_safety_snapshot_first(manager, tmp_path):
    """restore() snapshots CURRENT state before overwriting -> reversible."""
    manager.add_template("old", "before snapshot")
    snap = manager.snapshot()
    manager.add_template("new", "after snapshot")
    report = manager.restore(snap.name)
    safety = tmp_path / "snapshots" / report["safety_snapshot"]
    assert safety.exists()
    # Safety copy must contain the pre-restore state (incl. "new"),
    # proving it differs from the restore target (which lacks "new")
    safety_data = json.loads(safety.read_text())
    assert "new" in safety_data["templates"]


def test_restore_report_fields(manager):
    manager.add_template("a", "A")
    snap = manager.snapshot()
    report = manager.restore(snap.name)
    assert set(report) == {"restored", "snapshot", "safety_snapshot"}
    assert report["snapshot"] == str(snap)


# --- CLI ---

def test_cli_snapshots_table(runner, manager):
    manager.add_template("greet", "Hi")
    dest = manager.snapshot()
    result = runner.invoke(main, ["snapshots"])
    assert result.exit_code == 0
    assert dest.name in result.output


def test_cli_snapshots_empty_message(runner):
    result = runner.invoke(main, ["snapshots"])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_cli_restore_happy_path(runner, manager):
    manager.add_template("greet", "Hello {{name}}!")
    snap = manager.snapshot()
    manager.add_template("oops", "post-snap")
    result = runner.invoke(main, ["restore", snap.name])
    assert result.exit_code == 0
    assert "Restored 1 template(s)" in result.output
    data = json.loads(manager.templates_file.read_text())
    assert "oops" not in data["templates"]


def test_cli_restore_missing_fails(runner):
    result = runner.invoke(main, ["restore", "templates-19990101-000000.json"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()

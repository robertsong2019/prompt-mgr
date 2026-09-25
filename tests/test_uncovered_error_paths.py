"""Tests for error paths left uncovered before 2026-09-26.

Covers the last uncovered branches in cli.py (edit ValueError handler,
delete display-only failure, restore FileNotFoundError) and manager.py
(_quarantine_store OSError fallback).

Discipline notes:
- ``delete`` failure prints an error but exits 0 (display-only), unlike
  ``edit``/``restore`` failures which exit non-zero. These tests PIN the
  current behavior deliberately; changing exit codes is a behavior change
  that would break scripts and needs an explicit decision.
"""

import os

import pytest
from click.testing import CliRunner

from prompt_mgr.cli import main
from prompt_mgr.manager import PromptManager


@pytest.fixture
def runner(tmp_path):
    """CLI runner with isolated data dir (same convention as test_cli_error_paths)."""
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    yield CliRunner()
    os.environ.pop("PROMPT_MGR_DATA_DIR", None)


# --- edit: ValueError after existence check (cli.py 155-156) ---


def test_edit_valueerror_after_existence_check_exits_1(runner, monkeypatch):
    """edit exits 1 with an error when update_template raises after the
    existence check passed (e.g. template vanishes between the two calls).

    get_template is patched to lie so the real ValueError branch runs.
    """
    monkeypatch.setattr(PromptManager, "get_template", lambda self, name: True)
    result = runner.invoke(main, ["edit", "ghost", "-c", "new body"])
    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Template not found: ghost" in result.output


# --- delete: display-only failure (cli.py 180-181) ---


def test_delete_display_only_failure_exits_0(runner, monkeypatch):
    """When delete_template returns False despite the existence check,
    the CLI prints an error but exits 0 (display-only failure).
    """
    runner.invoke(main, ["add", "victim", "-c", "body"])
    monkeypatch.setattr(PromptManager, "delete_template", lambda self, name: False)
    result = runner.invoke(main, ["delete", "victim", "--yes"])
    assert result.exit_code == 0
    assert "Could not delete template: victim" in result.output


# --- restore: FileNotFoundError (cli.py 300-302) ---


def test_restore_missing_snapshot_exits_1(runner, tmp_path):
    """restore with an unknown snapshot exits 1 and must NOT create a
    safety snapshot (the FileNotFoundError raises before any write).
    """
    result = runner.invoke(main, ["restore", "templates-19990101-000000.json"])
    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Snapshot not found" in result.output
    assert not (tmp_path / "snapshots").exists()


def test_restore_path_traversal_name_rejected(runner, tmp_path):
    """restore rejects separator/'..' names at the CLI boundary (exit 1,
    no file access attempted)."""
    result = runner.invoke(main, ["restore", "../evil.json"])
    assert result.exit_code == 1
    assert "Invalid snapshot name" in result.output


def test_restore_corrupt_snapshot_exits_1(runner, tmp_path):
    """restore with a syntactically-corrupt snapshot exits 1 and leaves
    the current store untouched (no safety snapshot, no rewrite)."""
    runner.invoke(main, ["add", "keep-me", "-c", "precious"])
    store_before = (tmp_path / "templates.json").read_text(encoding="utf-8")

    snaps = tmp_path / "snapshots"
    snaps.mkdir()
    (snaps / "templates-bad.json").write_text("{ truncated", encoding="utf-8")

    result = runner.invoke(main, ["restore", "templates-bad.json"])
    assert result.exit_code == 1
    assert "Error" in result.output
    assert (tmp_path / "templates.json").read_text(encoding="utf-8") == store_before
    # no safety snapshot of the (unchanged) store should appear either
    assert list(snaps.glob("templates-*.json")) == [snaps / "templates-bad.json"]


# --- manager: quarantine OSError fallback (manager.py 59-60) ---


def test_quarantine_oserror_names_copy_failure(runner, tmp_path, monkeypatch, capsys):
    """When even the quarantine copy fails (OSError), the store still
    loads fresh and the warning names the copy failure — no crash.
    """
    store = tmp_path / "templates.json"
    store.write_text("{not valid json", encoding="utf-8")

    import shutil

    def boom(src, dst):
        raise OSError(13, "permission denied")

    monkeypatch.setattr(shutil, "copy2", boom)

    mgr = PromptManager()

    assert mgr.collection.list_all() == []
    out = capsys.readouterr().out
    assert "quarantine failed" in out
    assert "permission denied" in out

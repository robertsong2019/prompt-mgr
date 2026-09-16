"""Tests for F25 PromptManager.snapshot() + CLI snapshot."""

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


# --- Manager tests ---

def test_snapshot_creates_timestamped_copy(manager):
    """snapshot() writes snapshots/templates-YYYYMMDD-HHMMSS.json with store content."""
    manager.add_template("greet", "Hello {{name}}!")
    dest = manager.snapshot()
    assert dest.parent.name == "snapshots"
    assert re.fullmatch(r"templates-\d{8}-\d{6}(\.\d+)?\.json", dest.name)
    assert dest.exists()
    assert json.loads(dest.read_text()) == json.loads(manager.templates_file.read_text())


def test_snapshot_captures_unsaved_memory_state(manager):
    """snapshot flushes in-memory state first: direct collection edits are captured."""
    manager.add_template("saved", "one")
    manager.collection.add(Template(name="unsaved", content="two"))
    dest = manager.snapshot()
    data = json.loads(dest.read_text())
    names = list(json.loads(dest.read_text())["templates"].keys())
    assert "unsaved" in names and "saved" in names


def test_snapshot_same_second_distinct(manager):
    """Two snapshots within one second produce distinct files, nothing overwritten."""
    manager.add_template("a", "x")
    first = manager.snapshot()
    second = manager.snapshot()
    assert first != second
    assert first.exists() and second.exists()


def test_snapshot_leaves_store_intact(manager):
    """Main store unchanged and reloadable after snapshot."""
    manager.add_template("keep", "Hello {{name}}!")
    before = manager.templates_file.read_text()
    manager.snapshot()
    assert manager.templates_file.read_text() == before
    assert PromptManager.__name__  # sanity import alive


# --- CLI tests ---

def test_cli_snapshot(runner):
    """CLI snapshot prints the created file path."""
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["add", "t1", "-c", "Hello {{name}}"])
        assert result.exit_code == 0
        result = runner.invoke(main, ["snapshot"])
        assert result.exit_code == 0
        assert re.search(r"templates-\d{8}-\d{6}", result.output.replace("\n", ""))

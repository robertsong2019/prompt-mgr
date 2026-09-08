"""Tests for F18: PromptManager.render_to_file + CLI render --output."""

import os
import uuid
import pytest
from pathlib import Path

from click.testing import CliRunner

from prompt_mgr.manager import PromptManager
from prompt_mgr.cli import main


@pytest.fixture
def manager(tmp_path):
    """Manager with isolated data dir."""
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path / "data")
    try:
        mgr = PromptManager()
        mgr.add_template("greet", "Hello {{name}}, welcome to {{place}}!", tags=["t"])
        yield mgr
    finally:
        del os.environ["PROMPT_MGR_DATA_DIR"]


VARS = {"name": "Alice", "place": "Wonderland"}


# --- manager level ---

def test_render_to_file_basic(manager, tmp_path):
    """Renders content into the file and returns the Path."""
    out = tmp_path / "out.txt"
    result = manager.render_to_file("greet", VARS, out)
    assert result == out
    assert out.read_text(encoding="utf-8") == "Hello Alice, welcome to Wonderland!"


def test_render_to_file_creates_nested_dirs(manager, tmp_path):
    """Parent directories are created automatically."""
    out = tmp_path / "a" / "b" / "out.txt"
    manager.render_to_file("greet", VARS, out)
    assert out.read_text(encoding="utf-8") == "Hello Alice, welcome to Wonderland!"


def test_render_to_file_overwrites(manager, tmp_path):
    """Existing file content is replaced, not appended."""
    out = tmp_path / "out.txt"
    out.write_text("STALE CONTENT", encoding="utf-8")
    manager.render_to_file("greet", VARS, out)
    assert out.read_text(encoding="utf-8") == "Hello Alice, welcome to Wonderland!"


def test_render_to_file_unicode(manager, tmp_path):
    """Unicode variable values round-trip intact."""
    out = tmp_path / "out.txt"
    manager.render_to_file("greet", {"name": "罗嵩", "place": "上海"},
                           out)
    assert "罗嵩" in out.read_text(encoding="utf-8")
    assert "上海" in out.read_text(encoding="utf-8")


def test_render_to_file_missing_vars_no_file(manager, tmp_path):
    """Missing variables raise ValueError and leave no file behind."""
    out = tmp_path / "out.txt"
    with pytest.raises(ValueError, match="Missing variables"):
        manager.render_to_file("greet", {"name": "Alice"}, out)
    assert not out.exists()


def test_render_to_file_unknown_template(manager, tmp_path):
    """Unknown template raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        manager.render_to_file("nope-xyz", VARS, tmp_path / "out.txt")


# --- CLI level ---

@pytest.fixture
def runner(tmp_path):
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path / "data")
    yield CliRunner()
    del os.environ["PROMPT_MGR_DATA_DIR"]


def _add_greet(runner):
    result = runner.invoke(main, [
        "add", "greet", "--content", "Hello {{name}} from {{place}}!",
    ])
    assert result.exit_code == 0


def test_cli_render_output_writes_file(runner, tmp_path):
    """--output writes the file and prints confirmation, not the content."""
    _add_greet(runner)
    out = tmp_path / "rendered.txt"
    result = runner.invoke(main, [
        "render", "greet", "--vars", "name=Bob,place=Paris",
        "--output", str(out),
    ])
    assert result.exit_code == 0
    assert "Hello Bob from Paris!" not in result.output
    assert out.read_text(encoding="utf-8") == "Hello Bob from Paris!"


def test_cli_render_without_output_still_panels(runner):
    """Backward compat: no --output keeps stdout rendering."""
    _add_greet(runner)
    result = runner.invoke(main, [
        "render", "greet", "--vars", "name=Bob,place=Paris",
    ])
    assert result.exit_code == 0
    assert "Hello Bob from Paris!" in result.output


def test_cli_render_output_missing_vars_fails(runner, tmp_path):
    """--output with missing variables errors out and writes nothing."""
    _add_greet(runner)
    out = tmp_path / "rendered.txt"
    result = runner.invoke(main, [
        "render", "greet", "--vars", "name=Bob",
        "--output", str(out),
    ])
    assert result.exit_code != 0
    assert not out.exists()

"""Tests for CLI error paths and edge cases."""

import os
import json
import pytest
from click.testing import CliRunner
from prompt_mgr.cli import main


@pytest.fixture
def runner(tmp_path):
    """Create a CLI runner with isolated data dir."""
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    yield CliRunner()
    del os.environ["PROMPT_MGR_DATA_DIR"]


# --- list command ---

def test_list_empty(runner):
    """list with no templates shows 'No templates found'."""
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_list_json_empty(runner):
    """list --format json with no templates."""
    result = runner.invoke(main, ["list", "--format", "json"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_list_by_tag_no_match(runner):
    """list --tags with a tag that has no matches."""
    runner.invoke(main, ["add", "t1", "-c", "hello"])
    result = runner.invoke(main, ["list", "-t", "nonexistent"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_list_json_with_data(runner):
    """list --format json returns valid JSON when templates exist."""
    runner.invoke(main, ["add", "json-t1", "-c", "content"])
    result = runner.invoke(main, ["list", "-f", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    names = [t["name"] for t in data]
    assert "json-t1" in names


def test_list_json_multiple(runner):
    """list --format json with multiple templates."""
    runner.invoke(main, ["add", "a1", "-c", "first"])
    runner.invoke(main, ["add", "a2", "-c", "second"])
    result = runner.invoke(main, ["list", "-f", "json"])
    data = json.loads(result.output)
    assert len(data) == 2


def test_list_table_default(runner):
    """list default format (table) shows template names."""
    runner.invoke(main, ["add", "tbl-t1", "-c", "content"])
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "tbl-t1" in result.output


# --- search command ---

def test_search_empty(runner):
    """search with no templates shows 'No templates found'."""
    result = runner.invoke(main, ["search"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_search_no_match(runner):
    """search with no matching results."""
    runner.invoke(main, ["add", "abc", "-c", "hello world"])
    result = runner.invoke(main, ["search", "zzzzz"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_search_by_tag_no_match(runner):
    """search --tags with non-matching tag."""
    runner.invoke(main, ["add", "t1", "-c", "hello"])
    result = runner.invoke(main, ["search", "-t", "nonexistent"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_search_with_match(runner):
    """search finds matching template."""
    runner.invoke(main, ["add", "code-tmpl", "-c", "review code", "-t", "coding"])
    result = runner.invoke(main, ["search", "code"])
    assert result.exit_code == 0
    assert "code-tmpl" in result.output

# --- show command ---

def test_show_not_found(runner):
    """show with nonexistent template."""
    result = runner.invoke(main, ["show", "nonexistent"])
    assert result.exit_code != 0
    assert "Template not found" in result.output


def test_show_with_description_and_variables(runner):
    """show displays description and variables."""
    runner.invoke(main, ["add", "dv-tmpl", "-c", "Hello {{name}}, you are {{age}}", "-d", "A greeting"])
    result = runner.invoke(main, ["show", "dv-tmpl"])
    assert result.exit_code == 0
    assert "A greeting" in result.output
    assert "name" in result.output
    assert "age" in result.output


def test_show_no_description_no_vars(runner):
    """show without description or variables works fine."""
    runner.invoke(main, ["add", "plain-tmpl", "-c", "just text"])
    result = runner.invoke(main, ["show", "plain-tmpl"])
    assert result.exit_code == 0
    assert "plain-tmpl" in result.output

# --- edit command ---

def test_edit_not_found(runner):
    """edit with nonexistent template."""
    result = runner.invoke(main, ["edit", "nonexistent", "-c", "new"])
    assert result.exit_code != 0
    assert "Template not found" in result.output


def test_edit_only_tags(runner):
    """edit only tags, leaving content unchanged."""
    runner.invoke(main, ["add", "tag-only", "-c", "original"])
    result = runner.invoke(main, ["edit", "tag-only", "-t", "new-tag"])
    assert result.exit_code == 0
    assert "Template updated" in result.output


def test_edit_only_description(runner):
    """edit only description."""
    runner.invoke(main, ["add", "desc-edit", "-c", "content"])
    result = runner.invoke(main, ["edit", "desc-edit", "-d", "new desc"])
    assert result.exit_code == 0
    assert "Template updated" in result.output

# --- delete command ---

def test_delete_not_found(runner):
    """delete with nonexistent template."""
    result = runner.invoke(main, ["delete", "nonexistent", "-y"])
    assert result.exit_code != 0
    assert "Template not found" in result.output


def test_delete_cancelled(runner):
    """delete without --yes and user cancels."""
    runner.invoke(main, ["add", "cancel-me", "-c", "content"])
    result = runner.invoke(main, ["delete", "cancel-me"], input="n\n")
    assert result.exit_code == 0
    assert "Cancelled" in result.output

# --- render command ---

def test_render_not_found(runner):
    """render with nonexistent template."""
    result = runner.invoke(main, ["render", "nonexistent"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_render_backslash_value(runner):
    r"""render keeps Windows-style paths in --vars literal (regression).

    Used to crash with re.error: bad escape \U before the fix.
    """
    runner.invoke(main, ["add", "winpath", "-c", "path={{p}}"])
    result = runner.invoke(main, ["render", "winpath", "--vars", r"p=C:\Users\test"])
    assert result.exit_code == 0
    assert "C:\\Users\\test" in result.output


def test_render_missing_variable(runner):
    """render without required variables raises error."""
    runner.invoke(main, ["add", "need-var", "-c", "Hello {{name}}"])
    result = runner.invoke(main, ["render", "need-var"])
    assert result.exit_code != 0


def test_render_no_vars(runner):
    """render a template with no variables."""
    runner.invoke(main, ["add", "no-vars", "-c", "Just static text"])
    result = runner.invoke(main, ["render", "no-vars"])
    assert result.exit_code == 0
    assert "Just static text" in result.output


def test_render_invalid_var_format(runner):
    """render with malformed variable assignment."""
    runner.invoke(main, ["add", "bad-var", "-c", "Hello {{name}}"])
    result = runner.invoke(main, ["render", "bad-var", "-v", "no-equals-sign"])
    assert result.exit_code != 0

# --- import command ---

def test_import_nonexistent_file(runner):
    """import from nonexistent file."""
    # Click validates existence via type=click.Path(exists=True)
    result = runner.invoke(main, ["import", "-i", "/tmp/nonexistent_prompt_mgr_test.json"])
    assert result.exit_code != 0


def test_import_invalid_json(runner, tmp_path):
    """import from invalid JSON file."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json {{{")
    result = runner.invoke(main, ["import", "-i", str(bad_file)])
    assert result.exit_code != 0

# --- export command ---

def test_export_creates_file(runner, tmp_path):
    """export creates a JSON file."""
    runner.invoke(main, ["add", "exp-t1", "-c", "hello"])
    out = tmp_path / "out.json"
    result = runner.invoke(main, ["export", "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    # Export format is {"templates": {name: {...}, ...}}
    if "templates" in data:
        assert "exp-t1" in data["templates"]
    else:
        names = [t["name"] for t in data]
        assert "exp-t1" in names

"""Tests for prompt_mgr.utils."""

import pytest
import os
from pathlib import Path

from prompt_mgr.utils import (
    get_data_dir,
    get_templates_file,
    ensure_data_dir,
    substitute_variables,
    parse_variable_assignments,
    validate_template_name,
    format_template_table,
)
from prompt_mgr.models import Template


# --- get_data_dir ---

def test_get_data_dir_default(tmp_path, monkeypatch):
    """get_data_dir returns home/.prompt-mgr when env not set."""
    monkeypatch.delenv("PROMPT_MGR_DATA_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_data_dir()
    assert result == tmp_path / ".prompt-mgr"


def test_get_data_dir_from_env(monkeypatch):
    """get_data_dir respects PROMPT_MGR_DATA_DIR env var."""
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", "/custom/data")
    assert get_data_dir() == Path("/custom/data")


# --- get_templates_file ---

def test_get_templates_file(monkeypatch):
    """get_templates_file returns data_dir/templates.json."""
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", "/custom/data")
    result = get_templates_file()
    assert result == Path("/custom/data/templates.json")


# --- ensure_data_dir ---

def test_ensure_data_dir_creates_dir(tmp_path):
    """ensure_data_dir creates the directory if it doesn't exist."""
    target = tmp_path / "nested" / "data"
    os.environ["PROMPT_MGR_DATA_DIR"] = str(target)
    try:
        ensure_data_dir()
        assert target.exists()
        assert target.is_dir()
    finally:
        os.environ.pop("PROMPT_MGR_DATA_DIR", None)


def test_ensure_data_dir_idempotent(tmp_path):
    """ensure_data_dir is safe to call when dir already exists."""
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    try:
        ensure_data_dir()
        ensure_data_dir()  # should not raise
        assert tmp_path.exists()
    finally:
        os.environ.pop("PROMPT_MGR_DATA_DIR", None)


# --- substitute_variables ---

def test_substitute_variables_basic():
    """substitute_variables replaces simple placeholders."""
    result = substitute_variables("Hello {{name}}!", {"name": "World"})
    assert result == "Hello World!"


def test_substitute_variables_multiple():
    """substitute_variables handles multiple variables."""
    result = substitute_variables(
        "{{greeting}}, {{name}}!", {"greeting": "Hi", "name": "Alice"}
    )
    assert result == "Hi, Alice!"


def test_substitute_variables_no_match():
    """substitute_variables leaves unmatched placeholders intact."""
    result = substitute_variables("Hello {{name}}", {})
    assert result == "Hello {{name}}"


def test_substitute_variables_partial_overlap():
    """substitute_variables only replaces exact key matches."""
    result = substitute_variables("{{name}} {{namespace}}", {"name": "Bob"})
    # "namespace" is a different key, should remain
    assert "{{namespace}}" in result
    assert "Bob" in result


def test_substitute_variables_empty_content():
    """substitute_variables handles empty content."""
    assert substitute_variables("", {"name": "Bob"}) == ""


def test_substitute_variables_special_regex_chars():
    """substitute_variables handles keys that could be regex special chars."""
    # Keys are word chars normally, but test with dots
    result = substitute_variables("Hello {{user.name}}", {"user.name": "Admin"})
    assert result == "Hello Admin"


def test_substitute_variables_backslash_value():
    """substitute_variables keeps backslashes in values literal (regression).

    Values are used as literal replacements, not re.sub replacement
    templates: ``C:\\Users\\test`` must not raise ``re.error: bad escape``
    and must not be mangled.
    """
    result = substitute_variables("path={{p}}", {"p": r"C:\Users\test"})
    assert result == r"path=C:\Users\test"


def test_substitute_variables_group_reference_value():
    """substitute_variables must not interpret \\1 as a group reference."""
    result = substitute_variables("Hello {{name}}", {"name": r"\1"})
    assert result == "Hello \\1"


# --- parse_variable_assignments ---

def test_parse_variable_assignments_single():
    """parse_variable_assignments parses a single key=value."""
    result = parse_variable_assignments(["name=Alice"])
    assert result == {"name": "Alice"}


def test_parse_variable_assignments_multiple():
    """parse_variable_assignments parses multiple assignments."""
    result = parse_variable_assignments(["name=Alice", "role=admin"])
    assert result == {"name": "Alice", "role": "admin"}


def test_parse_variable_assignments_with_equals_in_value():
    """parse_variable_assignments handles = in the value part."""
    result = parse_variable_assignments(["expr=a=b+c"])
    assert result == {"expr": "a=b+c"}


def test_parse_variable_assignments_strips_whitespace():
    """parse_variable_assignments strips whitespace from key and value."""
    result = parse_variable_assignments(["  name  =  Alice  "])
    assert result == {"name": "Alice"}


def test_parse_variable_assignments_invalid():
    """parse_variable_assignments raises ValueError for malformed input."""
    with pytest.raises(ValueError, match="Invalid variable assignment"):
        parse_variable_assignments(["invalid"])


def test_parse_variable_assignments_empty_list():
    """parse_variable_assignments returns empty dict for empty list."""
    assert parse_variable_assignments([]) == {}


# --- validate_template_name ---

def test_validate_template_name_valid():
    """validate_template_name accepts alphanumeric, hyphens, underscores."""
    assert validate_template_name("my-template") is True
    assert validate_template_name("my_template") is True
    assert validate_template_name("MyTemplate123") is True
    assert validate_template_name("a") is True


def test_validate_template_name_invalid():
    """validate_template_name rejects special characters and spaces."""
    assert validate_template_name("") is False
    assert validate_template_name("invalid name") is False
    assert validate_template_name("invalid/name") is False
    assert validate_template_name("invalid.name") is False
    assert validate_template_name("invalid@name") is False


# --- format_template_table ---

def test_format_template_table_empty():
    """format_template_table handles empty list."""
    result = format_template_table([])
    assert result == "No templates found."


def test_format_template_table_basic():
    """format_template_table renders templates with name and tags."""
    templates = [
        Template(name="greet", content="Hello {{name}}", tags=["social"], description="A greeting"),
    ]
    result = format_template_table(templates)
    assert "📌 greet" in result
    assert "Description: A greeting" in result
    assert "Tags: social" in result
    assert "Preview: Hello {{name}}" in result


def test_format_template_table_show_content():
    """format_template_table shows full content when show_content=True."""
    templates = [
        Template(name="long", content="A" * 200, tags=[]),
    ]
    result = format_template_table(templates, show_content=True)
    assert "Content:" in result
    assert "A" * 200 in result


def test_format_template_table_preview_truncates():
    """format_template_table truncates long content in preview."""
    templates = [
        Template(name="long", content="A" * 200, tags=[]),
    ]
    result = format_template_table(templates, show_content=False)
    assert "..." in result
    assert "A" * 200 not in result


def test_format_template_table_no_tags():
    """format_template_table shows 'none' when tags are empty."""
    templates = [
        Template(name="notags", content="hi", tags=[]),
    ]
    result = format_template_table(templates)
    assert "Tags: none" in result

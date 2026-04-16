"""Tests for CLI commands."""

import pytest
import uuid
from click.testing import CliRunner
from prompt_mgr.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


def test_cli_add(runner):
    """Test adding a template via CLI."""
    unique_name = f"test-template-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(main, [
        "add",
        unique_name,
        "--content", "Hello {{name}}",
        "--tags", "greeting,test",
        "--description", "A test template",
    ])
    
    assert result.exit_code == 0
    assert f"Template added: {unique_name}" in result.output


def test_cli_add_invalid_name(runner):
    """Test adding a template with invalid name."""
    result = runner.invoke(main, [
        "add",
        "invalid name!",
        "--content", "test",
    ])
    
    assert result.exit_code != 0
    assert "Invalid template name" in result.output


def test_cli_list(runner):
    """Test listing templates."""
    # Add a template first
    runner.invoke(main, [
        "add",
        "test1",
        "--content", "content1",
    ])
    
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "test1" in result.output


def test_cli_search(runner):
    """Test searching templates."""
    # Add templates
    runner.invoke(main, [
        "add",
        "code-review",
        "--content", "Review {{code}}",
        "--tags", "coding",
    ])
    
    runner.invoke(main, [
        "add",
        "translate",
        "--content", "Translate {{text}}",
        "--tags", "translation",
    ])
    
    result = runner.invoke(main, ["search", "code"])
    assert result.exit_code == 0
    assert "code-review" in result.output


def test_cli_show(runner):
    """Test showing a template."""
    unique_name = f"show-test-{uuid.uuid4().hex[:8]}"
    # Add a template
    runner.invoke(main, [
        "add",
        unique_name,
        "--content", "Hello {{name}}",
        "--description", "Test template",
    ])
    
    result = runner.invoke(main, ["show", unique_name])
    assert result.exit_code == 0
    assert unique_name in result.output
    assert "Test template" in result.output


def test_cli_edit(runner):
    """Test editing a template."""
    # Add a template
    runner.invoke(main, [
        "add",
        "test",
        "--content", "old content",
    ])
    
    # Edit the template
    result = runner.invoke(main, [
        "edit",
        "test",
        "--content", "new content",
        "--tags", "updated",
    ])
    
    assert result.exit_code == 0
    assert "Template updated: test" in result.output


def test_cli_delete(runner):
    """Test deleting a template."""
    # Add a template
    runner.invoke(main, [
        "add",
        "test",
        "--content", "content",
    ])
    
    # Delete with confirmation
    result = runner.invoke(main, ["delete", "test"], input="y\n")
    assert result.exit_code == 0
    assert "Template deleted: test" in result.output
    
    # Delete with --yes flag
    runner.invoke(main, ["add", "test2", "--content", "content"])
    result = runner.invoke(main, ["delete", "test2", "--yes"])
    assert result.exit_code == 0


def test_cli_render(runner):
    """Test rendering a template."""
    unique_name = f"render-test-{uuid.uuid4().hex[:8]}"
    # Add a template
    runner.invoke(main, [
        "add",
        unique_name,
        "--content", "Hello {{name}}, welcome to {{place}}!",
    ])
    
    result = runner.invoke(main, [
        "render",
        unique_name,
        "--vars", "name=Alice,place=Wonderland",
    ])
    
    assert result.exit_code == 0
    assert "Hello Alice, welcome to Wonderland!" in result.output


def test_cli_export_import(runner, tmp_path):
    """Test exporting and importing templates."""
    # Add a template
    runner.invoke(main, [
        "add",
        "test",
        "--content", "content",
    ])
    
    # Export
    export_file = tmp_path / "export.json"
    result = runner.invoke(main, ["export", "--output", str(export_file)])
    assert result.exit_code == 0
    assert export_file.exists()
    
    # Import (in a new environment would create a new manager)
    result = runner.invoke(main, [
        "import",
        "--input", str(export_file),
    ])
    assert result.exit_code == 0
    assert "Imported" in result.output

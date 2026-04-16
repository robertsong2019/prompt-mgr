"""Tests for PromptManager."""

import pytest
import tempfile
import os
from pathlib import Path

from prompt_mgr.manager import PromptManager
from prompt_mgr.models import Template


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory."""
    data_dir = tmp_path / ".prompt-mgr"
    data_dir.mkdir()
    old_env = os.environ.get("PROMPT_MGR_DATA_DIR")
    os.environ["PROMPT_MGR_DATA_DIR"] = str(data_dir)
    yield data_dir
    if old_env:
        os.environ["PROMPT_MGR_DATA_DIR"] = old_env
    else:
        os.environ.pop("PROMPT_MGR_DATA_DIR", None)


@pytest.fixture
def manager(temp_data_dir):
    """Create a PromptManager instance."""
    return PromptManager()


def test_add_template(manager):
    """Test adding a template."""
    template = manager.add_template(
        name="test-template",
        content="Hello {{name}}",
        tags=["greeting"],
        description="A test template",
    )
    
    assert template.name == "test-template"
    assert template.content == "Hello {{name}}"
    assert template.tags == ["greeting"]
    assert template.description == "A test template"
    assert "name" in template.extract_variables()


def test_add_duplicate_template(manager):
    """Test adding a duplicate template."""
    manager.add_template("test", "content")
    
    with pytest.raises(ValueError, match="already exists"):
        manager.add_template("test", "new content")


def test_add_invalid_name(manager):
    """Test adding a template with invalid name."""
    with pytest.raises(ValueError, match="Invalid template name"):
        manager.add_template("invalid name!", "content")


def test_get_template(manager):
    """Test getting a template."""
    manager.add_template("test", "content")
    
    template = manager.get_template("test")
    assert template is not None
    assert template.name == "test"
    
    # Non-existent template
    assert manager.get_template("nonexistent") is None


def test_update_template(manager):
    """Test updating a template."""
    manager.add_template("test", "old content", tags=["old"])
    
    updated = manager.update_template(
        name="test",
        content="new content",
        tags=["new"],
        description="updated",
    )
    
    assert updated.content == "new content"
    assert updated.tags == ["new"]
    assert updated.description == "updated"


def test_update_nonexistent_template(manager):
    """Test updating a non-existent template."""
    with pytest.raises(ValueError, match="not found"):
        manager.update_template("nonexistent", "content")


def test_delete_template(manager):
    """Test deleting a template."""
    manager.add_template("test", "content")
    
    assert manager.delete_template("test") is True
    assert manager.get_template("test") is None
    
    # Delete non-existent template
    assert manager.delete_template("nonexistent") is False


def test_list_templates(manager):
    """Test listing templates."""
    manager.add_template("template1", "content1", tags=["tag1"])
    manager.add_template("template2", "content2", tags=["tag2"])
    manager.add_template("template3", "content3", tags=["tag1", "tag2"])
    
    # List all
    all_templates = manager.list_templates()
    assert len(all_templates) == 3
    
    # Filter by tag
    filtered = manager.list_templates(tags=["tag1"])
    assert len(filtered) == 2


def test_search_templates(manager):
    """Test searching templates."""
    manager.add_template("code-review", "Review {{code}}", description="Code review template")
    manager.add_template("translate", "Translate {{text}}", description="Translation template")
    
    # Search by name
    results = manager.search_templates("code")
    assert len(results) == 1
    assert results[0].name == "code-review"
    
    # Search by content
    results = manager.search_templates("Translate")
    assert len(results) == 1
    
    # Search by description
    results = manager.search_templates("review")
    assert len(results) == 1


def test_render_template(manager):
    """Test rendering a template."""
    manager.add_template(
        "greeting",
        "Hello {{name}}, welcome to {{place}}!",
    )
    
    result = manager.render_template(
        "greeting",
        {"name": "Alice", "place": "Wonderland"},
    )
    
    assert result == "Hello Alice, welcome to Wonderland!"


def test_render_template_missing_variables(manager):
    """Test rendering with missing variables."""
    manager.add_template("test", "Hello {{name}} and {{other}}")
    
    with pytest.raises(ValueError, match="Missing variables"):
        manager.render_template("test", {"name": "Alice"})


def test_render_nonexistent_template(manager):
    """Test rendering a non-existent template."""
    with pytest.raises(ValueError, match="not found"):
        manager.render_template("nonexistent", {})


def test_export_import_templates(manager, tmp_path):
    """Test exporting and importing templates."""
    # Add some templates
    manager.add_template("template1", "content1", tags=["tag1"])
    manager.add_template("template2", "content2", tags=["tag2"])
    
    # Export
    export_file = tmp_path / "export.json"
    manager.export_templates(export_file)
    
    # Import to a new manager with isolated storage
    import os
    old_env = os.environ.get("PROMPT_MGR_DATA_DIR")
    try:
        os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path / "new_manager")
        new_manager = PromptManager()
        imported_count = new_manager.import_templates(export_file)
        
        assert imported_count == 2
        assert new_manager.get_template("template1") is not None
        assert new_manager.get_template("template2") is not None
    finally:
        if old_env is not None:
            os.environ["PROMPT_MGR_DATA_DIR"] = old_env
        elif "PROMPT_MGR_DATA_DIR" in os.environ:
            del os.environ["PROMPT_MGR_DATA_DIR"]


def test_template_variables(manager):
    """Test template variable extraction."""
    template = manager.add_template(
        "test",
        "Hello {{name}}, your code is {{code}} and {{status}}",
    )
    
    variables = template.extract_variables()
    assert set(variables) == {"name", "code", "status"}

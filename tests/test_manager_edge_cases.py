"""Tests for PromptManager edge cases and untested paths."""

import pytest
import tempfile
import json
import os
from pathlib import Path

from prompt_mgr.manager import PromptManager
from prompt_mgr.models import Template, TemplateCollection


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


# --- Partial update tests ---

def test_update_template_content_only(manager):
    """update_template should update only content when other fields are None."""
    manager.add_template("t1", "old content", tags=["tag1"], description="desc")
    updated = manager.update_template("t1", content="new content")
    assert updated.content == "new content"
    assert updated.tags == ["tag1"]  # unchanged
    assert updated.description == "desc"  # unchanged


def test_update_template_tags_only(manager):
    """update_template should update only tags when other fields are None."""
    manager.add_template("t1", "content", tags=["old"], description="desc")
    updated = manager.update_template("t1", tags=["new", "extra"])
    assert updated.content == "content"  # unchanged
    assert updated.tags == ["new", "extra"]
    assert updated.description == "desc"  # unchanged


def test_update_template_description_only(manager):
    """update_template should update only description when other fields are None."""
    manager.add_template("t1", "content", tags=["tag"], description="old desc")
    updated = manager.update_template("t1", description="new desc")
    assert updated.content == "content"  # unchanged
    assert updated.tags == ["tag"]  # unchanged
    assert updated.description == "new desc"


def test_update_template_updates_timestamp(manager):
    """update_template should update the updated_at timestamp."""
    manager.add_template("t1", "content")
    original = manager.get_template("t1")
    original_ts = original.updated_at
    
    import time
    time.sleep(0.01)
    
    updated = manager.update_template("t1", content="new")
    assert updated.updated_at != original_ts


# --- Persistence tests ---

def test_templates_persist_across_managers(temp_data_dir):
    """Templates should persist when creating a new PromptManager."""
    mgr1 = PromptManager()
    mgr1.add_template("persist-test", "content", tags=["persistent"])
    
    mgr2 = PromptManager()
    template = mgr2.get_template("persist-test")
    assert template is not None
    assert template.content == "content"
    assert template.tags == ["persistent"]


def test_load_corrupted_file(temp_data_dir):
    """Loading a corrupted JSON file should return empty collection."""
    templates_file = temp_data_dir / "templates.json"
    templates_file.write_text("{ invalid json !!!")
    
    mgr = PromptManager()
    assert len(mgr.list_templates()) == 0


# --- import_templates edge cases ---

def test_import_templates_with_overwrite(temp_data_dir, tmp_path):
    """import_templates with overwrite=True should replace existing templates."""
    mgr = PromptManager()
    mgr.add_template("t1", "original content")
    
    # Create import file with same name but different content
    export_file = tmp_path / "import.json"
    export_data = {
        "templates": {
            "t1": {
                "name": "t1",
                "content": "overwritten content",
                "tags": [],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "description": None,
            },
            "t2": {
                "name": "t2",
                "content": "new template",
                "tags": [],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "description": None,
            },
        }
    }
    export_file.write_text(json.dumps(export_data))
    
    imported = mgr.import_templates(export_file, overwrite=True)
    assert imported == 2
    
    t1 = mgr.get_template("t1")
    assert t1.content == "overwritten content"
    assert mgr.get_template("t2") is not None


def test_import_templates_skip_existing(temp_data_dir, tmp_path):
    """import_templates without overwrite should skip existing templates."""
    mgr = PromptManager()
    mgr.add_template("t1", "original")
    
    export_file = tmp_path / "import.json"
    export_data = {
        "templates": {
            "t1": {
                "name": "t1",
                "content": "should be skipped",
                "tags": [],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "description": None,
            },
            "t2": {
                "name": "t2",
                "content": "new one",
                "tags": [],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "description": None,
            },
        }
    }
    export_file.write_text(json.dumps(export_data))
    
    imported = mgr.import_templates(export_file, overwrite=False)
    assert imported == 1
    
    # t1 should be unchanged
    assert mgr.get_template("t1").content == "original"
    # t2 should be imported
    assert mgr.get_template("t2") is not None


def test_import_empty_file(temp_data_dir, tmp_path):
    """import_templates with empty templates dict should return 0."""
    mgr = PromptManager()
    
    export_file = tmp_path / "empty.json"
    export_file.write_text(json.dumps({"templates": {}}))
    
    imported = mgr.import_templates(export_file)
    assert imported == 0


# --- render_template edge cases ---

def test_render_template_extra_variables(manager):
    """render_template should ignore extra variables not in template."""
    manager.add_template("t1", "Hello {{name}}")
    result = manager.render_template("t1", {"name": "Alice", "extra": "ignored"})
    assert result == "Hello Alice"


def test_render_template_no_variables(manager):
    """render_template should work with templates that have no variables."""
    manager.add_template("t1", "static content")
    result = manager.render_template("t1", {})
    assert result == "static content"


def test_render_template_multiple_same_variable(manager):
    """render_template should replace all occurrences of a variable."""
    manager.add_template("t1", "{{x}} and {{x}} again")
    result = manager.render_template("t1", {"x": "foo"})
    assert result == "foo and foo again"


# --- delete_template edge case ---

def test_delete_template_removes_from_persistence(temp_data_dir):
    """Deleted templates should not reappear after reloading."""
    mgr1 = PromptManager()
    mgr1.add_template("doomed", "content")
    mgr1.delete_template("doomed")
    
    mgr2 = PromptManager()
    assert mgr2.get_template("doomed") is None


# --- search edge cases ---

def test_search_empty_collection(manager):
    """Searching an empty collection should return empty list."""
    results = manager.search_templates("anything")
    assert results == []


def test_search_with_both_query_and_tags(manager):
    """search_templates should filter by both query and tags."""
    manager.add_template("python-guide", "Python programming", tags=["coding", "guide"])
    manager.add_template("python-tutorial", "Learn Python fast", tags=["tutorial"])
    manager.add_template("java-guide", "Java programming", tags=["coding", "guide"])
    
    # Search for "python" with tag "guide"
    results = manager.search_templates("python", tags=["guide"])
    assert len(results) == 1
    assert results[0].name == "python-guide"


# --- clone_template edge cases ---

def test_clone_nonexistent_template(manager):
    """Cloning a non-existent template should raise ValueError."""
    with pytest.raises(ValueError, match="not found"):
        manager.clone_template("nonexistent", "clone")


def test_clone_to_existing_name(manager):
    """Cloning to an existing template name should raise ValueError."""
    manager.add_template("source", "content")
    manager.add_template("target", "existing")
    
    with pytest.raises(ValueError, match="already exists"):
        manager.clone_template("source", "target")


def test_clone_invalid_name(manager):
    """Cloning with an invalid name should raise ValueError."""
    manager.add_template("source", "content")
    with pytest.raises(ValueError, match="Invalid template name"):
        manager.clone_template("source", "invalid name!")


def test_clone_preserves_content_and_tags(manager):
    """Cloned template should have same content and tags as source."""
    manager.add_template("original", "Hello {{name}}", tags=["greeting"], description="A greeting")
    clone = manager.clone_template("original", "cloned")
    
    assert clone.content == "Hello {{name}}"
    assert clone.tags == ["greeting"]
    assert clone.description == "A greeting"
    assert clone.name == "cloned"
    
    # Modifying clone should not affect original
    clone.tags.append("new")
    original = manager.get_template("original")
    assert "new" not in original.tags


# --- get_stats edge cases ---

def test_get_stats_empty_collection(manager):
    """get_stats on empty collection should return zero stats."""
    stats = manager.get_stats()
    assert stats["total"] == 0
    assert stats["tag_frequency"] == {}
    assert stats["total_variables"] == 0
    assert stats["avg_content_length"] == 0
    assert stats["templates_with_variables"] == 0


def test_get_stats_with_data(manager):
    """get_stats should correctly compute statistics."""
    manager.add_template("t1", "Hello {{name}}", tags=["a", "b"])
    manager.add_template("t2", "No vars", tags=["a"])
    manager.add_template("t3", "{{x}} and {{y}}", tags=["c"])
    
    stats = manager.get_stats()
    assert stats["total"] == 3
    assert stats["tag_frequency"]["a"] == 2
    assert stats["tag_frequency"]["b"] == 1
    assert stats["tag_frequency"]["c"] == 1
    assert stats["total_variables"] == 3  # 1 (name) + 0 + 2 (x, y)
    assert stats["templates_with_variables"] == 2  # t1 and t3
    # avg content length: len("Hello {{name}}")=14, len("No vars")=7, len("{{x}} and {{y}}")=15
    # (14 + 7 + 15) // 3 = 12
    assert stats["avg_content_length"] == 12

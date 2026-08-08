"""Tests for F7 rename_template and F8 add_tag/remove_tag."""

import json
import pytest
from unittest.mock import patch, MagicMock
from prompt_mgr.manager import PromptManager
from prompt_mgr.models import Template


@pytest.fixture
def manager(tmp_path):
    """Create a manager with isolated storage."""
    templates_file = tmp_path / "templates.json"
    with patch("prompt_mgr.manager.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_data_dir", return_value=tmp_path):
        mgr = PromptManager()
        mgr.templates_file = templates_file
        return mgr


@pytest.fixture
def populated_manager(manager):
    """Manager with a few templates."""
    manager.add_template("greeting", "Hello {{name}}!", tags=["social", "casual"])
    manager.add_template("farewell", "Goodbye {{name}}.", tags=["social"])
    manager.add_template("code-review", "Review: {{repo}}", tags=["work", "technical"])
    return manager


# ─── F7: rename_template ────────────────────────────────────────────

class TestRenameTemplate:

    def test_basic_rename(self, populated_manager):
        """Rename preserves content, tags, description."""
        result = populated_manager.rename_template("greeting", "hello")
        assert result.name == "hello"
        assert result.content == "Hello {{name}}!"
        assert result.tags == ["social", "casual"]
        # Old name should not exist
        assert populated_manager.get_template("greeting") is None
        # New name should exist
        assert populated_manager.get_template("hello") is not None

    def test_rename_preserves_description(self, populated_manager):
        """Description should survive rename."""
        populated_manager.update_template("greeting", description="A hello template")
        result = populated_manager.rename_template("greeting", "hi")
        assert result.description == "A hello template"

    def test_rename_updates_timestamp(self, populated_manager):
        """Renamed template should have updated_at >= original created_at."""
        original = populated_manager.get_template("greeting")
        result = populated_manager.rename_template("greeting", "hello")
        assert result.updated_at >= original.updated_at

    def test_rename_old_not_found(self, populated_manager):
        """Should raise ValueError if old name doesn't exist."""
        with pytest.raises(ValueError, match="Template not found: nonexistent"):
            populated_manager.rename_template("nonexistent", "new-name")

    def test_rename_new_already_exists(self, populated_manager):
        """Should raise ValueError if new name already taken."""
        with pytest.raises(ValueError, match="Template already exists: farewell"):
            populated_manager.rename_template("greeting", "farewell")

    def test_rename_invalid_name(self, populated_manager):
        """Should raise ValueError for invalid new name."""
        with pytest.raises(ValueError, match="Invalid template name"):
            populated_manager.rename_template("greeting", "invalid name with spaces!")

    def test_rename_persists_to_file(self, populated_manager):
        """Rename should be saved to disk."""
        populated_manager.rename_template("greeting", "hello")
        # Reload from file
        with open(populated_manager.templates_file, "r") as f:
            data = json.load(f)
        names = list(data["templates"].keys())
        assert "hello" in names
        assert "greeting" not in names

    def test_rename_same_name_allowed(self, populated_manager):
        """Renaming to the same name should work (identity rename)."""
        result = populated_manager.rename_template("greeting", "greeting")
        assert result.name == "greeting"

    def test_rename_to_valid_special_chars(self, populated_manager):
        """Hyphens and underscores should be allowed."""
        result = populated_manager.rename_template("greeting", "hello-world_test")
        assert result.name == "hello-world_test"


# ─── F8: add_tag / remove_tag ─────────────────────────────────────────

class TestAddTag:

    def test_add_tag_basic(self, populated_manager):
        """Add a new tag to a template."""
        result = populated_manager.add_tag("greeting", "friendly")
        assert "friendly" in result.tags
        assert "social" in result.tags  # existing tags preserved
        assert "casual" in result.tags

    def test_add_tag_idempotent(self, populated_manager):
        """Adding an existing tag should not duplicate it."""
        result = populated_manager.add_tag("greeting", "social")
        assert result.tags.count("social") == 1

    def test_add_tag_persists(self, populated_manager):
        """Tag addition should be saved to disk."""
        populated_manager.add_tag("greeting", "new-tag")
        with open(populated_manager.templates_file, "r") as f:
            data = json.load(f)
        greeting_data = data["templates"]["greeting"]
        assert "new-tag" in greeting_data["tags"]

    def test_add_tag_template_not_found(self, populated_manager):
        """Should raise ValueError for non-existent template."""
        with pytest.raises(ValueError, match="Template not found: ghost"):
            populated_manager.add_tag("ghost", "tag")

    def test_add_tag_updates_timestamp(self, populated_manager):
        """Adding a tag should update the timestamp."""
        original = populated_manager.get_template("greeting")
        result = populated_manager.add_tag("greeting", "fresh")
        assert result.updated_at >= original.updated_at


class TestRemoveTag:

    def test_remove_tag_basic(self, populated_manager):
        """Remove an existing tag."""
        result = populated_manager.remove_tag("greeting", "casual")
        assert "casual" not in result.tags
        assert "social" in result.tags  # other tags preserved

    def test_remove_tag_not_present(self, populated_manager):
        """Removing a non-existent tag should be a no-op (no error)."""
        result = populated_manager.remove_tag("greeting", "nonexistent")
        assert result.tags == ["social", "casual"]

    def test_remove_tag_persists(self, populated_manager):
        """Tag removal should be saved to disk."""
        populated_manager.remove_tag("greeting", "social")
        with open(populated_manager.templates_file, "r") as f:
            data = json.load(f)
        greeting_data = data["templates"]["greeting"]
        assert "social" not in greeting_data["tags"]

    def test_remove_tag_template_not_found(self, populated_manager):
        """Should raise ValueError for non-existent template."""
        with pytest.raises(ValueError, match="Template not found: ghost"):
            populated_manager.remove_tag("ghost", "tag")

    def test_remove_tag_updates_timestamp(self, populated_manager):
        """Removing a tag should update the timestamp."""
        original = populated_manager.get_template("greeting")
        result = populated_manager.remove_tag("greeting", "casual")
        assert result.updated_at >= original.updated_at

    def test_remove_all_tags(self, populated_manager):
        """Remove all tags one by one."""
        populated_manager.remove_tag("greeting", "social")
        result = populated_manager.remove_tag("greeting", "casual")
        assert result.tags == []

    def test_add_then_remove_roundtrip(self, populated_manager):
        """Add a tag then remove it should leave original state."""
        original_tags = list(populated_manager.get_template("greeting").tags)
        populated_manager.add_tag("greeting", "temp")
        populated_manager.remove_tag("greeting", "temp")
        result = populated_manager.get_template("greeting")
        assert result.tags == original_tags

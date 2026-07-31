"""Tests for PromptManager.clone_template and PromptManager.get_stats."""

import pytest
import os

from prompt_mgr.manager import PromptManager


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
    return PromptManager()


# --- clone_template ---

class TestCloneTemplate:

    def test_clone_basic(self, manager):
        """Clone creates an independent copy with the new name."""
        original = manager.add_template(
            "greeting",
            "Hello {{name}}",
            tags=["social", "english"],
            description="A greeting template",
        )
        clone = manager.clone_template("greeting", "greeting-v2")

        assert clone.name == "greeting-v2"
        assert clone.content == original.content
        assert clone.tags == original.tags
        assert clone.description == original.description

    def test_clone_tags_are_independent(self, manager):
        """Modifying clone's tags doesn't affect the original."""
        manager.add_template("src", "content", tags=["a", "b"])
        clone = manager.clone_template("src", "dst")

        clone.tags.append("c")
        original = manager.get_template("src")
        assert "c" not in original.tags

    def test_clone_persists_to_disk(self, manager):
        """Cloned template survives a new manager instance."""
        manager.add_template("src", "Hello {{name}}", tags=["greeting"])
        manager.clone_template("src", "cloned")

        # New manager from same storage
        new_mgr = PromptManager()
        assert new_mgr.get_template("cloned") is not None

    def test_clone_nonexistent_source(self, manager):
        """Cloning a non-existent template raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            manager.clone_template("nonexistent", "clone")

    def test_clone_existing_target_name(self, manager):
        """Cloning to an existing name raises ValueError."""
        manager.add_template("src", "content")
        manager.add_template("dst", "existing")

        with pytest.raises(ValueError, match="already exists"):
            manager.clone_template("src", "dst")

    def test_clone_invalid_name(self, manager):
        """Cloning to an invalid name raises ValueError."""
        manager.add_template("src", "content")
        with pytest.raises(ValueError, match="Invalid template name"):
            manager.clone_template("src", "invalid name!")

    def test_clone_content_is_independent(self, manager):
        """Clone gets its own content copy (string is immutable, but verify equality)."""
        manager.add_template("src", "Hello {{name}}, welcome!")
        clone = manager.clone_template("src", "dst")
        assert clone.content == "Hello {{name}}, welcome!"

    def test_clone_preserves_variables(self, manager):
        """Cloned template has the same extractable variables."""
        manager.add_template("src", "Hello {{name}} from {{place}}")
        clone = manager.clone_template("src", "dst")
        assert set(clone.extract_variables()) == {"name", "place"}

    def test_clone_no_tags(self, manager):
        """Cloning a template with no tags works."""
        manager.add_template("src", "content")
        clone = manager.clone_template("src", "dst")
        assert clone.tags == []

    def test_clone_no_description(self, manager):
        """Cloning a template with no description works."""
        manager.add_template("src", "content")
        clone = manager.clone_template("src", "dst")
        assert clone.description is None


# --- get_stats ---

class TestGetStats:

    def test_stats_empty_collection(self, manager):
        """Stats on empty collection returns zeros."""
        stats = manager.get_stats()
        assert stats["total"] == 0
        assert stats["tag_frequency"] == {}
        assert stats["total_variables"] == 0
        assert stats["avg_content_length"] == 0
        assert stats["templates_with_variables"] == 0

    def test_stats_total_count(self, manager):
        """Stats reports correct total count."""
        manager.add_template("t1", "content1")
        manager.add_template("t2", "content2")
        manager.add_template("t3", "content3")

        stats = manager.get_stats()
        assert stats["total"] == 3

    def test_stats_tag_frequency(self, manager):
        """Stats reports correct tag frequency distribution."""
        manager.add_template("t1", "c", tags=["python", "web"])
        manager.add_template("t2", "c", tags=["python", "api"])
        manager.add_template("t3", "c", tags=["rust"])

        stats = manager.get_stats()
        assert stats["tag_frequency"]["python"] == 2
        assert stats["tag_frequency"]["web"] == 1
        assert stats["tag_frequency"]["api"] == 1
        assert stats["tag_frequency"]["rust"] == 1

    def test_stats_tag_frequency_no_tags(self, manager):
        """Templates with no tags don't affect tag_frequency."""
        manager.add_template("t1", "c")
        manager.add_template("t2", "c", tags=["x"])

        stats = manager.get_stats()
        assert stats["tag_frequency"] == {"x": 1}

    def test_stats_total_variables(self, manager):
        """Stats sums unique variables across all templates."""
        manager.add_template("t1", "Hello {{name}}")
        manager.add_template("t2", "Translate {{text}} from {{lang}}")
        manager.add_template("t3", "No variables here")

        stats = manager.get_stats()
        assert stats["total_variables"] == 3  # name + text + lang

    def test_stats_avg_content_length(self, manager):
        """Stats computes average content length."""
        manager.add_template("t1", "12345")     # 5 chars
        manager.add_template("t2", "1234567890")  # 10 chars

        stats = manager.get_stats()
        assert stats["avg_content_length"] == 7  # (5 + 10) // 2

    def test_stats_templates_with_variables(self, manager):
        """Stats counts templates that have at least one variable."""
        manager.add_template("t1", "Hello {{name}}")
        manager.add_template("t2", "No vars")
        manager.add_template("t3", "{{x}} and {{y}}")

        stats = manager.get_stats()
        assert stats["templates_with_variables"] == 2

    def test_stats_single_template(self, manager):
        """Stats with one template works correctly."""
        manager.add_template(
            "only",
            "Hello {{name}}",
            tags=["greeting"],
            description="test",
        )

        stats = manager.get_stats()
        assert stats["total"] == 1
        assert stats["tag_frequency"] == {"greeting": 1}
        assert stats["total_variables"] == 1
        assert stats["avg_content_length"] == len("Hello {{name}}")
        assert stats["templates_with_variables"] == 1

    def test_stats_duplicate_variables_across_templates(self, manager):
        """Same variable name in different templates is counted per-template."""
        manager.add_template("t1", "{{x}}")
        manager.add_template("t2", "{{x}} and {{y}}")

        stats = manager.get_stats()
        assert stats["total_variables"] == 3  # 1 + 2 (counted per template, not unique)

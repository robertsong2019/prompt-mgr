"""Tests for TemplateCollection.recent() and CLI recent command."""

import os
import pytest
from click.testing import CliRunner
from prompt_mgr.models import Template, TemplateCollection
from prompt_mgr.cli import main


@pytest.fixture
def runner(tmp_path):
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    yield CliRunner()
    del os.environ["PROMPT_MGR_DATA_DIR"]


# --- Model tests ---

def test_recent_empty():
    """recent on empty collection returns []."""
    c = TemplateCollection()
    assert c.recent() == []


def test_recent_returns_all_when_n_exceeds_count():
    """recent(n=100) returns all templates when fewer exist."""
    c = TemplateCollection()
    for i in range(3):
        t = Template(name=f"t{i}", content=f"content {i}")
        t.updated_at = f"2026-08-{18-i:02d}T10:00:00"
        c.add(t)
    result = c.recent(100)
    assert len(result) == 3
    assert result[0].name == "t0"  # t0 has 08-18, most recent


def test_recent_sorts_by_updated_at_desc():
    """recent sorts by updated_at descending."""
    c = TemplateCollection()
    # Add oldest first
    t1 = Template(name="oldest", content="a")
    t1.updated_at = "2026-01-01T00:00:00"
    t2 = Template(name="middle", content="b")
    t2.updated_at = "2026-06-15T12:00:00"
    t3 = Template(name="newest", content="c")
    t3.updated_at = "2026-08-18T20:00:00"
    for t in [t1, t2, t3]:
        c.add(t)
    result = c.recent(2)
    assert [t.name for t in result] == ["newest", "middle"]


def test_recent_n_limits_result():
    """recent(n=2) returns at most 2 templates."""
    c = TemplateCollection()
    for i in range(5):
        t = Template(name=f"t{i}", content=f"c{i}")
        t.updated_at = f"2026-08-{18-i:02d}T10:00:00"
        c.add(t)
    result = c.recent(2)
    assert len(result) == 2
    assert result[0].name == "t0"  # t0 has largest date (08-18)


def test_recent_n_default_10():
    """recent() defaults to n=10."""
    c = TemplateCollection()
    for i in range(15):
        t = Template(name=f"t{i}", content="c")
        t.updated_at = f"2026-08-{28-i:02d}T10:00:00"
        c.add(t)
    result = c.recent()
    assert len(result) == 10


def test_recent_does_not_mutate_collection():
    """recent does not modify the original collection."""
    c = TemplateCollection()
    t = Template(name="test", content="hello")
    t.updated_at = "2026-08-18T10:00:00"
    c.add(t)
    _ = c.recent(1)
    assert c.get("test") is not None
    assert len(c.list_all()) == 1

# --- CLI tests ---

def test_cli_recent_empty(runner):
    """CLI recent with no templates shows message."""
    result = runner.invoke(main, ["recent"])
    assert result.exit_code == 0
    assert "No templates found" in result.output


def test_cli_recent_shows_templates(runner):
    """CLI recent shows recently updated templates."""
    runner.invoke(main, ["add", "old-tmpl", "-c", "old"])
    runner.invoke(main, ["add", "new-tmpl", "-c", "new"])
    result = runner.invoke(main, ["recent"])
    assert result.exit_code == 0
    assert "new-tmpl" in result.output
    assert "old-tmpl" in result.output


def test_cli_recent_limits_output(runner):
    """CLI recent --limit 1 shows only 1 template."""
    for i in range(5):
        runner.invoke(main, ["add", f"r{i}", "-c", f"content {i}"])
    result = runner.invoke(main, ["recent", "-n", "1"])
    assert result.exit_code == 0
    # Only the most recent should appear
    lines = [l for l in result.output.split("\n") if "📌" in l]
    assert len(lines) == 1

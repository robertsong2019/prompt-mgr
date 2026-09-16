"""Tests for F24 TemplateCollection.validate_all() + PromptManager.validate_all() + CLI doctor."""

import os
import pytest
from click.testing import CliRunner
from prompt_mgr.models import Template, TemplateCollection
from prompt_mgr.manager import PromptManager
from prompt_mgr.cli import main


@pytest.fixture
def runner(tmp_path):
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    yield CliRunner()
    del os.environ["PROMPT_MGR_DATA_DIR"]


@pytest.fixture
def manager(tmp_path):
    templates_file = tmp_path / "templates.json"
    from unittest.mock import patch
    with patch("prompt_mgr.manager.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_data_dir", return_value=tmp_path):
        mgr = PromptManager()
        mgr.templates_file = templates_file
        return mgr


# --- Collection tests ---

def test_validate_all_empty():
    """validate_all on empty collection returns {}."""
    c = TemplateCollection()
    assert c.validate_all() == {}


def test_validate_all_clean():
    """Templates without warnings are not reported."""
    c = TemplateCollection()
    c.add(Template(name="a", content="Hello {{name}}"))
    c.add(Template(name="b", content="Plain text."))
    assert c.validate_all() == {}


def test_validate_all_reports_dirty():
    """Templates with warnings are reported with their warning lists."""
    c = TemplateCollection()
    c.add(Template(name="clean", content="Hi {{who}}"))
    c.add(Template(name="dirty", content="Hi {{who"))
    report = c.validate_all()
    assert list(report.keys()) == ["dirty"]
    assert any("Unbalanced" in w for w in report["dirty"])


def test_validate_all_sorted_with_multiple_warnings():
    """Report keys sorted by name; a template may have several warnings."""
    c = TemplateCollection()
    c.add(Template(name="zeta", content="ok"))
    c.add(Template(name="beta", content="   "))
    c.add(Template(name="alpha", content="x } y"))
    report = c.validate_all()
    assert list(report.keys()) == ["alpha", "beta"]
    assert len(report["beta"]) >= 1  # empty content
    assert any("Lone" in w for w in report["alpha"])


def test_validate_all_does_not_mutate():
    """Lint sweep is read-only: content untouched after the call."""
    c = TemplateCollection()
    c.add(Template(name="dirty", content="Hi {{who"))
    c.validate_all()
    assert c.get("dirty").content == "Hi {{who"


# --- Manager tests ---

def test_manager_validate_all_forwards(manager):
    """Manager forwards to collection and reports dirty templates."""
    manager.add_template("good", "Hello {{name}}!")
    manager.add_template("bad", "oops }")
    report = manager.validate_all()
    assert list(report.keys()) == ["bad"]
    assert any("Lone" in w for w in report["bad"])


def test_manager_validate_all_clean(manager):
    """Healthy store yields empty report."""
    manager.add_template("good", "Hello {{name}}!")
    assert manager.validate_all() == {}


# --- CLI tests ---

def test_cli_doctor_clean(runner):
    """doctor on healthy store prints OK summary."""
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["add", "ok", "-c", "Hello {{name}}"])
        assert result.exit_code == 0
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "1 template" in result.output
        assert "no issues" in result.output


def test_cli_doctor_reports_warnings(runner):
    """doctor lists each offending template with its warnings."""
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["add", "bad", "-c", "Hi {{name"])
        assert result.exit_code == 0
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "bad" in result.output
        assert "Unbalanced" in result.output

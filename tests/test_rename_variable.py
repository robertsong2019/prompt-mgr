"""Tests for rename_variable — F22 (write-side of F20 variables_inventory)."""

import pytest
from click.testing import CliRunner

from prompt_mgr.models import Template, TemplateCollection
from prompt_mgr.manager import PromptManager
from prompt_mgr.cli import main


# ---------- collection layer ----------

def _c(*specs):
    c = TemplateCollection()
    for name, content in specs:
        c.add(Template(name=name, content=content))
    return c


def test_rename_basic():
    c = _c(("greet", "hello {{name}}"), ("bye", "goodbye {{name}}"))
    report = c.rename_variable("name", "user")
    assert report == {"renamed": {"bye": 1, "greet": 1}, "total_replacements": 2}
    assert c.get("greet").content == "hello {{user}}"
    assert c.get("bye").content == "goodbye {{user}}"


def test_rename_multiple_occurrences_counted():
    c = _c(("a", "{{x}} then {{x}} again {{x}}"))
    report = c.rename_variable("x", "y")
    assert report == {"renamed": {"a": 3}, "total_replacements": 3}
    assert c.get("a").content == "{{y}} then {{y}} again {{y}}"


def test_rename_word_boundary_no_prefix_collision():
    """Renaming `topic` must not touch `{{topic_id}}`."""
    c = _c(("a", "{{topic}} and {{topic_id}}"))
    report = c.rename_variable("topic", "subject")
    assert report == {"renamed": {"a": 1}, "total_replacements": 1}
    assert c.get("a").content == "{{subject}} and {{topic_id}}"


def test_rename_other_variables_untouched():
    c = _c(("a", "{{x}} {{y}} {{x}}"))
    c.rename_variable("x", "z")
    assert c.get("a").content == "{{z}} {{y}} {{z}}"


def test_rename_absent_variable_noop_not_error():
    c = _c(("a", "hello {{name}}"))
    before = c.get("a").content
    report = c.rename_variable("ghost", "new")
    assert report == {"renamed": {}, "total_replacements": 0}
    assert c.get("a").content == before


def test_rename_report_sorted_by_template_name():
    c = _c(("zeta", "{{v}}"), ("alpha", "{{v}}"), ("mid", "{{v}}"))
    report = c.rename_variable("v", "w")
    assert list(report["renamed"].keys()) == ["alpha", "mid", "zeta"]


def test_rename_same_name_raises():
    c = _c(("a", "{{x}}"))
    with pytest.raises(ValueError, match="identical"):
        c.rename_variable("x", "x")


@pytest.mark.parametrize("bad", ["user name", "user-1", "", "{{x}}"])
def test_rename_invalid_new_name_raises(bad):
    c = _c(("a", "{{x}}"))
    with pytest.raises(ValueError, match="[Ii]nvalid new variable name"):
        c.rename_variable("x", bad)


def test_rename_invalid_old_name_raises():
    c = _c(("a", "{{x}}"))
    with pytest.raises(ValueError, match="[Ii]nvalid old variable name"):
        c.rename_variable("bad name", "y")


def test_rename_empty_collection():
    assert TemplateCollection().rename_variable("a", "b") == {
        "renamed": {},
        "total_replacements": 0,
    }


# ---------- manager layer ----------

@pytest.fixture
def mgr(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    m = PromptManager()
    m.add_template("uses", "hello {{name}} twice {{name}}")
    m.add_template("plain", "no vars here")
    return m


def test_manager_rename_persists_and_bumps(mgr, tmp_path):
    before = mgr.get_template("uses").updated_at
    plain_before = mgr.get_template("plain").updated_at
    report = mgr.rename_variable("name", "user")
    assert report == {"renamed": {"uses": 2}, "total_replacements": 2}
    assert mgr.get_template("uses").updated_at != before
    # Unaffected template untouched
    assert mgr.get_template("plain").updated_at == plain_before
    # Reload from disk: persisted
    m2 = PromptManager()
    assert m2.get_template("uses").content == "hello {{user}} twice {{user}}"


def test_manager_rename_noop_no_save_no_bump(mgr):
    before = mgr.get_template("uses").updated_at
    report = mgr.rename_variable("ghost", "other")
    assert report["total_replacements"] == 0
    assert mgr.get_template("uses").updated_at == before
    assert mgr.get_template("uses").content == "hello {{name}} twice {{name}}"


# ---------- CLI layer ----------

def test_cli_rename_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    PromptManager().add_template("t", "hi {{name}}")
    result = CliRunner().invoke(main, ["rename-variable", "name", "user"])
    assert result.exit_code == 0
    assert "user" in result.output
    assert PromptManager().get_template("t").content == "hi {{user}}"


def test_cli_rename_variable_noop_message(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    PromptManager().add_template("t", "hi {{name}}")
    result = CliRunner().invoke(main, ["rename-variable", "ghost", "user"])
    assert result.exit_code == 0
    assert "ghost" in result.output
    assert "hi {{name}}" in PromptManager().get_template("t").content


def test_cli_rename_variable_error_exit(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    PromptManager().add_template("t", "hi {{name}}")
    result = CliRunner().invoke(main, ["rename-variable", "name", "name"])
    assert result.exit_code != 0


# ---------- F23: dry-run preview ----------

def test_dry_run_reports_without_mutating():
    c = _c(("a", "{{x}} twice {{x}}"), ("b", "{{x}}"))
    report = c.rename_variable("x", "y", dry_run=True)
    assert report == {"renamed": {"a": 2, "b": 1}, "total_replacements": 3}
    assert c.get("a").content == "{{x}} twice {{x}}"
    assert c.get("b").content == "{{x}}"


def test_dry_run_report_equals_real_run():
    c1 = _c(("a", "{{x}} {{x}}"), ("b", "no vars"))
    c2 = _c(("a", "{{x}} {{x}}"), ("b", "no vars"))
    dry = c1.rename_variable("x", "y", dry_run=True)
    real = c2.rename_variable("x", "y")
    assert dry == real == {"renamed": {"a": 2}, "total_replacements": 2}
    # c1 untouched by its dry run
    assert c1.get("a").content == "{{x}} {{x}}"


def test_dry_run_still_validates_names():
    c = _c(("a", "{{x}}"))
    with pytest.raises(ValueError, match="identical"):
        c.rename_variable("x", "x", dry_run=True)


def test_manager_dry_run_no_persist_no_bump(mgr):
    before = mgr.get_template("uses").updated_at
    report = mgr.rename_variable("name", "user", dry_run=True)
    assert report["total_replacements"] == 2
    assert mgr.get_template("uses").updated_at == before
    # Disk state unchanged
    m2 = PromptManager()
    assert m2.get_template("uses").content == "hello {{name}} twice {{name}}"


def test_cli_dry_run_shows_report_without_writing(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    PromptManager().add_template("t", "hi {{name}}")
    result = CliRunner().invoke(
        main, ["rename-variable", "name", "user", "--dry-run"]
    )
    assert result.exit_code == 0
    assert PromptManager().get_template("t").content == "hi {{name}}"

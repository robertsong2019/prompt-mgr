"""Tests for TemplateCollection.variables_inventory() — F20."""

from prompt_mgr.models import Template, TemplateCollection


def _make(name, content, **kw):
    return Template(name=name, content=content, **kw)


# ---------- model layer ----------

def test_empty_collection():
    """Empty collection returns empty dict."""
    assert TemplateCollection().variables_inventory() == {}


def test_single_template_single_variable():
    """One template, one variable."""
    c = TemplateCollection()
    c.add(_make("greet", "hello {{name}}"))
    inv = c.variables_inventory()
    assert inv == {"name": {"count": 1, "templates": ["greet"]}}


def test_shared_variable_aggregates():
    """Variable used by multiple templates aggregates both names."""
    c = TemplateCollection()
    c.add(_make("a", "hi {{user}}"))
    c.add(_make("b", "bye {{user}} and {{topic}}"))
    inv = c.variables_inventory()
    assert inv["user"] == {"count": 2, "templates": ["a", "b"]}
    assert inv["topic"] == {"count": 1, "templates": ["b"]}


def test_duplicate_occurrences_count_once():
    """Same variable occurring twice in one template counts once (per-template semantics, like tag_summary)."""
    c = TemplateCollection()
    c.add(_make("a", "{{x}} then {{x}} again"))
    inv = c.variables_inventory()
    assert inv == {"x": {"count": 1, "templates": ["a"]}}


def test_sorting_count_desc_then_name_asc():
    """Inventory sorted by usage count desc, then variable name asc."""
    c = TemplateCollection()
    c.add(_make("a", "{{zeta}} {{alpha}}"))
    c.add(_make("b", "{{alpha}}"))
    c.add(_make("c", "{{mid}}"))
    keys = list(c.variables_inventory().keys())
    assert keys == ["alpha", "mid", "zeta"]


def test_no_variable_templates_absent():
    """Templates without variables contribute nothing."""
    c = TemplateCollection()
    c.add(_make("plain", "no vars here"))
    assert c.variables_inventory() == {}


def test_variable_tag_namespaces_independent():
    """A tag with the same name as a variable does not leak into inventory."""
    c = TemplateCollection()
    c.add(_make("a", "use {{topic}}", tags=["topic"]))
    inv = c.variables_inventory()
    assert list(inv.keys()) == ["topic"]
    assert inv["topic"]["count"] == 1


# ---------- manager forward ----------

def test_manager_forward(tmp_path, monkeypatch):
    """PromptManager.variables_inventory() forwards to collection."""
    from prompt_mgr.manager import PromptManager
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    m = PromptManager()
    m.add_template("a", "hello {{who}}", tags=[])
    inv = m.variables_inventory()
    assert inv == {"who": {"count": 1, "templates": ["a"]}}


def test_manager_empty(tmp_path, monkeypatch):
    """Empty store forwards to empty inventory."""
    from prompt_mgr.manager import PromptManager
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    m = PromptManager()
    assert m.variables_inventory() == {}


# ---------- CLI ----------

def test_cli_variables_command(tmp_path, monkeypatch):
    """CLI `variables` lists variable usage."""
    from click.testing import CliRunner
    from prompt_mgr.cli import main as cli
    from prompt_mgr.manager import PromptManager
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    runner = CliRunner()

    m = PromptManager()
    m.add_template("greet", "hello {{name}}")
    m.add_template("bye", "bye {{name}} / {{lang}}")

    result = runner.invoke(cli, ["variables"])
    assert result.exit_code == 0
    assert "name" in result.output
    assert "2" in result.output
    assert "greet" in result.output and "bye" in result.output


def test_cli_variables_empty(tmp_path, monkeypatch):
    """CLI `variables` on empty store exits cleanly."""
    from click.testing import CliRunner
    from prompt_mgr.cli import main as cli
    monkeypatch.setenv("PROMPT_MGR_DATA_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["variables"])
    assert result.exit_code == 0
    assert "No variables" in result.output

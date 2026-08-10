"""Tests for TemplateCollection.search_by_variables() — F13."""

from prompt_mgr.models import Template, TemplateCollection


def _make(name, content, **kw):
    return Template(name=name, content=content, **kw)


def test_match_any():
    """'any' returns templates using at least one of the variables."""
    c = TemplateCollection()
    c.add(_make("a", "Hello {{name}}"))
    c.add(_make("b", "Key is {{api_key}}"))
    c.add(_make("c", "No variables here"))
    result = c.search_by_variables(["name", "api_key"], match="any")
    assert len(result) == 2
    assert set(t.name for t in result) == {"a", "b"}


def test_match_all():
    """'all' returns only templates using ALL specified variables."""
    c = TemplateCollection()
    c.add(_make("a", "{{name}} and {{role}}"))
    c.add(_make("b", "{{name}} only"))
    c.add(_make("c", "{{role}} only"))
    result = c.search_by_variables(["name", "role"], match="all")
    assert len(result) == 1
    assert result[0].name == "a"


def test_match_all_single_match():
    """'all' with one variable returns templates using that variable."""
    c = TemplateCollection()
    c.add(_make("a", "{{x}}"))
    c.add(_make("b", "{{y}}"))
    c.add(_make("c", "no vars"))
    result = c.search_by_variables(["x"], match="all")
    assert len(result) == 1
    assert result[0].name == "a"


def test_no_match():
    """Returns empty when no templates use the variables."""
    c = TemplateCollection()
    c.add(_make("a", "{{name}}"))
    result = c.search_by_variables(["nonexistent"])
    assert result == []


def test_empty_variables():
    """Empty variable list returns empty (no possible match)."""
    c = TemplateCollection()
    c.add(_make("a", "{{name}}"))
    result = c.search_by_variables([])
    assert result == []


def test_invalid_match_raises():
    """Invalid match mode → ValueError."""
    c = TemplateCollection()
    try:
        c.search_by_variables(["x"], match="exact")
        assert False, "Should have raised"
    except ValueError as e:
        assert "exact" in str(e)


def test_case_sensitive_variables():
    """Variable matching is case-sensitive."""
    c = TemplateCollection()
    c.add(_make("a", "{{API_KEY}}"))
    c.add(_make("b", "{{api_key}}"))
    result = c.search_by_variables(["API_KEY"])
    assert len(result) == 1
    assert result[0].name == "a"


def test_duplicate_variables():
    """Duplicate variable names in search list are deduped by set logic."""
    c = TemplateCollection()
    c.add(_make("a", "{{name}}"))
    result = c.search_by_variables(["name", "name"], match="any")
    assert len(result) == 1


def test_many_variables():
    """Search with multiple variables across multiple templates."""
    c = TemplateCollection()
    c.add(_make("a", "{{a}} {{b}} {{c}}"))
    c.add(_make("b", "{{a}} {{b}}"))
    c.add(_make("c", "{{c}}"))
    c.add(_make("d", "{{x}}"))
    # 'any' for a,b,c hits a,b,c
    result_any = c.search_by_variables(["a", "b", "c"], match="any")
    assert len(result_any) == 3
    # 'all' for a,b,c hits only a
    result_all = c.search_by_variables(["a", "b", "c"], match="all")
    assert len(result_all) == 1
    assert result_all[0].name == "a"


def test_template_with_same_var_twice():
    """Template using same variable multiple times still matched once."""
    c = TemplateCollection()
    c.add(_make("a", "{{name}} says {{name}}"))
    result = c.search_by_variables(["name"])
    assert len(result) == 1


def test_manager_integration():
    """search_by_variables works through PromptManager."""
    from prompt_mgr.manager import PromptManager
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        os.environ["PROMPT_MGR_DATA_DIR"] = td
        try:
            mgr = PromptManager()
            mgr.add_template("a", "Hello {{name}}, role={{role}}")
            mgr.add_template("b", "Key={{api_key}}")
            mgr.add_template("c", "No vars")
            result = mgr.collection.search_by_variables(["role"], match="any")
            assert len(result) == 1
            assert result[0].name == "a"
        finally:
            del os.environ["PROMPT_MGR_DATA_DIR"]

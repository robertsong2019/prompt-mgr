"""Tests for Template.validate()."""

import pytest
from prompt_mgr.models import Template


def test_validate_clean():
    t = Template(name="clean", content="Hello {{name}}")
    assert t.validate() == []


def test_validate_empty_content():
    t = Template(name="empty", content="  ")
    w = t.validate()
    assert any("empty" in x for x in w)


def test_validate_unclosed_variable():
    t = Template(name="unclosed", content="Hello {{name")
    w = t.validate()
    assert any("Unbalanced" in x for x in w)


def test_validate_extra_close():
    t = Template(name="extra", content="Hello name}}")
    w = t.validate()
    assert any("Unbalanced" in x for x in w)


def test_validate_multiple_variables():
    t = Template(name="multi", content="{{a}} and {{b}} and {{c}}")
    assert t.validate() == []


def test_validate_lone_brace():
    t = Template(name="lone", content="Hello {name}")
    w = t.validate()
    assert any("Lone" in x for x in w)


def test_validate_no_warnings_static():
    t = Template(name="static", content="Just plain text with no variables")
    assert t.validate() == []

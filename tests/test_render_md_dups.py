"""Tests for Template.render(), Template.to_markdown(), and TemplateCollection.find_duplicates()."""

import pytest
from prompt_mgr.models import Template, TemplateCollection


# ─── F1: Template.render() ───


class TestTemplateRender:
    """Test Template.render(variables) method."""

    def test_basic_substitution(self):
        t = Template(name="greet", content="Hello {{name}}!")
        result = t.render({"name": "World"})
        assert result == "Hello World!"

    def test_multiple_variables(self):
        t = Template(name="email", content="Dear {{name}}, your code is {{code}}.")
        result = t.render({"name": "Alice", "code": "12345"})
        assert "Alice" in result
        assert "12345" in result

    def test_no_variables(self):
        t = Template(name="static", content="No variables here.")
        result = t.render({})
        assert result == "No variables here."

    def test_missing_variable_raises(self):
        t = Template(name="greet", content="Hello {{name}} and {{title}}!")
        with pytest.raises(ValueError, match="Missing variables"):
            t.render({"name": "World"})

    def test_all_missing_raises(self):
        t = Template(name="greet", content="Hello {{name}}!")
        with pytest.raises(ValueError, match="name"):
            t.render({})

    def test_extra_variables_ignored(self):
        t = Template(name="greet", content="Hello {{name}}!")
        result = t.render({"name": "World", "extra": "ignored"})
        assert result == "Hello World!"

    def test_repeated_variables(self):
        t = Template(name="echo", content="{{x}} and {{x}} and {{x}}")
        result = t.render({"x": "hi"})
        assert result == "hi and hi and hi"

    def test_special_regex_chars_in_value(self):
        t = Template(name="test", content="Value: {{v}}")
        result = t.render({"v": "$$$ (regex)"})
        assert result == "Value: $$$ (regex)"

    def test_empty_string_variable(self):
        t = Template(name="test", content="Hello {{name}}!")
        result = t.render({"name": ""})
        assert result == "Hello !"

    def test_underscore_variable(self):
        t = Template(name="test", content="{{snake_case}} works")
        result = t.render({"snake_case": "yes"})
        assert result == "yes works"

    def test_render_does_not_modify_template(self):
        t = Template(name="greet", content="Hello {{name}}!")
        original = t.content
        t.render({"name": "World"})
        assert t.content == original


# ─── F2: Template.to_markdown() ───


class TestTemplateToMarkdown:
    """Test Template.to_markdown() method."""

    def test_basic_markdown(self):
        t = Template(name="my-template", content="Hello world")
        md = t.to_markdown()
        assert "## my-template" in md
        assert "Hello world" in md

    def test_includes_description(self):
        t = Template(name="t1", content="content", description="A test template")
        md = t.to_markdown()
        assert "*A test template*" in md

    def test_includes_tags(self):
        t = Template(name="t1", content="content", tags=["python", "ai"])
        md = t.to_markdown()
        assert "**Tags:**" in md
        assert "python" in md
        assert "ai" in md

    def test_no_tags_no_tags_section(self):
        t = Template(name="t1", content="content")
        md = t.to_markdown()
        assert "**Tags:**" not in md

    def test_includes_variables(self):
        t = Template(name="t1", content="Hello {{name}}, your score is {{score}}")
        md = t.to_markdown()
        assert "**Variables:**" in md
        assert "name" in md
        assert "score" in md

    def test_no_variables_no_vars_section(self):
        t = Template(name="t1", content="No vars")
        md = t.to_markdown()
        assert "**Variables:**" not in md

    def test_includes_timestamps(self):
        t = Template(name="t1", content="content", created_at="2026-01-01T00:00:00", updated_at="2026-06-01T12:00:00")
        md = t.to_markdown()
        assert "**Created:** 2026-01-01" in md
        assert "**Updated:** 2026-06-01" in md

    def test_content_in_code_block(self):
        t = Template(name="t1", content="print('hello')")
        md = t.to_markdown()
        assert "```\nprint('hello')\n```" in md

    def test_full_markdown_structure(self):
        t = Template(
            name="email-template",
            content="Dear {{name}}, welcome!",
            tags=["email", "onboarding"],
            description="Welcome email template",
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-02T00:00:00",
        )
        md = t.to_markdown()
        # Verify ordering: title → desc → tags → vars → timestamps → code
        title_pos = md.index("## email-template")
        desc_pos = md.index("*Welcome email template*")
        tags_pos = md.index("**Tags:**")
        vars_pos = md.index("**Variables:**")
        created_pos = md.index("**Created:**")
        code_pos = md.index("```")
        assert title_pos < desc_pos < tags_pos < vars_pos < created_pos < code_pos

    def test_variables_sorted(self):
        t = Template(name="t1", content="{{zebra}} {{apple}} {{mango}}")
        md = t.to_markdown()
        vars_pos = md.index("**Variables:**")
        apple_pos = md.index("apple", vars_pos)
        mango_pos = md.index("mango", vars_pos)
        zebra_pos = md.index("zebra", vars_pos)
        assert apple_pos < mango_pos < zebra_pos


# ─── F4: TemplateCollection.find_duplicates() ───


class TestFindDuplicates:
    """Test TemplateCollection.find_duplicates() method."""

    def test_no_duplicates(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="content A"))
        col.add(Template(name="b", content="content B"))
        dups = col.find_duplicates()
        assert dups == {}

    def test_exact_duplicates(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="same content"))
        col.add(Template(name="b", content="same content"))
        dups = col.find_duplicates()
        assert len(dups) == 1
        for names in dups.values():
            assert sorted(names) == ["a", "b"]

    def test_three_duplicates(self):
        col = TemplateCollection()
        col.add(Template(name="x", content="identical"))
        col.add(Template(name="y", content="identical"))
        col.add(Template(name="z", content="identical"))
        dups = col.find_duplicates()
        assert len(dups) == 1
        for names in dups.values():
            assert sorted(names) == ["x", "y", "z"]

    def test_whitespace_difference_not_duplicate(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="content"))
        col.add(Template(name="b", content="content "))  # trailing space
        dups = col.find_duplicates()
        # Different content = not duplicate
        assert dups == {}

    def test_multiple_groups(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="group1"))
        col.add(Template(name="b", content="group1"))
        col.add(Template(name="c", content="group2"))
        col.add(Template(name="d", content="group2"))
        col.add(Template(name="e", content="unique"))
        dups = col.find_duplicates()
        assert len(dups) == 2

    def test_empty_collection(self):
        col = TemplateCollection()
        assert col.find_duplicates() == {}

    def test_single_template(self):
        col = TemplateCollection()
        col.add(Template(name="only", content="content"))
        assert col.find_duplicates() == {}

    def test_names_sorted_in_groups(self):
        col = TemplateCollection()
        col.add(Template(name="zeta", content="dup"))
        col.add(Template(name="alpha", content="dup"))
        col.add(Template(name="mid", content="dup"))
        dups = col.find_duplicates()
        for names in dups.values():
            assert names == ["alpha", "mid", "zeta"]

    def test_returns_dict(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="x"))
        col.add(Template(name="b", content="x"))
        dups = col.find_duplicates()
        assert isinstance(dups, dict)

    def test_large_content(self):
        large = "x" * 10000
        col = TemplateCollection()
        col.add(Template(name="a", content=large))
        col.add(Template(name="b", content=large))
        dups = col.find_duplicates()
        assert len(dups) == 1

    def test_different_templates_different_vars_not_dup(self):
        col = TemplateCollection()
        col.add(Template(name="a", content="Hello {{name}}"))
        col.add(Template(name="b", content="Hello {{user}}"))
        dups = col.find_duplicates()
        assert dups == {}

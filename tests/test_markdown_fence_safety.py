"""F84 regression: markdown fence safety — content containing bare ``` lines.

A template whose content itself contains a line of ``` (e.g. a markdown
snippet documenting fenced code) used to break the export→import roundtrip:
the bare ``` line closed the export fence early and everything between it
and the next ``` was silently dropped. Fix: dynamic fence length on export
(CommonMark rule: fence must be longer than any backtick run at line start
in the content) and >= length close semantics on import.
"""

import pytest

from prompt_mgr.models import Template


NAUGHTY = "before\n```\nnaughty fence\n```\nafter"


def test_roundtrip_content_with_bare_triple_backtick_line():
    """Content containing a bare ``` line survives to_markdown→from_markdown."""
    t = Template(name="snippet", content=NAUGHTY, tags=["x"])
    md = t.to_markdown()
    t2 = Template.from_markdown(md)
    assert t2.name == "snippet"
    assert t2.content == NAUGHTY


def test_export_uses_longer_fence_when_content_has_backtick_line():
    """Writer escapes by lengthening the fence instead of emitting ``` naively."""
    t = Template(name="snippet", content=NAUGHTY)
    md = t.to_markdown()
    fence_lines = [
        line.strip() for line in md.splitlines()
        if line.strip() and set(line.strip()) == {"`"}
    ]
    # opening fence = first pure-backtick line; must be longer than 3
    assert fence_lines and len(fence_lines[0]) > 3


def test_roundtrip_content_with_longer_backtick_run():
    """Even a ```` run in content roundtrips (fence grows past it)."""
    content = "code\n````\ninner\n````\ntail"
    t = Template(name="hard", content=content)
    t2 = Template.from_markdown(t.to_markdown())
    assert t2.content == content


def test_import_closes_on_equal_or_longer_fence_only():
    """Reader (CommonMark): fence closes on >= opening length, not shorter runs."""
    # 4-backtick fence must NOT be closed by a 3-backtick line
    text = "## hard\n\n````\nnot-a-close\n```\nstill inside\n````"
    t = Template.from_markdown(text)
    assert t.content == "not-a-close\n```\nstill inside"


def test_import_still_rejects_unterminated_long_fence():
    text = "## broken\n\n````\ncontent without matching close"
    with pytest.raises(ValueError, match="Unterminated"):
        Template.from_markdown(text)


def test_import_tolerates_shorter_fence_inside_when_open_is_3():
    """Back-compat: a 3-fence block behaves exactly as before for well-formed input."""
    text = "## ok\n\n```\nplain\n```\n"
    t = Template.from_markdown(text)
    assert t.content == "plain"

"""Tests for F16 CLI wiring: export/import --format markdown round-trip."""

import os

import pytest
from click.testing import CliRunner

from prompt_mgr.cli import main


@pytest.fixture
def runner(tmp_path):
    """Create a CLI runner with isolated data dir."""
    os.environ["PROMPT_MGR_DATA_DIR"] = str(tmp_path)
    yield CliRunner()
    del os.environ["PROMPT_MGR_DATA_DIR"]


def add_sample(runner, name="review", content="Check {{lang}} code.", tags="quality"):
    return runner.invoke(
        main, ["add", name, "--content", content, "--tags", tags]
    )


def test_export_markdown_writes_document(runner, tmp_path):
    add_sample(runner)
    out = tmp_path / "lib.md"
    result = runner.invoke(main, ["export", "--format", "markdown", "-o", str(out)])
    assert result.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert "# Prompt Library" in text
    assert "## review" in text


def test_export_default_still_json(runner, tmp_path):
    add_sample(runner)
    out = tmp_path / "templates.json"
    result = runner.invoke(main, ["export", "-o", str(out)])
    assert result.exit_code == 0
    assert '"templates"' in out.read_text(encoding="utf-8")


def test_markdown_roundtrip_via_cli(runner, tmp_path):
    add_sample(runner)
    md = tmp_path / "lib.md"
    runner.invoke(main, ["export", "--format", "markdown", "-o", str(md)])

    # Wipe the store, then re-import from markdown
    import prompt_mgr.manager as m
    data_file = os.environ["PROMPT_MGR_DATA_DIR"] + "/templates.json"
    if os.path.exists(data_file):
        os.remove(data_file)

    result = runner.invoke(main, ["import", "-i", str(md), "--format", "markdown"])
    assert result.exit_code == 0
    assert "Imported 1 templates" in result.output

    show = runner.invoke(main, ["show", "review"])
    assert show.exit_code == 0
    assert "Check {{lang}} code." in show.output


def test_import_markdown_multiple_templates(runner, tmp_path):
    doc = (
        "# Prompt Library\n\n"
        "## Contents\n\n- [a](#a)\n\n"
        "## a\n\n**Tags:** x\n\n**Created:** 2026-01-01T00:00:00  \n"
        "**Updated:** 2026-01-01T00:00:00\n\n```\nA {{v}}\n```\n\n"
        "## b\n\n**Tags:** y\n\n```\nB\n```\n"
    )
    src = tmp_path / "two.md"
    src.write_text(doc, encoding="utf-8")
    result = runner.invoke(main, ["import", "-i", str(src), "--format", "markdown"])
    assert result.exit_code == 0
    assert "Imported 2 templates" in result.output


def test_import_markdown_skips_existing_without_overwrite(runner, tmp_path):
    add_sample(runner)
    md = tmp_path / "lib.md"
    runner.invoke(main, ["export", "--format", "markdown", "-o", str(md)])
    result = runner.invoke(main, ["import", "-i", str(md), "--format", "markdown"])
    assert result.exit_code == 0
    assert "Imported 0 templates" in result.output


def test_import_markdown_overwrite_replaces(runner, tmp_path):
    add_sample(runner)
    md = tmp_path / "lib.md"
    runner.invoke(main, ["export", "--format", "markdown", "-o", str(md)])

    # Stale markdown: modify 'review' content after export, store keeps old copy
    text = md.read_text(encoding="utf-8").replace("Check {{lang}} code.", "NEW CONTENT")
    md.write_text(text, encoding="utf-8")

    # Without --overwrite the stale name is skipped
    skip = runner.invoke(main, ["import", "-i", str(md), "--format", "markdown"])
    assert "Imported 0 templates" in skip.output

    result = runner.invoke(
        main, ["import", "-i", str(md), "--format", "markdown", "--overwrite"]
    )
    assert result.exit_code == 0
    assert "Imported 1 templates" in result.output
    show = runner.invoke(main, ["show", "review"])
    assert "NEW CONTENT" in show.output


def test_import_markdown_no_blocks_imports_zero(runner, tmp_path):
    src = tmp_path / "empty.md"
    src.write_text("# nothing\njust text\n", encoding="utf-8")
    result = runner.invoke(main, ["import", "-i", str(src), "--format", "markdown"])
    assert result.exit_code == 0
    assert "Imported 0 templates" in result.output


def test_import_markdown_missing_file_errors(runner, tmp_path):
    result = runner.invoke(
        main, ["import", "-i", str(tmp_path / "nope.md"), "--format", "markdown"]
    )
    assert result.exit_code != 0

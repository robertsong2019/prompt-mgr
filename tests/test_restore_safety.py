"""Tests for restore/import structural-corruption safety + store quarantine.

RED-verified bugs (2026-09-20):
1. restore() accepted valid-JSON foreign documents ({"foo": 1}) —
   TemplateCollection.from_dict's .get("templates", {}) silently produced an
   empty collection, so a "successful" restore OVERWROTE the store with an
   empty state (silent store destruction, exit 0).
2. _load_templates started fresh on a corrupt store file, and the next save
   clobbered the corrupt file — every template irrecoverably lost.
"""

import json
import os
from unittest.mock import patch

import pytest

from prompt_mgr.manager import PromptManager


@pytest.fixture
def env(tmp_path):
    """Patched store location in a tmp dir."""
    templates_file = tmp_path / "templates.json"
    with patch("prompt_mgr.manager.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_templates_file", return_value=templates_file), \
         patch("prompt_mgr.utils.get_data_dir", return_value=tmp_path):
        yield {"templates_file": templates_file, "tmp_path": tmp_path}


@pytest.fixture
def manager(env):
    mgr = PromptManager()
    mgr.templates_file = env["templates_file"]
    return mgr


@pytest.fixture
def two_template_store(manager):
    manager.add_template("alpha", "content of alpha {{x}}", tags=["t1"])
    manager.add_template("beta", "content of beta", description="d")
    return manager


def write_snapshot(tmp_path, name, payload):
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir(exist_ok=True)
    p = snap_dir / name
    p.write_text(json.dumps(payload) if not isinstance(payload, str) else payload,
                 encoding="utf-8")
    return p.name


FOREIGN_SNAPSHOTS = [
    {"foo": 1},                                  # valid JSON, no templates key
    [],                                          # top-level list
    "just a string",                             # top-level string
    {"templates": []},                           # templates member not a dict
    {"templates": {"a": {"content": "x"}}},      # entry missing required name
    {"templates": {"a": "not-a-dict"}},          # entry not an object
]


@pytest.mark.parametrize("payload", FOREIGN_SNAPSHOTS,
                         ids=lambda p: json.dumps(p)[:40])
def test_restore_foreign_snapshot_raises_and_store_untouched(
        two_template_store, env, payload):
    """Structurally-foreign snapshot -> ValueError BEFORE any write.

    RED-pinned: previously {"foo": 1} restored 'successfully' (restored=0)
    and wiped alpha/beta off disk.
    """
    m = two_template_store
    store_before = env["templates_file"].read_text()
    name = write_snapshot(env["tmp_path"], "templates-20990101-000000.json", payload)

    with pytest.raises(ValueError):
        m.restore(name)

    # store untouched: templates alive, bytes identical
    assert m.get_template("alpha") is not None
    assert m.get_template("beta") is not None
    assert env["templates_file"].read_text() == store_before


def test_restore_malformed_json_snapshot_still_rejected(two_template_store, env):
    """Syntax corruption path (pre-existing contract) stays fail-closed."""
    m = two_template_store
    snap_dir = env["tmp_path"] / "snapshots"
    snap_dir.mkdir(exist_ok=True)
    (snap_dir / "templates-20990101-000001.json").write_text("{corrupt!!", encoding="utf-8")

    with pytest.raises((json.JSONDecodeError, ValueError)):
        m.restore("templates-20990101-000001.json")
    assert m.get_template("alpha") is not None


def test_restore_empty_store_snapshot_remains_legit(two_template_store, env):
    """A real empty-store snapshot {"templates": {}} still restores (restored=0)
    with a safety snapshot — only FOREIGN structures are rejected."""
    m = two_template_store
    name = write_snapshot(env["tmp_path"], "templates-20990101-000002.json",
                          {"templates": {}})
    report = m.restore(name)
    assert report["restored"] == 0
    assert m.collection.list_all() == []
    assert (env["tmp_path"] / "snapshots" / report["safety_snapshot"]).is_file()


def test_import_foreign_json_raises_not_silent_zero(manager, env):
    """import_templates with foreign JSON -> ValueError, not '✓ Imported 0'."""
    bad = env["tmp_path"] / "bad.json"
    bad.write_text(json.dumps({"foo": 1}), encoding="utf-8")
    with pytest.raises(ValueError):
        manager.import_templates(bad)


def test_corrupt_store_load_quarantines_backup(env):
    """Corrupt store file: fresh start, but corrupt bytes preserved in a
    .corrupt-*.bak beside it — next save no longer destroys the only copy.
    RED-pinned: previously the backup did not exist and one add_template
    permanently overwrote the corrupt (recoverable) store.
    """
    store = env["templates_file"]
    corrupt_bytes = "{corrupted!! not json"
    store.write_text(corrupt_bytes, encoding="utf-8")

    with patch("prompt_mgr.manager.get_templates_file", return_value=store), \
         patch("prompt_mgr.utils.get_templates_file", return_value=store), \
         patch("prompt_mgr.utils.get_data_dir", return_value=env["tmp_path"]):
        m2 = PromptManager()
        assert m2.collection.list_all() == []          # fresh start preserved
        m2.add_template("gamma", "only survivor")       # triggers a save

    backups = list(env["tmp_path"].glob("templates.json.corrupt-*.bak"))
    assert len(backups) == 1, "corrupt store must be quarantined exactly once"
    assert backups[0].read_text(encoding="utf-8") == corrupt_bytes
    # quarantine survives subsequent saves
    assert store.read_text() != corrupt_bytes


def test_foreign_store_load_quarantines_and_starts_fresh(env):
    """Structurally-foreign store (valid JSON) -> ValueError -> quarantine +
    fresh collection (constructor must not crash)."""
    store = env["templates_file"]
    store.write_text(json.dumps({"foo": 1}), encoding="utf-8")

    with patch("prompt_mgr.manager.get_templates_file", return_value=store), \
         patch("prompt_mgr.utils.get_templates_file", return_value=store), \
         patch("prompt_mgr.utils.get_data_dir", return_value=env["tmp_path"]):
        m3 = PromptManager()
        assert m3.collection.list_all() == []

    backups = list(env["tmp_path"].glob("templates.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert json.loads(backups[0].read_text(encoding="utf-8")) == {"foo": 1}

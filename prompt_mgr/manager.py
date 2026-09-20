"""Core manager for prompt templates."""

import json
import os
import re
from typing import List, Optional, Dict
from pathlib import Path

from .models import Template, TemplateCollection
from .utils import (
    get_templates_file,
    ensure_data_dir,
    substitute_variables,
    validate_template_name,
)


class PromptManager:
    """Manager for prompt templates."""

    def __init__(self):
        """Initialize the prompt manager."""
        self.templates_file = get_templates_file()
        self.collection = self._load_templates()

    def _load_templates(self) -> TemplateCollection:
        """Load templates from file."""
        ensure_data_dir()

        if not self.templates_file.exists():
            return TemplateCollection()

        try:
            with open(self.templates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TemplateCollection.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Corrupted or foreign store: start fresh, but quarantine the
            # unreadable file first — the next save would otherwise clobber
            # it and destroy every template irrecoverably.
            self._quarantine_store(e)
            return TemplateCollection()

    def _quarantine_store(self, reason: Exception) -> None:
        """Preserve an unreadable store file beside itself before a fresh-state save overwrites it."""
        import shutil
        from datetime import datetime

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.templates_file.with_name(
            f"{self.templates_file.name}.corrupt-{stamp}.bak"
        )
        try:
            shutil.copy2(self.templates_file, backup)
            print(
                f"Warning: Could not load templates file: {reason}\n"
                f"Corrupt store preserved at: {backup}"
            )
        except OSError as e:
            print(
                f"Warning: Could not load templates file: {reason} "
                f"(quarantine failed: {e})"
            )

    def _save_templates(self) -> None:
        """Save templates to file."""
        ensure_data_dir()

        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(self.collection.to_dict(), f, indent=2)

    def add_template(
        self,
        name: str,
        content: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Template:
        """Add a new template.

        Args:
            name: Template name
            content: Template content
            tags: List of tags
            description: Template description

        Returns:
            Created template

        Raises:
            ValueError: If template name is invalid or already exists
        """
        if not validate_template_name(name):
            raise ValueError(
                f"Invalid template name: {name}. "
                "Use only alphanumeric characters, hyphens, and underscores."
            )

        if self.collection.get(name):
            raise ValueError(f"Template already exists: {name}")

        template = Template(
            name=name,
            content=content,
            tags=tags or [],
            description=description,
        )

        self.collection.add(template)
        self._save_templates()

        return template

    def get_template(self, name: str) -> Optional[Template]:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        return self.collection.get(name)

    def update_template(
        self,
        name: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Template:
        """Update an existing template.

        Args:
            name: Template name
            content: New content (optional)
            tags: New tags (optional)
            description: New description (optional)

        Returns:
            Updated template

        Raises:
            ValueError: If template doesn't exist
        """
        template = self.collection.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        if content is not None:
            template.content = content
        if tags is not None:
            template.tags = tags
        if description is not None:
            template.description = description

        template.update_timestamp()
        self._save_templates()

        return template

    def delete_template(self, name: str) -> bool:
        """Delete a template.

        Args:
            name: Template name

        Returns:
            True if deleted, False if not found
        """
        result = self.collection.delete(name)
        if result:
            self._save_templates()
        return result

    def list_templates(
        self,
        tags: Optional[List[str]] = None,
    ) -> List[Template]:
        """List all templates, optionally filtered by tags.

        Args:
            tags: Filter by tags (optional)

        Returns:
            List of templates
        """
        if not tags:
            return self.collection.list_all()

        return self.collection.search(query="", tags=tags)

    def search_templates(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        regex: bool = False,
    ) -> List[Template]:
        """Search templates by query and/or tags.

        Args:
            query: Search query (substring, or regex when regex=True)
            tags: Filter by tags (optional)
            regex: Treat query as a case-sensitive regular expression

        Returns:
            List of matching templates
        """
        return self.collection.search(query=query, tags=tags, regex=regex)

    def render_template(
        self,
        name: str,
        variables: Dict[str, str],
    ) -> str:
        """Render a template with variables.

        Args:
            name: Template name
            variables: Variable values

        Returns:
            Rendered template content

        Raises:
            ValueError: If template not found
        """
        template = self.collection.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        # Check for missing variables
        required_vars = template.extract_variables()
        missing_vars = set(required_vars) - set(variables.keys())

        if missing_vars:
            raise ValueError(
                f"Missing variables: {', '.join(missing_vars)}. "
                f"Required: {', '.join(required_vars)}"
            )

        return substitute_variables(template.content, variables)

    def render_to_file(
        self,
        name: str,
        variables: Dict[str, str],
        output_file: Path,
    ) -> Path:
        """Render a template and write the result to a file.

        Args:
            name: Template name
            variables: Variable values
            output_file: Destination path (parent dirs created as needed)

        Returns:
            The output path

        Raises:
            ValueError: If template not found or variables missing
                (in which case no file is written)
        """
        result = self.render_template(name, variables)
        output = Path(output_file)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, encoding="utf-8")
        return output

    def export_templates(self, output_file: Path) -> None:
        """Export templates to a JSON file.

        Args:
            output_file: Output file path
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.collection.to_dict(), f, indent=2)

    def clone_template(self, source_name: str, new_name: str) -> Template:
        """Clone an existing template with a new name.

        Args:
            source_name: Name of the template to clone
            new_name: Name for the cloned template

        Returns:
            The cloned Template

        Raises:
            ValueError: If source doesn't exist or new name already taken
        """
        source = self.collection.get(source_name)
        if not source:
            raise ValueError(f"Template not found: {source_name}")

        if self.collection.get(new_name):
            raise ValueError(f"Template already exists: {new_name}")

        if not validate_template_name(new_name):
            raise ValueError(
                f"Invalid template name: {new_name}. "
                "Use only alphanumeric characters, hyphens, and underscores."
            )

        clone = Template(
            name=new_name,
            content=source.content,
            tags=list(source.tags),
            description=source.description,
        )

        self.collection.add(clone)
        self._save_templates()
        return clone

    def get_stats(self) -> dict:
        """Return statistics about the template collection.

        Returns:
            Dictionary with keys:
            - total: total number of templates
            - tag_frequency: dict of tag -> count
            - total_variables: sum of unique variables across all templates
            - avg_content_length: mean content length in characters
            - templates_with_variables: count of templates that have variables
        """
        templates = self.collection.list_all()
        total = len(templates)

        if total == 0:
            return {
                "total": 0,
                "tag_frequency": {},
                "total_variables": 0,
                "avg_content_length": 0,
                "templates_with_variables": 0,
            }

        tag_freq = {}
        total_vars = 0
        total_content_len = 0
        with_vars = 0

        for t in templates:
            for tag in t.tags:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1
            total_vars += len(t.extract_variables())
            total_content_len += len(t.content)
            if t.extract_variables():
                with_vars += 1

        return {
            "total": total,
            "tag_frequency": tag_freq,
            "total_variables": total_vars,
            "avg_content_length": total_content_len // total,
            "templates_with_variables": with_vars,
        }

    def rename_template(self, old_name: str, new_name: str) -> Template:
        """Rename a template preserving all its data.

        Args:
            old_name: Current template name
            new_name: New template name

        Returns:
            The renamed Template

        Raises:
            ValueError: If old name doesn't exist, new name already taken,
                       or new name is invalid
        """
        template = self.collection.get(old_name)
        if not template:
            raise ValueError(f"Template not found: {old_name}")

        if old_name == new_name:
            return template

        if self.collection.get(new_name):
            raise ValueError(f"Template already exists: {new_name}")

        if not validate_template_name(new_name):
            raise ValueError(
                f"Invalid template name: {new_name}. "
                "Use only alphanumeric characters, hyphens, and underscores."
            )

        # Delete old, add with new name (preserves content/tags/description)
        self.collection.delete(old_name)
        renamed = Template(
            name=new_name,
            content=template.content,
            tags=list(template.tags),
            description=template.description,
        )
        self.collection.add(renamed)
        self._save_templates()
        return renamed

    def add_tag(self, name: str, tag: str) -> Template:
        """Add a single tag to a template.

        Args:
            name: Template name
            tag: Tag to add

        Returns:
            Updated Template

        Raises:
            ValueError: If template doesn't exist
        """
        template = self.collection.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        if tag not in template.tags:
            template.tags.append(tag)
            template.update_timestamp()
            self._save_templates()
        return template

    def remove_tag(self, name: str, tag: str) -> Template:
        """Remove a single tag from a template.

        Args:
            name: Template name
            tag: Tag to remove

        Returns:
            Updated Template

        Raises:
            ValueError: If template doesn't exist
        """
        template = self.collection.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        if tag in template.tags:
            template.tags.remove(tag)
            template.update_timestamp()
            self._save_templates()
        return template

    def recent_templates(self, n: int = 10) -> list:
        """Return the n most recently updated templates.

        Args:
            n: Maximum number of templates to return.

        Returns:
            List of Template objects sorted by updated_at descending.
        """
        return self.collection.recent(n)

    def variables_inventory(self) -> dict:
        """Return the variable-level usage inventory of the store.

        Returns:
            Same structure as ``TemplateCollection.variables_inventory()``:
            variable name -> {"count": n_templates, "templates": sorted names},
            sorted by count desc then variable name asc.
        """
        return self.collection.variables_inventory()

    def validate_all(self) -> dict:
        """Health check: warnings for every invalid template.

        Read-only forward to :meth:`TemplateCollection.validate_all`.
        Returns ``{name: [warnings]}`` sorted by name; empty dict when
        all templates pass validation.
        """
        return self.collection.validate_all()

    def snapshot(self) -> Path:
        """Write a timestamped backup of the template store.

        Flushes in-memory state first, so the snapshot always equals
        what the manager currently holds (edits made directly on
        ``collection`` are captured too). The main store is left
        untouched. Snapshots land in ``snapshots/`` next to the store as
        ``templates-YYYYMMDD-HHMMSS.json``; same-second collisions get a
        ``.1``, ``.2``... suffix. Run before risky bulk operations
        (``rename_variable``, markdown imports).

        Returns:
            Path to the created snapshot file.
        """
        import shutil
        from datetime import datetime

        self._save_templates()  # flush so snapshot == current in-memory state
        snap_dir = self.templates_file.parent / "snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = snap_dir / f"templates-{stamp}.json"
        n = 1
        while dest.exists():  # same-second collision guard
            dest = snap_dir / f"templates-{stamp}.{n}.json"
            n += 1
        shutil.copyfile(self.templates_file, dest)
        return dest

    def list_snapshots(self) -> list:
        """Inventory existing snapshots, newest first.

        Only files matching ``templates-*.json`` in the snapshots
        directory are reported. Each entry carries ``name``, ``path``,
        ``size_bytes`` and ``modified`` (epoch mtime). Missing or empty
        directory yields an empty list.
        """
        snap_dir = self.templates_file.parent / "snapshots"
        if not snap_dir.is_dir():
            return []
        entries = [
            {
                "name": p.name,
                "path": p,
                "size_bytes": p.stat().st_size,
                "modified": p.stat().st_mtime,
            }
            for p in snap_dir.iterdir()
            if p.is_file() and re.fullmatch(r"templates-\d{8}-\d{6}(\.\d+)?\.json", p.name)
        ]
        entries.sort(key=lambda e: (e["modified"], e["name"]), reverse=True)
        return entries

    def restore(self, name: str) -> dict:
        """Roll the store back to a snapshot.

        Takes a safety snapshot of the CURRENT state first, so a restore
        is itself reversible (the pre-restore state survives in
        ``snapshots/``). Then replaces the in-memory collection with the
        snapshot's contents and rewrites the store file.

        Args:
            name: Snapshot filename as reported by :meth:`list_snapshots`
                (e.g. ``templates-20260919-220000.json``). Must be a bare
                filename — separators or ``..`` are rejected.

        Returns:
            ``{"restored": <template count>, "snapshot": <path>,
            "safety_snapshot": <filename>}``

        Raises:
            ValueError: name is empty, contains separators or ``..``;
                snapshot is syntactically valid JSON but not a template
                store (store untouched).
            FileNotFoundError: no such snapshot.
            json.JSONDecodeError: snapshot is corrupt (store untouched).
        """
        if not name or os.sep in name or (os.altsep and os.altsep in name) or ".." in name:
            raise ValueError(f"Invalid snapshot name: {name!r}")
        snap_path = self.templates_file.parent / "snapshots" / name
        if not snap_path.is_file():
            raise FileNotFoundError(f"Snapshot not found: {name}")

        with open(snap_path, "r", encoding="utf-8") as f:
            data = json.load(f)  # syntax corruption raises before any write
        validated = TemplateCollection.from_dict(data)  # structural corruption raises before any write

        safety = self.snapshot()  # flush current state + copy: reversible
        self.collection = validated
        self._save_templates()
        return {
            "restored": len(self.collection.list_all()),
            "snapshot": str(snap_path),
            "safety_snapshot": safety.name,
        }

    def rename_variable(self, old: str, new: str, dry_run: bool = False) -> dict:
        """Rename a variable across all templates and persist.

        Affected templates get ``updated_at`` bumped and the store is
        saved once. A no-op rename (variable unused anywhere) skips
        both, mirroring the bulk tag discipline. ``dry_run=True``
        returns the same report without persisting or bumping.

        Args:
            old: Current variable name (``\\w+``).
            new: New variable name (``\\w+``), different from ``old``.
            dry_run: Preview only — never saves.

        Returns:
            Same report as ``TemplateCollection.rename_variable``.
        """
        report = self.collection.rename_variable(old, new, dry_run=dry_run)
        if not dry_run and report["total_replacements"]:
            for name in report["renamed"]:
                self.collection.get(name).update_timestamp()
            self._save_templates()
        return report

    def bulk_add_tags(self, names: list, tags: list) -> dict:
        """Add tags to multiple templates in one batch.

        Unlike ``add_tag``, unknown template names do not raise; they are
        reported in the result so one bad name cannot abort a batch.

        Args:
            names: Template names to modify.
            tags: Tags to add to each.

        Returns:
            {"updated": [names that gained at least one tag],
             "missing": [names not found]}
        """
        updated, missing = [], []
        for name in names:
            template = self.collection.get(name)
            if not template:
                missing.append(name)
                continue
            added = [t for t in tags if t not in template.tags]
            if added:
                template.tags.extend(added)
                template.update_timestamp()
                updated.append(name)
        if updated:
            self._save_templates()
        return {"updated": updated, "missing": missing}

    def bulk_remove_tags(self, names: list, tags: list) -> dict:
        """Remove tags from multiple templates in one batch.

        Unknown template names do not raise; they are reported in
        ``missing``.

        Args:
            names: Template names to modify.
            tags: Tags to remove from each.

        Returns:
            {"updated": [names that lost at least one tag],
             "missing": [names not found]}
        """
        updated, missing = [], []
        for name in names:
            template = self.collection.get(name)
            if not template:
                missing.append(name)
                continue
            before = len(template.tags)
            template.tags = [t for t in template.tags if t not in tags]
            if len(template.tags) != before:
                template.update_timestamp()
                updated.append(name)
        if updated:
            self._save_templates()
        return {"updated": updated, "missing": missing}

    def _merge_templates(self, templates, overwrite: bool) -> int:
        """Merge templates into the collection and persist.

        Shared merge loop for import_templates() / import_markdown_file():
        existing names are skipped unless overwrite=True.

        Args:
            templates: Iterable of Template objects to merge in.
            overwrite: Whether to overwrite existing templates.

        Returns:
            Number of templates actually imported.
        """
        imported_count = 0

        for template in templates:
            existing = self.collection.get(template.name)

            if existing and not overwrite:
                continue

            if existing:
                self.collection.delete(template.name)

            self.collection.add(template)
            imported_count += 1

        self._save_templates()
        return imported_count

    def import_templates(self, input_file: Path, overwrite: bool = False) -> int:
        """Import templates from a JSON file.

        Args:
            input_file: Input file path
            overwrite: Whether to overwrite existing templates

        Returns:
            Number of templates imported
        """
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported_collection = TemplateCollection.from_dict(data)
        return self._merge_templates(imported_collection.list_all(), overwrite)

    def export_markdown_file(self, output_file: Path) -> None:
        """Export the collection as a single markdown document - F16.

        Args:
            output_file: Destination path (written UTF-8).
        """
        output_file.write_text(self.collection.export_markdown(), encoding="utf-8")

    def import_markdown_file(self, input_file: Path, overwrite: bool = False) -> int:
        """Import templates from a markdown document - F16.

        Mirrors :meth:`import_templates`: templates whose names already
        exist are skipped unless ``overwrite`` is True.

        Args:
            input_file: Markdown file path (as written by
                ``export_markdown_file`` or hand-authored blocks).
            overwrite: Whether to overwrite existing templates.

        Returns:
            Number of templates imported.
        """
        text = input_file.read_text(encoding="utf-8")
        return self._merge_templates(self.collection.import_markdown(text), overwrite)

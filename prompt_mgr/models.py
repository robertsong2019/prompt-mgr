"""Data models for prompt templates."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import re


@dataclass
class Template:
    """Represents a prompt template."""

    name: str
    content: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        """Create template from dictionary."""
        return cls(
            name=data["name"],
            content=data["content"],
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            description=data.get("description"),
        )

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()

    def matches_query(self, query: str) -> bool:
        """Check if template matches a search query."""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower()
            or query_lower in self.content.lower()
            or (query_lower in self.description.lower() if self.description else False)
        )

    def has_tags(self, tags: List[str]) -> bool:
        """Check if template has all specified tags."""
        return all(tag in self.tags for tag in tags)

    def validate(self) -> List[str]:
        """Validate template for common issues.
        
        Returns:
            List of warning strings. Empty list means no issues.
        """
        warnings = []
        if not self.content.strip():
            warnings.append("Template content is empty or whitespace-only.")
        # Check for unclosed variable placeholders
        opens = self.content.count("{{")
        closes = self.content.count("}}")
        if opens != closes:
            warnings.append(f"Unbalanced variable syntax: {opens} '{{{{' but {closes} '}}}}'")
        # Check for single-brace (likely typo)
        for i, ch in enumerate(self.content):
            if ch == '{' and (i + 1 >= len(self.content) or self.content[i + 1] != '{'):
                if i == 0 or self.content[i - 1] != '{':
                    # Lone { not part of {{
                    warnings.append(f"Lone '{{' detected at position {i} — did you mean '{{{{'?" )
                    break  # one warning is enough
        return warnings

    def extract_variables(self) -> List[str]:
        """Extract variable names from template content."""
        import re
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, self.content)))

    def render(self, variables: dict) -> str:
        """Render the template with variable substitution.
        
        Args:
            variables: Dictionary of variable names and values
        
        Returns:
            Rendered template content
        
        Raises:
            ValueError: If required variables are missing
        """
        import re as _re
        
        required = self.extract_variables()
        missing = set(required) - set(variables.keys())
        if missing:
            raise ValueError(
                f"Missing variables: {', '.join(sorted(missing))}. "
                f"Required: {', '.join(sorted(required))}"
            )
        
        result = self.content
        for key, value in variables.items():
            pattern = r'\{\{' + _re.escape(key) + r'\}\}'
            # Literal replacement: lambda avoids re.sub interpreting
            # backslash escapes / group refs in values (e.g. r"\1", "\n").
            result = _re.sub(pattern, lambda _m, _v=value: _v, result)
        return result

    def to_markdown(self) -> str:
        """Export template as a formatted markdown block.
        
        Returns:
            Markdown-formatted string with template metadata and content.
        """
        lines = [
            f"## {self.name}",
            "",
        ]
        if self.description:
            lines.append(f"*{self.description}*")
            lines.append("")
        if self.tags:
            lines.append(f"**Tags:** {', '.join(self.tags)}")
            lines.append("")
        vars_ = self.extract_variables()
        if vars_:
            lines.append(f"**Variables:** {', '.join(sorted(vars_))}")
            lines.append("")
        lines.append(f"**Created:** {self.created_at}  ")
        lines.append(f"**Updated:** {self.updated_at}")
        lines.append("")
        # Fence safety: if the content itself contains lines of backticks, a
        # naive ``` fence would close early on import and silently drop the
        # lines in between. CommonMark rule: choose a fence strictly longer
        # than any backtick run at the start of a content line.
        import re
        runs = [len(m.group(0)) for m in re.finditer(r'^`+', self.content, re.M)]
        fence = "`" * max(3, (max(runs) + 1) if runs else 3)
        lines.append(fence)
        lines.append(self.content)
        lines.append(fence)
        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, text: str) -> "Template":
        """Create a template from a to_markdown()-format block — F16.

        Parses the block format emitted by ``to_markdown()``: an H2 name,
        optional italic description, optional bold Tags / Variables lines,
        Created/Updated timestamp lines, and a fenced code block holding
        the content. The Variables line is informational only — variables
        are re-derived from the content.

        Args:
            text: Markdown block (extra surrounding blank lines tolerated).

        Returns:
            Parsed Template.

        Raises:
            ValueError: If no ``## Name`` header is found or the code
                fence is never closed.
        """
        name = None
        description = None
        tags: List[str] = []
        created_at = None
        updated_at = None
        content_lines: List[str] = []
        fence_open = False
        fence_len = 0

        for raw in text.strip("\n").splitlines():
            stripped = raw.strip()
            if fence_open:
                # Close only on a backtick run at least as long as the
                # opening fence (CommonMark): a shorter run stays content.
                if (
                    stripped.startswith("`")
                    and set(stripped) == {"`"}
                    and len(stripped) >= fence_len
                ):
                    fence_open = False
                else:
                    content_lines.append(raw)
                continue
            if stripped.startswith("```"):
                fence_open = True
                fence_len = len(stripped)
            elif stripped.startswith("## ") and name is None:
                name = stripped[3:].strip()
            elif (
                description is None
                and len(stripped) > 1
                and stripped.startswith("*")
                and stripped.endswith("*")
                and not stripped.startswith("**")
            ):
                description = stripped[1:-1].strip()
            elif stripped.startswith("**Tags:**"):
                tags = [
                    t.strip()
                    for t in stripped[len("**Tags:**"):].split(",")
                    if t.strip()
                ]
            elif stripped.startswith("**Created:**"):
                created_at = stripped[len("**Created:**"):].strip()
            elif stripped.startswith("**Updated:**"):
                updated_at = stripped[len("**Updated:**"):].strip()
            # "**Variables:**" lines intentionally ignored (derived from content)

        if name is None:
            raise ValueError(
                "No '## Name' header found — not a template markdown block"
            )
        if fence_open:
            raise ValueError(f"Unterminated code fence in template '{name}'")

        kwargs = {}
        if created_at:
            kwargs["created_at"] = created_at
        if updated_at:
            kwargs["updated_at"] = updated_at
        return cls(
            name=name,
            content="\n".join(content_lines),
            tags=tags,
            description=description,
            **kwargs,
        )

    def to_json(self) -> str:
        """Serialize this template to a JSON string.

        Returns:
            JSON string representation of the template.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Template":
        """Create a template from a JSON string.

        Args:
            json_str: JSON string representation of a template.

        Returns:
            A Template instance.
        """
        return cls.from_dict(json.loads(json_str))

    def diff(self, other: "Template") -> dict:
        """Compare this template with another, return field-level differences.

        Args:
            other: The template to compare against.

        Returns:
            Dictionary mapping changed field names to their values.
            For scalar fields: ``{field: {"self": old, "other": new}}``
            For tags: ``{"tags": {"added": [...], "removed": [...]}}``
            Empty dict means templates are identical (excluding timestamps
            if they happen to match).
        """
        result = {}

        # Scalar fields
        for field_name in ("name", "content", "description"):
            self_val = getattr(self, field_name)
            other_val = getattr(other, field_name)
            if self_val != other_val:
                result[field_name] = {"self": self_val, "other": other_val}

        # Tags (set comparison)
        self_tags = set(self.tags)
        other_tags = set(other.tags)
        if self_tags != other_tags:
            result["tags"] = {
                "added": sorted(other_tags - self_tags),
                "removed": sorted(self_tags - other_tags),
            }

        return result

    def __str__(self) -> str:
        """String representation."""
        tags_str = ", ".join(self.tags) if self.tags else "no tags"
        return f"Template(name={self.name}, tags=[{tags_str}])"


@dataclass
class TemplateCollection:
    """Collection of templates."""

    templates: dict = field(default_factory=dict)

    def add(self, template: Template) -> None:
        """Add a template to the collection."""
        self.templates[template.name] = template

    def get(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        return self.templates.get(name)

    def delete(self, name: str) -> bool:
        """Delete a template by name."""
        if name in self.templates:
            del self.templates[name]
            return True
        return False

    def list_all(self) -> List[Template]:
        """List all templates."""
        return list(self.templates.values())

    def search(self, query: str = "", tags: Optional[List[str]] = None,
               regex: bool = False) -> List[Template]:
        """Search templates by query and/or tags.

        Args:
            query: Substring (default) or regular expression (regex=True).
            tags: If given, only templates having ALL of these tags.
            regex: Treat query as a Python regular expression matched
                (case-sensitively) against name, content and description.
                Invalid patterns raise ValueError.
        """
        pattern = None
        if regex and query:
            try:
                pattern = re.compile(query)
            except re.error as e:
                raise ValueError(f"Invalid regex {query!r}: {e}") from e

        results = []
        for template in self.templates.values():
            # Check query match
            if pattern is not None:
                matches_query = (
                    bool(pattern.search(template.name))
                    or bool(pattern.search(template.content))
                    or bool(pattern.search(template.description) if template.description else False)
                )
            else:
                matches_query = not query or template.matches_query(query)
            # Check tags match
            matches_tags = not tags or template.has_tags(tags)
            
            if matches_query and matches_tags:
                results.append(template)
        
        return results

    def diff(self, other: "TemplateCollection") -> dict:
        """Compare this collection with another.

        Args:
            other: The collection to compare against.

        Returns:
            Dictionary with three keys:
            - ``added``: sorted names present only in ``other``
            - ``removed``: sorted names present only in ``self``
            - ``changed``: mapping of shared names to their non-empty
              :meth:`Template.diff` results (content/description/tags)
        """
        added = sorted(set(other.templates) - set(self.templates))
        removed = sorted(set(self.templates) - set(other.templates))
        changed = {}
        for name in sorted(set(self.templates) & set(other.templates)):
            field_diff = self.templates[name].diff(other.templates[name])
            if field_diff:
                changed[name] = field_diff
        return {"added": added, "removed": removed, "changed": changed}

    def to_dict(self) -> dict:
        """Convert collection to dictionary."""
        return {
            "templates": {
                name: template.to_dict()
                for name, template in self.templates.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateCollection":
        """Create collection from dictionary."""
        collection = cls()
        for name, template_data in data.get("templates", {}).items():
            collection.add(Template.from_dict(template_data))
        return collection

    def to_json(self) -> str:
        """Convert collection to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "TemplateCollection":
        """Create collection from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def tag_summary(self) -> dict:
        """Return a summary of all tags and their template counts.
        
        Returns:
            Dictionary mapping tag name to number of templates using it.
            Sorted by count descending, then alphabetically.
        """
        freq = {}
        for template in self.templates.values():
            for tag in template.tags:
                freq[tag] = freq.get(tag, 0) + 1
        # Sort by count desc, then name asc
        return dict(sorted(freq.items(), key=lambda x: (-x[1], x[0])))

    def variables_inventory(self) -> dict:
        """Map each template variable to the templates that use it.

        Variable-level aggregation, complementing ``tag_summary`` (tag-level)
        and ``content_stats`` (character/token-level). Use it to assess the
        blast radius of renaming a variable before touching templates.

        Returns:
            Dictionary mapping variable name to ``{"count": n_templates,
            "templates": sorted list of template names}``. A variable used
            multiple times in one template counts once. Outer dict sorted
            by count descending, then variable name ascending.
        """
        usage = {}
        for template in self.templates.values():
            for var in template.extract_variables():
                usage.setdefault(var, []).append(template.name)
        return {
            var: {"count": len(names), "templates": sorted(names)}
            for var, names in sorted(
                usage.items(), key=lambda x: (-len(x[1]), x[0])
            )
        }

    def rename_variable(self, old: str, new: str, dry_run: bool = False) -> dict:
        """Rename a variable across all template contents.

        The write-side counterpart of ``variables_inventory`` (blast
        radius): replaces every ``{{old}}`` placeholder with ``{{new}}``.
        Delimiters are part of the match, so renaming ``topic`` never
        touches ``{{topic_id}}``.

        Args:
            old: Current variable name (``\\w+``).
            new: New variable name (``\\w+``), different from ``old``.
            dry_run: If True, report what would change without
                touching any content.

        Returns:
            {"renamed": {template_name: n_replacements},
             "total_replacements": n} — ``renamed`` sorted by template
            name. Renaming a variable nothing uses is a no-op, not an
            error.

        Raises:
            ValueError: If either name is not a valid variable name or
                the two names are identical.
        """
        import re as _re

        for label, name in (("old", old), ("new", new)):
            if not _re.fullmatch(r"\w+", str(name)):
                raise ValueError(f"Invalid {label} variable name: {name!r}")
        if old == new:
            raise ValueError("New variable name is identical to the old one")

        pattern = _re.compile(r"\{\{" + _re.escape(old) + r"\}\}")
        renamed, total = {}, 0
        for name in sorted(self.templates):
            template = self.templates[name]
            content, n = pattern.subn(
                lambda _m, _v="{{" + new + "}}": _v, template.content
            )
            if n:
                renamed[name] = n
                total += n
                if not dry_run:
                    template.content = content
        return {"renamed": renamed, "total_replacements": total}

    def sort_by(self, field: str = "name", reverse: bool = False) -> List[Template]:
        """Return templates sorted by a given field.

        Args:
            field: One of 'name', 'created_at', 'updated_at',
                   'content_length', 'tag_count'.
            reverse: If True, sort descending.

        Returns:
            New list of templates sorted by the specified field.

        Raises:
            ValueError: If field is not recognized.
        """
        valid_fields = {
            "name", "created_at", "updated_at",
            "content_length", "tag_count",
        }
        if field not in valid_fields:
            raise ValueError(
                f"Invalid sort field: {field}. "
                f"Valid fields: {', '.join(sorted(valid_fields))}"
            )

        def sort_key(t: Template):
            if field == "content_length":
                return len(t.content)
            if field == "tag_count":
                return len(t.tags)
            return getattr(t, field)

        return sorted(self.templates.values(), key=sort_key, reverse=reverse)

    def merge(self, other: "TemplateCollection") -> dict:
        """Merge another collection into this one.

        Templates unique to ``other`` are added directly.
        Templates in both are skipped (self wins by default).

        Args:
            other: The collection to merge from.

        Returns:
            Summary dict with keys:
            - ``added``: list of template names imported from other.
            - ``skipped``: list of names that already existed (kept self's version).
        """
        added: List[str] = []
        skipped: List[str] = []

        for template in other.list_all():
            if template.name in self.templates:
                skipped.append(template.name)
            else:
                self.templates[template.name] = template
                added.append(template.name)

        return {"added": sorted(added), "skipped": sorted(skipped)}

    def filter(self, predicate) -> List[Template]:
        """Filter templates by a predicate function.

        Args:
            predicate: A function ``(Template) -> bool``.

        Returns:
            List of templates matching the predicate.
        """
        return [t for t in self.templates.values() if predicate(t)]

    def group_by_tag(self) -> dict:
        """Group templates by their tags.

        Returns:
            Dictionary mapping each tag to a sorted list of template names.
            Templates without tags are grouped under the key ``"__untagged__"``.
        """
        groups: dict = {}
        for template in self.templates.values():
            if not template.tags:
                groups.setdefault("__untagged__", []).append(template.name)
            else:
                for tag in template.tags:
                    groups.setdefault(tag, []).append(template.name)
        # Sort names within each group
        return {tag: sorted(names) for tag, names in groups.items()}

    def search_by_variables(self, variables: List[str], match: str = "any") -> List[Template]:
        """Find templates that use specific variables.

        Args:
            variables: List of variable names to search for (without
                the ``{{``/``}}`` delimiters).
            match: One of ``"any"`` (default) or ``"all"``.
                "any" returns templates that use at least one of the
                specified variables; "all" returns only templates that
                use every specified variable.

        Returns:
            List of matching Templates.

        Raises:
            ValueError: If ``match`` is not ``"any"`` or ``"all"``.
        """
        if match not in ("any", "all"):
            raise ValueError(f"Invalid match mode: {match}. Use 'any' or 'all'.")

        want = set(variables)
        results = []
        for template in self.templates.values():
            have = set(template.extract_variables())
            if match == "all":
                if want <= have:
                    results.append(template)
            else:  # any
                if want & have:
                    results.append(template)
        return results

    def content_stats(self) -> dict:
        """Aggregate content statistics for the entire collection.

        Returns:
            Dictionary with:
            - ``total_chars``: total characters across all templates.
            - ``total_tokens``: total whitespace-split tokens.
            - ``avg_chars``: mean characters per template.
            - ``avg_tokens``: mean tokens per template.
            - ``longest``: name of template with most characters.
            - ``shortest``: name of template with fewest characters.
            - ``total_variables``: total unique variable slots.
        """
        templates = self.list_all()
        if not templates:
            return {
                "total_chars": 0, "total_tokens": 0,
                "avg_chars": 0, "avg_tokens": 0,
                "longest": None, "shortest": None,
                "total_variables": 0,
            }

        total_chars = sum(len(t.content) for t in templates)
        total_tokens = sum(len(t.content.split()) for t in templates)
        longest = max(templates, key=lambda t: len(t.content)).name
        shortest = min(templates, key=lambda t: len(t.content)).name
        total_vars = sum(len(t.extract_variables()) for t in templates)
        n = len(templates)

        return {
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "avg_chars": total_chars // n,
            "avg_tokens": total_tokens // n,
            "longest": longest,
            "shortest": shortest,
            "total_variables": total_vars,
        }

    def find_similar(self, name: str, top_k: int = 5) -> List[tuple]:
        """Find templates similar to the named template using token Jaccard.

        Args:
            name: The template to compare against.
            top_k: Maximum number of results to return.

        Returns:
            List of ``(template_name, jaccard_score)`` tuples sorted by
            score descending.  The target template itself is excluded.

        Raises:
            ValueError: If the named template does not exist.
        """
        if name not in self.templates:
            raise ValueError(f"Template not found: {name}")

        target_tokens = set(self.templates[name].content.lower().split())
        results = []

        for template in self.templates.values():
            if template.name == name:
                continue
            other_tokens = set(template.content.lower().split())
            if not target_tokens and not other_tokens:
                score = 1.0
            elif not target_tokens or not other_tokens:
                score = 0.0
            else:
                score = len(target_tokens & other_tokens) / len(target_tokens | other_tokens)
            results.append((template.name, round(score, 4)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def export_markdown(self, tags: Optional[List[str]] = None, sort_by: str = "name") -> str:
        """Export the collection as a single markdown document — F15.

        Args:
            tags: Optional tag filter — only templates with all the
                specified tags are exported (None exports everything).
            sort_by: Field to sort sections by: ``name`` (default),
                ``created`` (oldest first) or ``updated`` (most recently
                updated last).

        Returns:
            Markdown string: H1 title, generation timestamp, table of
            contents linking to each template section, then one
            ``to_markdown()`` block per template.
        """
        from datetime import datetime

        templates = self.list_all()
        if tags:
            templates = [t for t in templates if t.has_tags(tags)]

        sorters = {
            "name": lambda t: t.name,
            "created": lambda t: t.created_at,
            "updated": lambda t: t.updated_at,
        }
        key_fn = sorters.get(sort_by, sorters["name"])
        templates = sorted(templates, key=key_fn)

        title = "# Prompt Library"
        stamp = f"_Generated: {datetime.now().isoformat(timespec='seconds')}_"
        header = [title, "", stamp, ""]

        if not templates:
            return "\n".join(header + ["_No templates._"])

        toc = ["## Contents", ""]
        for t in templates:
            anchor = t.name.lower().replace(" ", "-")
            toc.append(f"- [{t.name}](#{anchor})")
        toc.append("")

        sections = [t.to_markdown() for t in templates]
        return "\n".join(header + toc + sections)

    def import_markdown(self, text: str) -> List[Template]:
        """Parse an exported markdown document back into templates — F16.

        Splits the document at H2 headers (skipping the ``Contents``
        section emitted by ``export_markdown()``; H2 lines inside code
        fences are treated as content, not boundaries) and parses each
        block with :meth:`Template.from_markdown`.

        The collection itself is not mutated — templates are returned so
        callers can inspect names and resolve conflicts before adding.

        Args:
            text: Markdown document (as produced by ``export_markdown()``,
                or any text with zero or more template blocks).

        Returns:
            Templates in document order. Documents without template
            blocks return an empty list.
        """
        blocks: List[List[str]] = []
        current: Optional[List[str]] = None  # None = between/skipped sections
        fence_open = False

        for raw in text.splitlines():
            stripped = raw.strip()
            if not fence_open and stripped.startswith("## "):
                if current is not None:
                    blocks.append(current)
                fence_open = False
                current = None if stripped == "## Contents" else [raw]
                continue
            if current is not None:
                if not fence_open and stripped.startswith("```"):
                    fence_open = True
                elif fence_open and stripped == "```":
                    fence_open = False
                current.append(raw)
        if current is not None:
            blocks.append(current)

        return [Template.from_markdown("\n".join(block)) for block in blocks]

    def recent(self, n: int = 10) -> List[Template]:
        """Return the n most recently updated templates.
        
        Args:
            n: Maximum number of templates to return.
        
        Returns:
            List of templates sorted by updated_at descending, capped at n.
        """
        return sorted(
            self.templates.values(),
            key=lambda t: t.updated_at,
            reverse=True,
        )[:n]

    def find_duplicates(self) -> dict:
        """Find templates with identical content.
        
        Returns:
            Dictionary mapping content hash to list of template names
            that share that content. Only includes entries with 2+ duplicates.
        """
        import hashlib
        
        groups = {}
        for template in self.templates.values():
            h = hashlib.sha256(template.content.encode()).hexdigest()
            groups.setdefault(h, []).append(template.name)
        
        return {
            h: sorted(names)
            for h, names in groups.items()
            if len(names) > 1
        }

"""Core manager for prompt templates."""

import json
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
        except (json.JSONDecodeError, KeyError) as e:
            # If file is corrupted, start fresh
            print(f"Warning: Could not load templates file: {e}")
            return TemplateCollection()

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
    ) -> List[Template]:
        """Search templates by query and/or tags.
        
        Args:
            query: Search query
            tags: Filter by tags (optional)
        
        Returns:
            List of matching templates
        """
        return self.collection.search(query=query, tags=tags)

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
        imported_count = 0
        
        for template in imported_collection.list_all():
            existing = self.collection.get(template.name)
            
            if existing and not overwrite:
                continue
            
            if existing:
                self.collection.delete(template.name)
            
            self.collection.add(template)
            imported_count += 1
        
        self._save_templates()
        return imported_count

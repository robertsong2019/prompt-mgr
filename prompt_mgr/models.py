"""Data models for prompt templates."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


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

    def extract_variables(self) -> List[str]:
        """Extract variable names from template content."""
        import re
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, self.content)))

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

    def search(self, query: str = "", tags: Optional[List[str]] = None) -> List[Template]:
        """Search templates by query and/or tags."""
        results = []
        for template in self.templates.values():
            # Check query match
            matches_query = not query or template.matches_query(query)
            # Check tags match
            matches_tags = not tags or template.has_tags(tags)
            
            if matches_query and matches_tags:
                results.append(template)
        
        return results

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

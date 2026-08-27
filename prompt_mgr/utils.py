"""Utility functions for prompt-mgr."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional


def get_data_dir() -> Path:
    """Get the data directory for storing templates."""
    data_dir = os.getenv("PROMPT_MGR_DATA_DIR")
    if data_dir:
        return Path(data_dir)
    return Path.home() / ".prompt-mgr"


def get_templates_file() -> Path:
    """Get the path to the templates file."""
    return get_data_dir() / "templates.json"


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)


def substitute_variables(template_content: str, variables: Dict[str, str]) -> str:
    """Substitute variables in template content.
    
    Args:
        template_content: Template content with {{variable}} placeholders
        variables: Dictionary of variable names and values
    
    Returns:
        Template content with variables substituted
    """
    result = template_content
    for key, value in variables.items():
        pattern = r'\{\{' + re.escape(key) + r'\}\}'
        # Use a function replacement so `value` is treated literally;
        # a string replacement would interpret backslashes (e.g. C:\Users
        # or \1) as escape/group references and crash with re.error.
        result = re.sub(pattern, lambda m, v=value: v, result)
    return result


def parse_variable_assignments(var_list: List[str]) -> Dict[str, str]:
    """Parse variable assignments from command-line arguments.
    
    Args:
        var_list: List of "key=value" strings
    
    Returns:
        Dictionary of variable names and values
    """
    variables = {}
    for var in var_list:
        if "=" not in var:
            raise ValueError(f"Invalid variable assignment: {var}. Expected format: key=value")
        key, value = var.split("=", 1)
        variables[key.strip()] = value.strip()
    return variables


def validate_template_name(name: str) -> bool:
    """Validate a template name.
    
    Args:
        name: Template name to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    # Only allow alphanumeric characters, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name))


def format_template_table(templates: List, show_content: bool = False) -> str:
    """Format templates as a table string.
    
    Args:
        templates: List of Template objects
        show_content: Whether to show full content
    
    Returns:
        Formatted table string
    """
    if not templates:
        return "No templates found."
    
    lines = []
    for template in templates:
        lines.append(f"\n📌 {template.name}")
        if template.description:
            lines.append(f"   Description: {template.description}")
        lines.append(f"   Tags: {', '.join(template.tags) if template.tags else 'none'}")
        if show_content:
            lines.append(f"   Content:\n{template.content}")
        else:
            # Show preview of content (first 100 chars)
            preview = template.content[:100]
            if len(template.content) > 100:
                preview += "..."
            lines.append(f"   Preview: {preview}")
        lines.append(f"   Variables: {', '.join(template.extract_variables()) or 'none'}")
    
    return "\n".join(lines)

# API Reference

This document provides detailed documentation for the Prompt Manager Python API.

## Table of Contents

- [Core Classes](#core-classes)
  - [PromptManager](#promptmanager)
  - [Template](#template)
  - [TemplateCollection](#templatecollection)
- [Utility Functions](#utility-functions)
- [Exceptions](#exceptions)

---

## Core Classes

### PromptManager

The main class for managing prompt templates.

#### Constructor

```python
PromptManager()
```

Initializes the prompt manager and loads existing templates from storage.

**Example:**
```python
from prompt_mgr import PromptManager

mgr = PromptManager()
```

#### Methods

##### `add_template(name, content, tags=None, description=None)`

Add a new template to the collection.

**Parameters:**
- `name` (str): Unique template name (alphanumeric, hyphens, underscores only)
- `content` (str): Template content with optional `{{variable}}` placeholders
- `tags` (List[str], optional): List of tags for categorization
- `description` (str, optional): Template description

**Returns:**
- `Template`: The created template object

**Raises:**
- `ValueError`: If name is invalid or template already exists

**Example:**
```python
template = mgr.add_template(
    name="code-review",
    content="Review this {{language}} code:\n{{code}}",
    tags=["coding", "review"],
    description="Template for code review prompts"
)
```

##### `get_template(name)`

Retrieve a template by name.

**Parameters:**
- `name` (str): Template name

**Returns:**
- `Template | None`: Template if found, None otherwise

**Example:**
```python
template = mgr.get_template("code-review")
if template:
    print(template.content)
```

##### `update_template(name, content=None, tags=None, description=None)`

Update an existing template.

**Parameters:**
- `name` (str): Template name
- `content` (str, optional): New content
- `tags` (List[str], optional): New tags
- `description` (str, optional): New description

**Returns:**
- `Template`: Updated template

**Raises:**
- `ValueError`: If template doesn't exist

**Example:**
```python
updated = mgr.update_template(
    name="code-review",
    content="Review this {{language}} code for {{focus}}:\n{{code}}",
    tags=["coding", "review", "security"]
)
```

##### `delete_template(name)`

Delete a template.

**Parameters:**
- `name` (str): Template name

**Returns:**
- `bool`: True if deleted, False if not found

**Example:**
```python
if mgr.delete_template("old-template"):
    print("Template deleted")
```

##### `list_templates(tags=None)`

List all templates, optionally filtered by tags.

**Parameters:**
- `tags` (List[str], optional): Filter by tags

**Returns:**
- `List[Template]`: List of templates

**Example:**
```python
# List all
all_templates = mgr.list_templates()

# Filter by tags
coding_templates = mgr.list_templates(tags=["coding"])
```

##### `search_templates(query, tags=None)`

Search templates by query and/or tags.

**Parameters:**
- `query` (str): Search query (searches name, content, description)
- `tags` (List[str], optional): Filter by tags

**Returns:**
- `List[Template]`: Matching templates

**Example:**
```python
results = mgr.search_templates("review", tags=["coding"])
for template in results:
    print(f"- {template.name}")
```

##### `render_template(name, variables)`

Render a template with variable values.

**Parameters:**
- `name` (str): Template name
- `variables` (Dict[str, str]): Variable values

**Returns:**
- `str`: Rendered template content

**Raises:**
- `ValueError`: If template not found or missing variables

**Example:**
```python
rendered = mgr.render_template(
    name="code-review",
    variables={
        "language": "python",
        "code": "def hello():\n    print('world')",
        "focus": "security"
    }
)
print(rendered)
```

##### `export_templates(output_file)`

Export templates to a JSON file.

**Parameters:**
- `output_file` (Path): Output file path

**Example:**
```python
from pathlib import Path
mgr.export_templates(Path("my-templates.json"))
```

##### `import_templates(input_file, overwrite=False)`

Import templates from a JSON file.

**Parameters:**
- `input_file` (Path): Input file path
- `overwrite` (bool): Whether to overwrite existing templates (default: False)

**Returns:**
- `int`: Number of templates imported

**Example:**
```python
count = mgr.import_templates(
    Path("shared-templates.json"),
    overwrite=True
)
print(f"Imported {count} templates")
```

---

### Template

Represents a single prompt template.

#### Attributes

- `name` (str): Template name
- `content` (str): Template content with `{{variable}}` placeholders
- `tags` (List[str]): List of tags
- `created_at` (str): ISO timestamp of creation
- `updated_at` (str): ISO timestamp of last update
- `description` (str, optional): Template description

#### Methods

##### `to_dict()`

Convert template to dictionary.

**Returns:**
- `dict`: Dictionary representation

**Example:**
```python
data = template.to_dict()
```

##### `from_dict(data)` (classmethod)

Create template from dictionary.

**Parameters:**
- `data` (dict): Dictionary data

**Returns:**
- `Template`: Created template

**Example:**
```python
template = Template.from_dict({
    "name": "my-template",
    "content": "Hello {{name}}",
    "tags": ["greeting"]
})
```

##### `update_timestamp()`

Update the `updated_at` timestamp to current time.

**Example:**
```python
template.update_timestamp()
```

##### `matches_query(query)`

Check if template matches a search query.

**Parameters:**
- `query` (str): Search query

**Returns:**
- `bool`: True if matches

**Example:**
```python
if template.matches_query("review"):
    print("Found a review template")
```

##### `has_tags(tags)`

Check if template has all specified tags.

**Parameters:**
- `tags` (List[str]): Tags to check

**Returns:**
- `bool`: True if has all tags

**Example:**
```python
if template.has_tags(["coding", "security"]):
    print("This is a coding security template")
```

##### `extract_variables()`

Extract variable names from template content.

**Returns:**
- `List[str]`: List of variable names

**Example:**
```python
vars = template.extract_variables()
# If content is "Hello {{name}}, welcome to {{place}}"
# vars will be ["name", "place"]
```

---

### TemplateCollection

Collection of templates with search and filtering capabilities.

#### Methods

##### `add(template)`

Add a template to the collection.

**Parameters:**
- `template` (Template): Template to add

**Example:**
```python
collection.add(template)
```

##### `get(name)`

Get a template by name.

**Parameters:**
- `name` (str): Template name

**Returns:**
- `Template | None`: Template if found

**Example:**
```python
template = collection.get("my-template")
```

##### `delete(name)`

Delete a template by name.

**Parameters:**
- `name` (str): Template name

**Returns:**
- `bool`: True if deleted

**Example:**
```python
collection.delete("old-template")
```

##### `list_all()`

List all templates.

**Returns:**
- `List[Template]`: All templates

**Example:**
```python
all_templates = collection.list_all()
```

##### `search(query, tags=None)`

Search templates by query and/or tags.

**Parameters:**
- `query` (str): Search query
- `tags` (List[str], optional): Filter by tags

**Returns:**
- `List[Template]`: Matching templates

**Example:**
```python
results = collection.search("review", tags=["coding"])
```

##### `to_dict()`

Convert collection to dictionary.

**Returns:**
- `dict`: Dictionary representation

##### `from_dict(data)` (classmethod)

Create collection from dictionary.

**Parameters:**
- `data` (dict): Dictionary data

**Returns:**
- `TemplateCollection`: Created collection

##### `to_json()`

Convert collection to JSON string.

**Returns:**
- `str`: JSON string

##### `from_json(json_str)` (classmethod)

Create collection from JSON string.

**Parameters:**
- `json_str` (str): JSON string

**Returns:**
- `TemplateCollection`: Created collection

---

## Utility Functions

### `get_templates_file()`

Get the path to the templates storage file.

**Returns:**
- `Path`: Path to templates.json

**Default location:** `~/.prompt-mgr/templates.json`

**Example:**
```python
from prompt_mgr.utils import get_templates_file

file_path = get_templates_file()
print(f"Templates stored at: {file_path}")
```

### `ensure_data_dir()`

Ensure the data directory exists.

**Example:**
```python
from prompt_mgr.utils import ensure_data_dir

ensure_data_dir()  # Creates ~/.prompt-mgr/ if needed
```

### `substitute_variables(content, variables)`

Substitute variables in template content.

**Parameters:**
- `content` (str): Template content with `{{variable}}` placeholders
- `variables` (Dict[str, str]): Variable values

**Returns:**
- `str`: Content with variables replaced

**Example:**
```python
from prompt_mgr.utils import substitute_variables

result = substitute_variables(
    "Hello {{name}}, welcome to {{place}}",
    {"name": "Alice", "place": "Wonderland"}
)
# Result: "Hello Alice, welcome to Wonderland"
```

### `validate_template_name(name)`

Validate a template name.

**Parameters:**
- `name` (str): Template name to validate

**Returns:**
- `bool`: True if valid

**Rules:**
- Only alphanumeric characters, hyphens, and underscores
- Must not be empty

**Example:**
```python
from prompt_mgr.utils import validate_template_name

if validate_template_name("my-template_v2"):
    print("Valid name")
```

---

## Exceptions

### `ValueError`

Raised in the following cases:
- Invalid template name
- Template already exists (when adding)
- Template not found (when updating/deleting/rendering)
- Missing required variables (when rendering)

**Example handling:**
```python
try:
    mgr.add_template("invalid name!", "content")
except ValueError as e:
    print(f"Error: {e}")
```

---

## Environment Variables

### `PROMPT_MGR_DATA_DIR`

Customize the data storage directory.

**Default:** `~/.prompt-mgr`

**Example:**
```bash
export PROMPT_MGR_DATA_DIR=/custom/path
prompt-mgr list
```

---

## Complete Example

```python
from prompt_mgr import PromptManager

# Initialize manager
mgr = PromptManager()

# Add a template
mgr.add_template(
    name="email-template",
    content="Dear {{name}},\n\n{{message}}\n\nBest regards,\n{{sender}}",
    tags=["email", "communication"],
    description="Professional email template"
)

# Render the template
email = mgr.render_template(
    "email-template",
    {
        "name": "Alice",
        "message": "Thank you for your contribution!",
        "sender": "Bob"
    }
)

print(email)

# Search templates
results = mgr.search_templates("email", tags=["communication"])
for template in results:
    print(f"Found: {template.name}")

# Export templates
from pathlib import Path
mgr.export_templates(Path("my-templates-backup.json"))
```

---

## See Also

- [Tutorial](TUTORIAL.md) - Step-by-step guide
- [Architecture](ARCHITECTURE.md) - Design decisions
- [README](../README.md) - Quick start guide

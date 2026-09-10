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

##### `clone_template(source_name, new_name)`

Copy a template under a new name. The clone's tag list is independent from the original.

**Parameters:**
- `source_name` (str): Template to copy
- `new_name` (str): Name for the copy

**Returns:**
- `Template`: The newly created clone

**Raises:**
- `ValueError`: If source doesn't exist or `new_name` is already taken

##### `rename_template(old_name, new_name)`

Rename a template, preserving content, tags, and description.

**Parameters:**
- `old_name` (str): Current name
- `new_name` (str): New name

**Returns:**
- `Template`: The renamed template

##### `add_tag(name, tag)` / `remove_tag(name, tag)`

Add or remove a single tag without rewriting the full template.

**Returns:**
- `Template`: The updated template

##### `recent_templates(n=10)`

Return the `n` most recently updated templates (newest first).

**Returns:**
- `List[Template]`

##### `get_stats()`

Aggregate statistics for the whole collection.

**Returns:**
- `dict`: Keys `total`, `tag_frequency`, `total_variables`, `avg_content_length`, `templates_with_variables`

**Example:**
```python
stats = mgr.get_stats()
print(f"{stats['total']} templates, {stats['total_variables']} variable slots")
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

##### `render(variables)`

Render the template directly on the model (no manager needed). Substitution is literal-safe: backslashes in variable values are preserved as-is.

**Parameters:**
- `variables` (dict): Variable name → value

**Returns:**
- `str`: Rendered content

##### `validate()`

Check the template for common issues.

**Returns:**
- `List[str]`: Warning strings; empty list means no issues detected

**Example:**
```python
for warning in template.validate():
    print("⚠", warning)
# e.g. "Unbalanced variable syntax: 2 '{{' but 1 '}}'"
```

##### `to_markdown()`

Format the template as a markdown block (name, tags, content fence).

The content fence is **dynamic** (CommonMark fence semantics): if the content itself contains lines of backticks, the fence is chosen one longer than the longest backtick run at a content line start (`max(3, longest + 1)`), so the block can always be re-imported without data loss. Content without backtick lines gets the classic exact-3 fence.

**Returns:**
- `str`

##### `from_markdown(md_block)` (classmethod)

Parse a `to_markdown()` block back into a template (inverse of `to_markdown()`; also used by `TemplateCollection.import_markdown()`).

The content fence closes only on a backtick run **at least as long as** the opening fence — a shorter backtick run inside the content is kept as content, not treated as the fence end. Blocks exported by older versions (exact-3 fences, no backtick lines in content) parse unchanged.

**Parameters:**
- `md_block` (str): Markdown block as produced by `to_markdown()`

**Returns:**
- `Template`

**Example:**
```python
md = t.to_markdown()          # fence auto-sizes if content has ``` lines
t2 = Template.from_markdown(md)  # round-trips without dropping lines
```

##### `to_json()` / `from_json(json_str)` (classmethod)

Single-template (de)serialization, independent of any collection.

##### `diff(other)`

Compare with another template field by field.

**Returns:**
- `dict`: Scalar fields as `{field: {"self": old, "other": new}}`; tags as `{"tags": {"added": [...], "removed": [...]}}`. Empty dict means identical.

**Example:**
```python
changes = v1.diff(v2)
if changes:
    print("Changed fields:", list(changes))
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

##### `tag_summary()`

Tag usage counts, sorted by frequency descending.

**Returns:**
- `dict`: tag → count

##### `sort_by(field="name", reverse=False)`

Return templates sorted by `name`, `created_at`, `updated_at`, `content_length`, or `tag_count`.

**Returns:**
- `List[Template]`

##### `merge(other)`

Merge another collection into this one. Templates unique to `other` are added; name collisions are skipped (self wins).

**Returns:**
- `dict`: `{"added": [...], "skipped": [...]}`

##### `filter(predicate)`

Filter by an arbitrary predicate function.

**Returns:**
- `List[Template]`

##### `group_by_tag()`

Group templates by tag; templates without tags are grouped under their own key.

**Returns:**
- `dict`: tag → `List[Template]`

##### `search_by_variables(variables, match="any")`

Find templates that require the given variables. `match="any"` needs at least one; `match="all"` needs every one.

**Returns:**
- `List[Template]`

**Example:**
```python
# Templates renderable with just {"code", "focus"}
candidates = collection.search_by_variables(["code", "focus"], match="all")
```

##### `content_stats()`

Aggregate content metrics across the collection.

**Returns:**
- `dict`: Keys `total_chars`, `total_tokens`, `avg_chars`, `avg_tokens`, `longest`, `shortest`, `total_variables`

##### `find_similar(name, top_k=5)`

Token Jaccard similarity search against the named template (target excluded).

**Returns:**
- `List[tuple]`: `(template_name, score)` pairs, score descending, scores rounded to 4 decimals

**Raises:**
- `ValueError`: If the named template doesn't exist

##### `export_markdown(tags=None, sort_by="name")`

Export the collection (optionally tag-filtered) as a single markdown document with a table of contents.

**Returns:**
- `str`

##### `recent(n=10)`

The `n` most recently updated templates, newest first.

##### `find_duplicates()`

Detect templates with identical content.

**Returns:**
- `dict`: SHA-256 content hash → sorted list of template names sharing that content. Only groups of 2+ are included.

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

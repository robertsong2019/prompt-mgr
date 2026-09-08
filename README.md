# Prompt Manager (prompt-mgr)

A lightweight CLI tool for managing AI prompt templates with variable substitution, categorization, and search.

## Features

- ✨ **Template Management**: Add, view, edit, rename, clone, and delete prompt templates
- 🏷️ **Categorization**: Organize templates with tags (add/remove tags individually)
- 🔍 **Search**: Find templates by name, content, tags, or required variables
- 📝 **Variable Substitution**: Use `{{variable}}` syntax for dynamic prompts (literal-backslash safe)
- 🎨 **Rendering**: Render final prompts with variable values
- 🧰 **Template Tools**: `diff()`, `validate()`, `to_markdown()`, `from_markdown()`, similarity search, duplicate detection
- 📊 **Statistics**: Collection stats, content metrics, and tag summaries
- 📦 **Import/Export**: Share templates between systems (JSON and single-doc Markdown)

## Installation

```bash
# Clone the repository
git clone https://github.com/robertsong2019/prompt-mgr.git
cd prompt-mgr

# Install dependencies
pip install -e .
```

## Quick Start

```bash
# Add a new template
prompt-mgr add code-review --content "Review this code: {{code}}" --tags "coding,review"

# List all templates
prompt-mgr list

# Search templates
prompt-mgr search --tags "coding"

# Render a template
prompt-mgr render code-review --var code="def hello(): print('world')"

# Edit a template
prompt-mgr edit code-review

# Delete a template
prompt-mgr delete code-review
```

## Template Format

Templates are stored as JSON:

```json
{
  "name": "code-review",
  "content": "Review this code: {{code}}\n\nFocus on: {{focus}}",
  "tags": ["coding", "review"],
  "created_at": "2026-03-18T22:00:00+08:00",
  "updated_at": "2026-03-18T22:00:00+08:00"
}
```

## Commands

### `prompt-mgr add <name>`
Add a new template.

```bash
prompt-mgr add my-template --content "Hello {{name}}" --tags "greeting"
```

Options:
- `--content`: Template content (required)
- `--tags`: Comma-separated tags
- `--editor`: Open editor for content (optional)

### `prompt-mgr list`
List all templates.

```bash
prompt-mgr list --tags "coding" --format json
```

Options:
- `--tags`: Filter by tags
- `--format`: Output format (table/json)

### `prompt-mgr search <query>`
Search templates.

```bash
prompt-mgr search "review" --tags "coding"
```

Options:
- `--tags`: Filter by tags

### `prompt-mgr show <name>`
Show full template details (content, tags, variables, timestamps).

```bash
prompt-mgr show my-template
```

### `prompt-mgr recent`
Show recently updated templates.

```bash
prompt-mgr recent --limit 5
```

Options:
- `--limit`: Number of templates to show (default: 10)

### `prompt-mgr render <name>`
Render a template with variables.

```bash
prompt-mgr render code-review --var code="def foo(): pass" --var focus="security"
```

Options:
- `--var`: Variable assignments (key=value)
- `--output/-o`: Write rendered result to a file instead of stdout

```bash
prompt-mgr render code-review --var code="..." --output out.txt
```

### `prompt-mgr edit <name>`
Edit a template.

```bash
prompt-mgr edit my-template
```

### `prompt-mgr delete <name>`
Delete a template.

```bash
prompt-mgr delete my-template
```

### `prompt-mgr export`
Export templates to JSON.

```bash
prompt-mgr export --output templates.json
```

### `prompt-mgr import`
Import templates from JSON.

```bash
prompt-mgr import --input templates.json
```

## Variable Substitution

Use `{{variable}}` syntax for dynamic content:

```bash
# Template: "Translate {{text}} from {{source}} to {{target}}"
prompt-mgr render translate --var text="Hello" --var source="en" --var target="zh"

# Output: "Translate Hello from en to zh"
```

## Use Cases

### 1. Code Review Templates
```bash
prompt-mgr add code-review \
  --content "Review this {{language}} code:\n```{{language}}\n{{code}}\n```\n\nFocus on: {{focus}}" \
  --tags "coding,review"
```

### 2. Translation Templates
```bash
prompt-mgr add translate \
  --content "Translate the following text from {{source}} to {{target}}:\n\n{{text}}" \
  --tags "translation"
```

### 3. Summary Templates
```bash
prompt-mgr add summarize \
  --content "Summarize the following text in {{word_count}} words:\n\n{{text}}" \
  --tags "summarization"
```

## Python API Highlights

Everything the CLI does is available programmatically via `PromptManager`, plus a set of collection/model utilities. Full details in the [API Reference](docs/API_REFERENCE.md).

### Manager operations

```python
from prompt_mgr import PromptManager

mgr = PromptManager()

mgr.clone_template("code-review", "code-review-v2")   # copy with independent tags
mgr.rename_template("old-name", "new-name")            # rename, preserving data
mgr.add_tag("code-review", "urgent")                   # tag management without full update
mgr.remove_tag("code-review", "urgent")
mgr.recent_templates(n=5)                               # most recently updated
mgr.get_stats()                                         # total, tag_frequency, avg_content_length, ...
```

### Template model

```python
t = mgr.get_template("code-review")

t.render({"code": "...", "focus": "security"})  # render directly on the model
t.validate()                                     # warn on empty content / unbalanced {{ }}
t.to_markdown()                                  # formatted markdown block
Template.from_markdown(md_block)                 # parse a to_markdown() block back — F16
t.to_json() / Template.from_json(s)              # single-template (de)serialization
t.diff(other)                                    # field-level changes + tag added/removed
```

### Collection utilities

```python
from prompt_mgr import PromptManager

collection = PromptManager()._load_templates()  # or build a TemplateCollection directly

collection.find_duplicates()                     # templates with identical content
collection.find_similar("code-review", top_k=3)  # token Jaccard similarity
templates = collection.search_by_variables(["code"], match="any")   # by required vars
collection.content_stats()                       # chars/tokens/vars, longest/shortest
collection.sort_by("updated_at", reverse=True)   # name/created_at/updated_at/content_length/tag_count
collection.group_by_tag()                        # tag -> templates (untagged grouped separately)
collection.merge(other)                          # {"added": [...], "skipped": [...]}
collection.export_markdown(tags=["coding"])      # single-doc export with TOC
collection.import_markdown(md_doc)               # parse exported markdown back into templates — F16
```

## Data Storage

Templates are stored in `~/.prompt-mgr/templates.json` by default.

Customize storage location:
```bash
export PROMPT_MGR_DATA_DIR=/custom/path
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/robertsong2019/prompt-mgr.git
cd prompt-mgr

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black prompt_mgr/
```

### Project Structure

```
prompt-mgr/
├── prompt_mgr/
│   ├── __init__.py
│   ├── cli.py          # CLI commands
│   ├── manager.py      # Core logic
│   ├── models.py       # Data models (Template, TemplateCollection)
│   └── utils.py        # Utilities
├── docs/               # API reference, tutorial, architecture guide
├── tests/
├── features.md         # Feature backlog & changelog notes
├── README.md
├── setup.py
└── requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[API Reference](docs/API_REFERENCE.md)** - Complete Python API documentation with examples
- **[Tutorial](docs/TUTORIAL.md)** - Step-by-step guide from basics to advanced usage
- **[Architecture](docs/ARCHITECTURE.md)** - Design decisions and technical details

### Quick Links

- **Getting Started**: See [Tutorial - Getting Started](docs/TUTORIAL.md#getting-started)
- **API Usage**: See [API Reference - Core Classes](docs/API_REFERENCE.md#core-classes)
- **Design Philosophy**: See [Architecture - Design Principles](docs/ARCHITECTURE.md#design-principles)

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/)
- Inspired by the need for better AI prompt management

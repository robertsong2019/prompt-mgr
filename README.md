# Prompt Manager (prompt-mgr)

A lightweight CLI tool for managing AI prompt templates with variable substitution, categorization, and search.

## Features

- ✨ **Template Management**: Add, view, edit, and delete prompt templates
- 🏷️ **Categorization**: Organize templates with tags
- 🔍 **Search**: Find templates by name, content, or tags
- 📝 **Variable Substitution**: Use `{{variable}}` syntax for dynamic prompts
- 🎨 **Rendering**: Render final prompts with variable values
- 📦 **Import/Export**: Share templates between systems

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

### `prompt-mgr render <name>`
Render a template with variables.

```bash
prompt-mgr render code-review --var code="def foo(): pass" --var focus="security"
```

Options:
- `--var`: Variable assignments (key=value)

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
│   ├── models.py       # Data models
│   └── utils.py        # Utilities
├── tests/
│   ├── test_manager.py
│   └── test_cli.py
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

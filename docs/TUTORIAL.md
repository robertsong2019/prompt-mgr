# Prompt Manager Tutorial

Welcome to the Prompt Manager tutorial! This guide will walk you through everything you need to know to effectively manage your AI prompts.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Basic Operations](#basic-operations)
4. [Advanced Features](#advanced-features)
5. [Real-World Examples](#real-world-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is Prompt Manager?

Prompt Manager is a CLI tool and Python library for managing AI prompt templates. It helps you:

- ✅ Store and organize prompts
- ✅ Use variables for dynamic content
- ✅ Categorize with tags
- ✅ Search and filter quickly
- ✅ Share templates between projects

### Why Use Prompt Manager?

**Problem:** You keep copy-pasting the same prompts, or you can't find that perfect prompt you wrote last week.

**Solution:** A centralized, searchable library of reusable prompt templates with variables.

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/robertsong2019/prompt-mgr.git
cd prompt-mgr

# Install in development mode
pip install -e .
```

### Verify Installation

```bash
prompt-mgr --help
```

You should see the list of available commands.

### Your First Template

Let's create a simple greeting template:

```bash
prompt-mgr add greeting \
  --content "Hello {{name}}! Welcome to {{place}}." \
  --tags "greeting,basic"
```

Now render it:

```bash
prompt-mgr render greeting \
  --var name="Alice" \
  --var place="Wonderland"
```

Output:
```
Hello Alice! Welcome to Wonderland.
```

Congratulations! You've created and used your first template! 🎉

---

## Basic Operations

### 1. Adding Templates

#### Simple Template

```bash
prompt-mgr add simple \
  --content "Translate this to French: {{text}}"
```

#### Template with Multiple Tags

```bash
prompt-mgr add code-review \
  --content "Review this {{language}} code:\n\`\`\`{{language}}\n{{code}}\n\`\`\`\n\nFocus on: {{focus}}" \
  --tags "coding,review,quality"
```

#### Using an Editor

For longer templates, use the `--editor` flag:

```bash
prompt-mgr add long-template --editor
```

This opens your default editor (from `$EDITOR` environment variable).

### 2. Listing Templates

#### List All

```bash
prompt-mgr list
```

Output:
```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Name           ┃ Tags                   ┃ Description       ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ code-review    │ coding, review, quality│ (none)            │
│ greeting       │ greeting, basic        │ (none)            │
│ simple         │ (none)                 │ (none)            │
└────────────────┴────────────────────────┴───────────────────┘
```

#### Filter by Tags

```bash
prompt-mgr list --tags "coding"
```

#### JSON Output

```bash
prompt-mgr list --format json
```

### 3. Searching Templates

Search across names, content, and descriptions:

```bash
# Search for "review"
prompt-mgr search review

# Search with tag filter
prompt-mgr search review --tags "coding"
```

### 4. Viewing Template Details

```bash
prompt-mgr get code-review
```

Output:
```
Name: code-review
Tags: coding, review, quality
Created: 2026-03-18T22:00:00+08:00
Updated: 2026-03-18T22:00:00+08:00

Content:
-------
Review this {{language}} code:
```{{language}}
{{code}}
```

Focus on: {{focus}}
```

### 5. Editing Templates

```bash
# Edit in your editor
prompt-mgr edit code-review

# Or update specific fields
prompt-mgr update code-review \
  --tags "coding,review,quality,security"
```

### 6. Deleting Templates

```bash
prompt-mgr delete old-template
```

You'll be asked for confirmation unless you use `--force`.

---

## Advanced Features

### Variable Substitution

Variables are enclosed in `{{double_braces}}`:

```bash
# Template with 3 variables
prompt-mgr add email \
  --content "Dear {{name}},\n\n{{message}}\n\nBest regards,\n{{sender}}"
```

Render with all variables:

```bash
prompt-mgr render email \
  --var name="Alice" \
  --var message="Thank you for your help!" \
  --var sender="Bob"
```

**Missing Variables:**

If you forget a variable, you'll get an error:

```bash
prompt-mgr render email --var name="Alice"
```

Error:
```
Error: Missing variables: message, sender
Required: name, message, sender
```

### Import/Export

#### Export Templates

```bash
# Export all templates
prompt-mgr export --output my-templates.json

# Export specific templates (future feature)
prompt-mgr export --output coding.json --tags "coding"
```

#### Import Templates

```bash
# Import without overwriting
prompt-mgr import --input shared-templates.json

# Import and overwrite existing
prompt-mgr import --input shared-templates.json --overwrite
```

**Use Case:** Share templates with your team or sync between machines.

### Custom Storage Location

By default, templates are stored in `~/.prompt-mgr/templates.json`.

Customize with environment variable:

```bash
export PROMPT_MGR_DATA_DIR=/path/to/custom/location
prompt-mgr list
```

---

## Real-World Examples

### Example 1: Code Review Assistant

Create a comprehensive code review template:

```bash
prompt-mgr add full-code-review \
  --content "You are a code reviewer. Review this {{language}} code and provide feedback on:

1. **Code Quality**: Readability, maintainability, best practices
2. **Performance**: Identify potential bottlenecks
3. **Security**: Look for vulnerabilities or security issues
4. **Testing**: Suggest test cases if missing

Code:
\`\`\`{{language}}
{{code}}
\`\`\`

Additional context: {{context}}

Provide a structured review with:
- Summary
- Critical issues (if any)
- Suggestions for improvement
- Positive aspects" \
  --tags "coding,review,comprehensive"
```

**Usage:**

```bash
prompt-mgr render full-code-review \
  --var language="python" \
  --var code="def process_data(data):
    results = []
    for item in data:
        results.append(transform(item))
    return results" \
  --var context="This function is called frequently in a data processing pipeline"
```

### Example 2: Technical Documentation Generator

```bash
prompt-mgr add generate-docs \
  --content "Generate technical documentation for the following {{type}}:

\`\`\`
{{code}}
\`\`\`

Include:
- Brief description
- Parameters (if function/method)
- Return value (if applicable)
- Example usage
- Edge cases or notes

Format: Markdown" \
  --tags "documentation,automation"
```

### Example 3: Multi-Language Translator

```bash
prompt-mgr add translate \
  --content "Translate the following text from {{source_lang}} to {{target_lang}}:

{{text}}

Preserve:
- Tone and style
- Technical terms (if any)
- Formatting (if any)" \
  --tags "translation,i18n"
```

**Usage:**

```bash
prompt-mgr render translate \
  --var source_lang="English" \
  --var target_lang="Chinese" \
  --var text="The quick brown fox jumps over the lazy dog."
```

### Example 4: Bug Report Analyzer

```bash
prompt-mgr add analyze-bug \
  --content "Analyze this bug report and provide:

1. **Root Cause Analysis**: What's likely causing the issue?
2. **Reproduction Steps**: Are they clear? What's missing?
3. **Impact Assessment**: How severe is this bug?
4. **Suggested Fix**: What should be changed?
5. **Test Case**: How to verify the fix?

Bug Report:
---
Title: {{title}}
Description: {{description}}
Steps to Reproduce: {{steps}}
Expected: {{expected}}
Actual: {{actual}}
Environment: {{environment}}
---

Provide actionable insights." \
  --tags "debugging,analysis,quality"
```

### Example 5: Meeting Summary Template

```bash
prompt-mgr add meeting-summary \
  --content "Summarize this meeting transcript:

{{transcript}}

Provide:
1. **Key Decisions**: What was decided?
2. **Action Items**: Who needs to do what?
3. **Open Questions**: What's still unresolved?
4. **Next Steps**: What happens next?

Format as a structured meeting summary." \
  --tags "productivity,meetings"
```

---

## Best Practices

### 1. Naming Conventions

Use clear, descriptive names:

✅ **Good:**
- `code-review-python`
- `email-professional`
- `translate-en-to-zh`

❌ **Bad:**
- `cr1`
- `temp`
- `test-template`

### 2. Tagging Strategy

Create a consistent tagging system:

- **By purpose:** `coding`, `writing`, `translation`
- **By domain:** `frontend`, `backend`, `devops`
- **By complexity:** `simple`, `comprehensive`
- **By status:** `production`, `experimental`

Example:

```bash
prompt-mgr add api-docs \
  --content "..." \
  --tags "documentation,api,backend,production"
```

### 3. Variable Naming

Use descriptive variable names:

✅ **Good:**
- `{{programming_language}}`
- `{{target_audience}}`
- `{{code_snippet}}`

❌ **Bad:**
- `{{x}}`
- `{{var1}}`
- `{{temp}}`

### 4. Template Organization

**Group related templates:**

```bash
# Code review family
code-review-simple
code-review-comprehensive
code-review-security

# Translation family
translate-general
translate-technical
translate-casual
```

**Use descriptions:**

```bash
prompt-mgr add code-review \
  --content "..." \
  --description "Comprehensive code review for production code"
```

### 5. Version Control

Export your templates regularly:

```bash
# Weekly backup
prompt-mgr export --output backups/templates-$(date +%Y%m%d).json

# Commit to git
git add backups/
git commit -m "Weekly template backup"
```

---

## Troubleshooting

### Template Not Found

**Error:**
```
Error: Template not found: my-template
```

**Solution:**
```bash
# List all templates to check the name
prompt-mgr list

# Search for it
prompt-mgr search "my"
```

### Missing Variables

**Error:**
```
Error: Missing variables: language, code
```

**Solution:**

Check what variables are needed:

```bash
# View template
prompt-mgr get my-template

# Extract variables (Python)
python -c "
from prompt_mgr import PromptManager
mgr = PromptManager()
template = mgr.get_template('my-template')
print('Required variables:', template.extract_variables())
"
```

### Invalid Template Name

**Error:**
```
Error: Invalid template name: my template!
```

**Solution:**

Use only alphanumeric characters, hyphens, and underscores:

✅ `my-template_v2`
❌ `my template!`
❌ `my.template`

### Corrupted Data File

**Error:**
```
Warning: Could not load templates file: ...
```

**Solution:**

```bash
# Backup current file
cp ~/.prompt-mgr/templates.json ~/.prompt-mgr/templates.json.bak

# Start fresh (WARNING: loses all templates)
rm ~/.prompt-mgr/templates.json

# Or restore from backup
prompt-mgr import --input backups/templates-20260318.json
```

---

## Advanced Tips

### 1. Using with Python Scripts

```python
from prompt_mgr import PromptManager

mgr = PromptManager()

# Batch process
languages = ["python", "javascript", "go"]
for lang in languages:
    prompt = mgr.render_template(
        "language-intro",
        {"language": lang}
    )
    print(f"=== {lang} ===")
    print(prompt)
    print()
```

### 2. Integration with AI APIs

```python
import openai
from prompt_mgr import PromptManager

mgr = PromptManager()

# Get template
prompt = mgr.render_template(
    "code-review",
    {
        "language": "python",
        "code": "def hello():\n    print('world')",
        "focus": "performance"
    }
)

# Send to OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

print(response.choices[0].message.content)
```

### 3. Template Inheritance

Create base templates and extend them:

```python
# Base template
mgr.add_template(
    "base-email",
    "{{greeting}}\n\n{{body}}\n\n{{signature}}",
    tags=["email", "base"]
)

# Specific email (you'd compose these in your code)
greeting = "Dear {{name}},"
body = "Thank you for {{action}}."
signature = "Best regards,\n{{sender}}"

# Compose
full_template = f"{greeting}\n\n{body}\n\n{signature}"
mgr.add_template("thank-you-email", full_template, tags=["email", "gratitude"])
```

---

## Next Steps

- 📖 Read the [API Reference](API_REFERENCE.md)
- 🏗️ Learn about the [Architecture](ARCHITECTURE.md)
- 🚀 Check out more examples in the `examples/` directory
- 💡 Share your templates with the community!

---

## Getting Help

- **GitHub Issues:** https://github.com/robertsong2019/prompt-mgr/issues
- **Documentation:** This tutorial + API Reference + Architecture docs
- **Community:** Share templates and tips with other users

Happy prompting! 🎉

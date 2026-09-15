# Changelog

All notable changes to Prompt Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **F22 variable rename** (Sep 15, 2026): `TemplateCollection.rename_variable(old, new)` / `PromptManager.rename_variable()` + CLI `rename-variable` — replace `{{old}}` with `{{new}}` across all templates (write-side of F20's blast-radius inventory); delimiter-anchored so `topic` never touches `{{topic_id}}`; unused variable is a no-op report, affected templates get `updated_at` bumped with a single save
- **F20 variables inventory** (Sep 9, 2026): `TemplateCollection.variables_inventory()` / `PromptManager.variables_inventory()` + CLI `variables` — variable-level usage aggregation (variable → count + sorted template names, count desc / name asc); check the blast radius before renaming a variable
- **F21 bulk tag operations** (Sep 9, 2026): `PromptManager.bulk_add_tags()` / `bulk_remove_tags()` — batch tag changes across templates; unknown names reported in `missing` instead of raising, single save at end, no-op edits skip `updated_at` bump
- **F19 regex search** (Sep 8, 2026): `TemplateCollection.search()` / `PromptManager.search_templates()` gain `regex=True`; CLI `search --regex` — case-sensitive pattern matching over name/content/description, invalid patterns rejected
- **F18 render to file** (Sep 8, 2026): `PromptManager.render_to_file()` + CLI `render --output/-o` — write rendered result to a file (parents auto-created; failures leave no file behind)
- **F17 collection diff** (Sep 8, 2026): `TemplateCollection.diff(other)` — added/removed names + per-template field-level changes, building on `Template.diff()`
- **F16 markdown round-trip** (Aug 30, 2026): `Template.from_markdown()` / `TemplateCollection.import_markdown()` / `PromptManager.export_markdown_file()` / `import_markdown_file()`; CLI `export` / `import` gain `--format markdown`
- **F1-F15 feature series** (Aug 2026): `Template.render()` / `to_markdown()` / `diff()` / `validate()` / `to_json()` / `from_json()`, `TemplateCollection.find_duplicates()` / `sort_by()` / `merge()` / `filter()` / `group_by_tag()` / `find_similar()` (token Jaccard) / `search_by_variables()` (any/all) / `content_stats()` / `export_markdown()` (TOC + tag filter)
- Manager: `clone_template()`, `rename_template()`, `add_tag()` / `remove_tag()`, `recent_templates()`, `get_stats()`
- CLI: `show` and `recent` commands
- Test suite 52 → 427 tests (99% coverage)
- Comprehensive documentation suite
  - API Reference (docs/API_REFERENCE.md)
  - Tutorial (docs/TUTORIAL.md)
  - Architecture guide (docs/ARCHITECTURE.md)
  - Documentation index (docs/README.md)
- Contributing guidelines (CONTRIBUTING.md)
- Changelog (CHANGELOG.md)

### Changed
- Enhanced README with documentation links
- `render()` substitution is literal-safe: backslashes in variable values are no longer interpreted as regex escapes

### Fixed
- **Markdown fence safety** (Sep 11, 2026): `to_markdown()` / `from_markdown()` round-trip could **silently drop content lines** when a template's content contained a bare ```` ``` ```` line — the export fence closed early on re-import and everything up to the next ```` ``` ```` vanished with no error. Fix follows CommonMark fence semantics:
  - `to_markdown()` picks a fence one longer than the longest backtick run at any content line start (`max(3, longest + 1)`); exact-3 fences unchanged for content without backtick lines
  - `from_markdown()` closes only on a backtick run **at least as long as** the opening fence; shorter runs are kept as content
  - Back-compat: all pre-fix blocks (exact-3 fences) round-trip byte-identically; caught red-first with 3 of 6 new tests verified failing on the old code (409 tests total)
- Literal backslash corruption in variable substitution (`re.sub` replacement semantics → lambda-based literal substitution)

## [1.0.0] - 2026-03-18

### Added
- Initial release
- Core features:
  - Template management (add, edit, delete, list)
  - Variable substitution with `{{variable}}` syntax
  - Tag-based categorization
  - Search functionality
  - Import/Export capabilities
  - JSON-based storage
- CLI interface with commands:
  - `prompt-mgr add` - Add new template
  - `prompt-mgr list` - List templates
  - `prompt-mgr search` - Search templates
  - `prompt-mgr render` - Render template with variables
  - `prompt-mgr edit` - Edit template
  - `prompt-mgr delete` - Delete template
  - `prompt-mgr export` - Export templates to JSON
  - `prompt-mgr import` - Import templates from JSON
- Python API:
  - `PromptManager` class for programmatic access
  - `Template` dataclass for template representation
  - `TemplateCollection` for managing multiple templates
- Data validation:
  - Template name validation
  - Variable extraction and validation
  - Duplicate detection
- Error handling:
  - Meaningful error messages
  - Graceful handling of corrupted data files
- Configuration:
  - Customizable storage location via `PROMPT_MGR_DATA_DIR`
  - Editor integration via `$EDITOR` environment variable
- Output formatting:
  - Table format (default)
  - JSON format (for scripting)

### Security
- Input validation for all user inputs
- Safe file operations
- No execution of template content

## [0.1.0] - 2026-03-15

### Added
- Project initialization
- Basic project structure
- Initial CLI scaffold

---

## Version History Summary

| Version | Date       | Description                    |
|---------|------------|--------------------------------|
| 1.0.0   | 2026-03-18 | Initial stable release         |
| 0.1.0   | 2026-03-15 | Project initialization         |

---

## Future Roadmap

### v1.1.0 (Planned)
- [ ] Template versioning
- [ ] Template categories/hierarchy
- [x] Enhanced search with regex support (F19, Sep 2026)

### v1.2.0 (Planned)
- [ ] Template composition
- [ ] Plugin system
- [ ] Remote storage backends (S3, GCS)

### v2.0.0 (Future)
- [ ] Template marketplace
- [ ] AI-powered template suggestions
- [ ] Web UI
- [ ] Multi-user support

---

For more details on planned features, see [Architecture - Future Enhancements](docs/ARCHITECTURE.md#future-enhancements).

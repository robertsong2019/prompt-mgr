# Changelog

All notable changes to Prompt Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **F1-F15 feature series** (Aug 2026): `Template.render()` / `to_markdown()` / `diff()` / `validate()` / `to_json()` / `from_json()`, `TemplateCollection.find_duplicates()` / `sort_by()` / `merge()` / `filter()` / `group_by_tag()` / `find_similar()` (token Jaccard) / `search_by_variables()` (any/all) / `content_stats()` / `export_markdown()` (TOC + tag filter)
- Manager: `clone_template()`, `rename_template()`, `add_tag()` / `remove_tag()`, `recent_templates()`, `get_stats()`
- CLI: `show` and `recent` commands
- Test suite 52 → 327 tests (99% coverage)
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
- [ ] Enhanced search with regex support

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

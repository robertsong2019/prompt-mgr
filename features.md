# prompt-mgr Feature Backlog

## ✅ Existing Features
- Template CRUD (add, get, update, delete, list)
- Template search by query and/or tags
- Template variable extraction (`{{variable}}` syntax)
- Template rendering with variable substitution
- JSON import/export
- Clone template (source → new name, independent tags)
- Collection statistics (total, tag_frequency, avg_content_length, templates_with_variables)
- tag_summary (sorted tag frequency)
- matches_query / has_tags on Template model
- CLI interface with rich table output

## 🔲 Feature Backlog

### Template Model
- [x] **F1**: `Template.render(variables)` — render directly on model (eliminates manager dependency) ✅ 2026-08-01
- [x] **F2**: `Template.to_markdown()` — export as formatted markdown block ✅ 2026-08-01
- [x] **F3**: `Template.diff(other)` — compare two templates, return field-level differences ✅ 2026-08-02

### Collection Operations
- [x] **F4**: `TemplateCollection.find_duplicates()` — detect templates with identical content ✅ 2026-08-01
- [x] **F5**: `TemplateCollection.sort_by(field, reverse)` — sort by name/created_at/updated_at/content_length/tag_count ✅ 2026-08-04
- [x] **F6**: `TemplateCollection.merge(other)` — merge two collections, report conflicts ✅ 2026-08-04

### Manager Operations
- [x] **F7**: `PromptManager.rename_template(old, new)` — rename preserving data ✅ 2026-08-08
- [x] **F8**: `PromptManager.add_tag(name, tag)` / `remove_tag(name, tag)` — tag management without full update ✅ 2026-08-08

## Priorities
**Tonight:** F1 (render on model), F2 (to_markdown), F4 (find_duplicates)

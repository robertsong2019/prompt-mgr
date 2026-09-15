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

### Collection & Model (Round 3)
- [x] **F9**: `TemplateCollection.filter(predicate)` — filter by arbitrary predicate function ✅ 2026-08-09
- [x] **F10**: `Template.to_json()` / `Template.from_json()` — single-template JSON serialization ✅ 2026-08-09
- [x] **F11**: `TemplateCollection.group_by_tag()` — group templates by tag, un tagged grouped separately ✅ 2026-08-09

### Collection & Model (Round 4)
- [x] **F12**: `TemplateCollection.find_similar(name, top_k)` — token Jaccard similarity search ✅ 2026-08-10
- [x] **F13**: `TemplateCollection.search_by_variables(vars, match)` — find templates by required variables (any/all) ✅ 2026-08-10
- [x] **F14**: `TemplateCollection.content_stats()` — aggregate content metrics (chars/tokens/vars/longest/shortest) ✅ 2026-08-10
- [x] **F15**: `TemplateCollection.export_markdown(tags, sort_by)` — single-doc export with TOC + tag filter + sorting ✅ 2026-08-17
- [x] **F16**: `Template.from_markdown()` + `TemplateCollection.import_markdown()` + `PromptManager.export_markdown_file/import_markdown_file` + CLI `export/import --format markdown` — full markdown round-trip ✅ 2026-08-30
- [x] **F17**: `TemplateCollection.diff(other)` — added/removed names + field-level changes for shared templates ✅ 2026-09-08
- [x] **F18**: `PromptManager.render_to_file(name, vars, output)` + CLI `render --output` — render directly to a file ✅ 2026-09-08
- [x] **F19**: `TemplateCollection.search(query, regex=True)` + `PromptManager.search_templates(regex)` + CLI `search --regex` — regex search ✅ 2026-09-08
- [x] **F20**: `TemplateCollection.variables_inventory()` + `PromptManager.variables_inventory()` + CLI `variables` — variable-level usage aggregation (blast radius before renaming a variable) ✅ 2026-09-09
- [x] **F21**: `PromptManager.bulk_add_tags(names, tags)` / `bulk_remove_tags(names, tags)` — batch tag ops, unknown names reported not raised ✅ 2026-09-09
- [x] **F22**: `TemplateCollection.rename_variable(old, new)` / `PromptManager.rename_variable()` + CLI `rename-variable` — write-side of F20 inventory: `{{old}}`→`{{new}}` across templates, delimiter-anchored, no-op on unused ✅ 2026-09-15
- [x] **F23**: `rename_variable(dry_run=True)` + CLI `--dry-run` — blast-radius preview without writing ✅ 2026-09-15
- [x] **Bugfix**: `Template.render()` backslash corruption — literal lambda substitution ✅ 2026-08-17

## Priorities
**Tonight:** F1 (render on model), F2 (to_markdown), F4 (find_duplicates)

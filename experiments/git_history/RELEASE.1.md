# 🔖 Release Notes: `v1.0.0-final`

## 🚀 Highlights
- **Standards-aware evaluation** of YAML systems data against user-defined JSON standards.
- **AI-powered diff summary** using Ollama (`mistral`) with multi-language support.
- **Schema-aware formatting** via local `schema` directories.
- **Markdown summary export** for easy documentation and reviews.
- **CLI-first UX** with config file overrides and flexible commit diff selection.

## ✅ New Features
- Standards matching logic with:
  - Support for `criticality` and `group` constraints
  - Smart fallback parsing of flattened or nested YAML structures
  - Per-system debug output for traceable evaluation
- Requirements validation engine (e.g. `SLA`, `RTO`, `RPO`)
- Git diff grouping by file type with support for YAML-only view
- Integrated AI summary via Ollama with Russian output by default
- Support for `.gitignore`-like pattern matching
- Markdown generation with alert markers for potentially breaking changes
- Schema loading for enriched prompt context (if `--use-schema` is enabled)

## 🛠 Fixes and Improvements
- Fixed YAML parsing from diffs by preserving indentation
- Improved fallback logic for nested YAML blocks (`kadzo.v2023.systems`)
- Better error handling and debug logs across parsing, loading, and evaluation
- Clean refactor of standards evaluation loop and normalization logic
- Logging verbosity now makes system-by-system matching traceable

## 🧪 Tested Scenarios
- New YAML files added to tracked paths
- Matching systems against criticality/group standards
- Invalid YAML files gracefully skipped
- AI summaries generated and exported to Markdown
- Configurable via both CLI and `config.yaml`
# 🔖 Release Notes: `v1.1.0`

## 🚀 Highlights
- **AI-Powered Standards Evaluation**: Introduced side-by-side semantic analysis using LLM (Mistral via Ollama) for all systems matched against defined standards.
- **Markdown Summary Enhancement**: Clean, tabular Markdown output with `Rule Match`, `AI Opinion`, and `Verdict` columns.
- **Conflict Flagging**: If AI disagrees with rule-based logic, results are highlighted as `⚠️ Conflict` for manual review.

## ✅ New Features
- AI matcher (`check_with_ai`) added to evaluate standards using natural language understanding.
- Markdown report now includes detailed comparison of rule logic vs AI reasoning.
- AI-powered requirements validation (prototype stage) available via `check_requirements_with_ai()`.
- Systems with incomplete data are skipped with clear debug logs.

## 🛠 Fixes & Improvements
- Patched YAML parsing logic to preserve indentation from diffs.
- Improved fallback for system block detection in nested structures (`kadzo.v2023.systems`, `entities.*`).
- Refined schema loading and debug printing.
- Bugfixes for uninitialized variables (`hits`, `ai_records`) and safe handling of `NoneType` AI responses.

## 📦 Summary Output Example
```
| System                                 | Rule Match | AI Opinion | Verdict        |
|----------------------------------------|------------|------------|----------------|
| ecogroup.berezka.systems.berezka       | ✅         | ✅ Yes     | ✅ Confirmed   |
| ecogroup.berezka.systems.berezka.catalog | ✅       | ❌ No      | ⚠️ Conflict    |
```

> ⚠️ Conflicts indicate systems that passed rule-based checks but may need manual review based on AI interpretation.

## 🧪 Verified Against
- 3 YAML files across schema + application layers
- 19 systems evaluated
- 5 matches, 1 AI conflict
- AI reasoning validated against prompt expectations

---

Built with ❤️ and a few dozen debug prints.
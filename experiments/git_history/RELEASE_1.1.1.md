# 🔖 Patch Notes: `v1.1.1`

## 🛠 Improvements
- Restored **AI-generated diff summaries** to the top of the Markdown report.
- Integrated both AI commit summaries and **Standards Evaluation: Rule vs AI** into a unified report.
- Localized summary output to Russian:
  - Section headers (`Изменения в коммите`, `Оценка стандартов`)
  - Verdicts (`Подтверждено`, `Конфликт`)
- Added handling for missing AI responses and unstructured systems.

## 🧪 Verified
- Markdown summary now includes both YAML change context and standards evaluation.
- Validated on 3 files, 19 systems, with matching and conflicting results.

---

Built as a refinement to v1.1.0 after feedback on markdown completeness and localization.
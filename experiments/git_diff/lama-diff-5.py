import ollama
import re
from rich import print


def parse_git_diff(diff_file):
    """Parses a Git diff and extracts OLD (Removed) and NEW (Added) text blocks, tracking affected objects."""

    old_text = []
    new_text = []
    affected_objects = set()  # Store objects referenced in `tag` fields

    with open(diff_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()

        if line.startswith("- ") and not line.startswith("---"):  # Removed content
            old_text.append(line[2:].strip())

        elif line.startswith("+ ") and not line.startswith("+++"):  # Added content
            new_text.append(line[2:].strip())

        # Detect tag-based dependencies
        if "tag:" in line:
            tag_match = re.search(r'tag:\s*(\S+)', line)
            if tag_match:
                affected_objects.add(tag_match.group(1))  # Extract the referenced object

    return "\n".join(old_text), "\n".join(new_text), affected_objects


def analyze_impact_with_ai(old_text, new_text, affected_objects):
    """Uses AI to analyze cross-domain impact based on modified objects and dependencies."""

    if not old_text and not new_text:
        return "**No significant changes detected.**"

    prompt = f"""
    You are analyzing changes in a system where objects reference each other via `tag` fields.
    Identify the impact of changes on other objects.

    **Changed Objects:**
    {old_text if old_text else "[No removed content]"}

    {new_text if new_text else "[No added content]"}

    **Affected Objects (via tag dependency):**
    {', '.join(affected_objects) if affected_objects else "[No affected objects detected]"}

    **Rules:**
    - Explain how the modifications impact referenced objects.
    - Identify whether the affected objects require updates.
    - Format the response in Markdown.
    """

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])

    return response["message"]["content"].strip()


def format_output(old_text, new_text, ai_summary, affected_objects):
    """Formats the Git diff output with Markdown support and impact analysis."""

    markdown_output = f"""
# 🚀 AI-Powered Git Diff Analysis

## 🔍 AI Summary of Changes:
{ai_summary}

---

## ❌ OLD (Removed) Content:
```diff
{old_text if old_text else "[No removed content.]"}
```

## ✅ NEW (Added) Content:
```diff
{new_text if new_text else "[No added content.]"}
```

---

## 🔗 Impact Analysis: Affected Objects
- {', '.join(affected_objects) if affected_objects else "No linked objects affected."}
"""

    print(markdown_output)

    return markdown_output  # Return markdown if needed for reports


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with actual Git diff file

    old_text, new_text, affected_objects = parse_git_diff(diff_file)
    ai_summary = analyze_impact_with_ai(old_text, new_text, affected_objects)
    markdown_report = format_output(old_text, new_text, ai_summary, affected_objects)

    # Optionally save the report for GitHub comments or documentation
    with open("it_diff_report.md", "w", encoding="utf-8") as md_file:
        md_file.write(markdown_report)

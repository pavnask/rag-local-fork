import ollama
import re
from rich import print


def parse_git_diff(diff_file):
    """Parses a Git diff and extracts OLD (Removed) and NEW (Added) text blocks."""

    old_text = []
    new_text = []

    with open(diff_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()

        if line.startswith("- ") and not line.startswith("---"):  # Removed content
            old_text.append(line[2:].strip())

        elif line.startswith("+ ") and not line.startswith("+++"):  # Added content
            new_text.append(line[2:].strip())

    return "\n".join(old_text), "\n".join(new_text)


def compare_text_with_ai(old_text, new_text):
    """Uses AI to compare OLD and NEW text blocks and summarize the differences."""

    if not old_text and not new_text:
        return "**No significant changes detected.**"

    prompt = f"""
    Compare the following OLD and NEW text blocks and summarize the key differences.

    **OLD TEXT (Removed):**
    {old_text if old_text else "[No removed content]"}

    **NEW TEXT (Added):**
    {new_text if new_text else "[No added content]"}

    **Rules:**
    - Identify key differences (modifications, additions, deletions).
    - Detect patterns: renaming, reformatting, structural changes.
    - Format the response in Markdown.
    - Do NOT rewrite the text—just summarize changes.
    - Provide a high-level summary followed by detailed analysis.
    """

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])

    return response["message"]["content"].strip()


def format_output(old_text, new_text, ai_summary):
    """Formats the Git diff output with Markdown support for better readability."""

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
"""

    print(markdown_output)

    return markdown_output  # Return markdown if needed for reports


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with actual Git diff file

    old_text, new_text = parse_git_diff(diff_file)
    ai_summary = compare_text_with_ai(old_text, new_text)
    markdown_report = format_output(old_text, new_text, ai_summary)

    # Optionally save the report for use in GitHub comments or documentation
    with open("git_diff_report.md", "w", encoding="utf-8") as md_file:
        md_file.write(markdown_report)

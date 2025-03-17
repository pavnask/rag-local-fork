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

    # Debugging Output
    print("\n🛠️ [bold yellow]DEBUG: Extracted Text Blocks[/bold yellow]")
    print("\n[red]❌ OLD (Removed) Content:[/red]")
    print("\n".join(old_text) if old_text else "[gray]No removed content.[/gray]")

    print("\n[green]✅ NEW (Added) Content:[/green]")
    print("\n".join(new_text) if new_text else "[gray]No added content.[/gray]")

    return "\n".join(old_text), "\n".join(new_text)


def compare_text_with_ai(old_text, new_text):
    """Uses Ollama to compare OLD and NEW text blocks and summarize the differences."""

    if not old_text and not new_text:
        return "[gray]No significant changes detected.[/gray]"

    prompt = f"""
    Compare the following OLD and NEW text blocks and summarize the key differences.

    **OLD TEXT (Removed):**
    {old_text if old_text else "[No removed content]"}

    **NEW TEXT (Added):**
    {new_text if new_text else "[No added content]"}

    **Rules:**
    - Identify key differences (modifications, additions, deletions).
    - Do NOT rewrite the text—just summarize changes.
    - Keep the response concise and factual.
    - Avoid unnecessary explanations.
    """

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])

    return response["message"]["content"].strip()


def format_output(old_text, new_text, ai_summary):
    """Formats the Git diff output along with AI-generated comparison."""

    print("\n🚀 [bold yellow]Git Diff Summary:[/bold yellow]\n")

    print("[red]❌ OLD (Removed) Content:[/red]")
    print(old_text if old_text else "[gray]No removed content.[/gray]")

    print("\n[green]✅ NEW (Added) Content:[/green]")
    print(new_text if new_text else "[gray]No added content.[/gray]")

    print("\n[blue]🔍 AI Analysis of Changes:[/blue]")
    print(ai_summary if ai_summary else "[gray]No significant changes detected.[/gray]")


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with actual Git diff file

    old_text, new_text = parse_git_diff(diff_file)
    ai_summary = compare_text_with_ai(old_text, new_text)
    format_output(old_text, new_text, ai_summary)
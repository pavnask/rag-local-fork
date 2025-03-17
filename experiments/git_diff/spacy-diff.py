import os
import re
import spacy
import difflib
from rich import print

MODEL_DIR = "spacy_model"  # Folder to store the model

# Define colors for different changes
REMOVED_ICON = "❌ [bold red]REMOVED[/bold red]"
ADDED_ICON = "✅ [bold green]ADDED[/bold green]"
CHANGED_ICON = "🔄 [bold yellow]CHANGED[/bold yellow]"
FILE_ICON = "📂 [bold blue]File Changed:[/bold blue]"


def load_or_train_spacy_model():
    """Loads the spaCy model if it exists; otherwise, creates and saves a blank model."""
    if os.path.exists(MODEL_DIR):
        print("✅ [green]Loading existing spaCy model...[/green]")
        return spacy.load(MODEL_DIR)  # Load from disk
    else:
        print("🚀 [blue]Training and saving new spaCy model...[/blue]")
        nlp = spacy.blank("en")  # Create a blank English model
        nlp.to_disk(MODEL_DIR)  # Save to disk for future use
        return nlp  # Return the new model


def highlight_changes(old, new):
    """Uses difflib to highlight only the changed parts in a modified line."""
    old_words = old.split()
    new_words = new.split()
    diff = list(difflib.ndiff(old_words, new_words))

    highlighted_old, highlighted_new = [], []

    for word in diff:
        if word.startswith("- "):  # Removed word
            highlighted_old.append(f"[red]{word[2:]}[/red]")
        elif word.startswith("+ "):  # Added word
            highlighted_new.append(f"[green]{word[2:]}[/green]")
        else:  # Unchanged word
            highlighted_old.append(word[2:])
            highlighted_new.append(word[2:])

    return " ".join(highlighted_old), " ".join(highlighted_new)


def parse_git_diff(diff_file):
    """Reads a Git diff file and formats it into a human-readable structure."""

    with open(diff_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    nlp = load_or_train_spacy_model()  # Load trained spaCy model

    readable_output = []
    removed_lines = []
    added_lines = []
    unchanged_lines = []
    old_line_num = 0
    new_line_num = 0

    for i, line in enumerate(lines):
        doc = nlp(line.strip())  # Process the line using spaCy

        if line.startswith("diff --git"):
            if removed_lines or added_lines or unchanged_lines:
                readable_output.append(format_columns(removed_lines, added_lines, unchanged_lines))
            readable_output.append(f"\n{FILE_ICON} {line.split()[-1]}")
            removed_lines = []
            added_lines = []
            unchanged_lines = []
            old_line_num = 0
            new_line_num = 0

        elif line.startswith("@@"):
            match = re.search(r'-(\d+),?\d* \+(\d+),?\d*', line)
            if match:
                old_line_num = int(match.group(1))
                new_line_num = int(match.group(2))
            removed_lines = []
            added_lines = []
            unchanged_lines = []

        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(f"{ADDED_ICON} {new_line_num}: {line[1:].strip()}")
            new_line_num += 1

        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(f"{REMOVED_ICON} {old_line_num}: {line[1:].strip()}")
            old_line_num += 1

        else:
            old_text = line.strip()
            new_text = lines[i + 1].strip() if i + 1 < len(lines) else ""

            if new_text.startswith("+") and old_text.replace("-", "").strip() == new_text.replace("+", "").strip():
                old_highlight, new_highlight = highlight_changes(old_text.replace("-", "").strip(),
                                                                 new_text.replace("+", "").strip())
                removed_lines.append(f"{CHANGED_ICON} {old_line_num}: {old_highlight}")
                added_lines.append(f"{CHANGED_ICON} {new_line_num}: {new_highlight}")
                new_line_num += 1
            else:
                unchanged_lines.append(f" {old_line_num}: {line.strip()}")
                old_line_num += 1
                new_line_num += 1

    if removed_lines or added_lines or unchanged_lines:
        readable_output.append(format_columns(removed_lines, added_lines, unchanged_lines))

    return "\n".join(readable_output)


def format_columns(removed, added, unchanged):
    """Formats removed, added, and unchanged lines into a readable format."""
    max_width = max(
        [len(line) for line in removed] +
        [len(line) for line in added] +
        [len(line) for line in unchanged] + [10]
    )

    header = f"{'[bold red]OLD (Removed)[/bold red]':<{max_width}} | {'[bold green]NEW (Added)[/bold green]':<{max_width}}"
    separator = "-" * (max_width * 2 + 3)

    formatted_lines = [header, separator]
    for old, new in zip(
            removed + [""] * (len(added) - len(removed)),
            added + [""] * (len(removed) - len(added))
    ):
        formatted_lines.append(f"{old:<{max_width}} | {new:<{max_width}}")

    for unchanged in unchanged:
        formatted_lines.append(f"{unchanged:<{max_width}} | {unchanged:<{max_width}}")

    return "\n".join(formatted_lines)


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with your actual Git diff file
    human_readable_diff = parse_git_diff(diff_file)
    print(human_readable_diff)
import re
import spacy
from rich import print


# Load spaCy model
def load_or_train_spacy_model():
    """Loads or creates a spaCy model for text processing."""
    if spacy.util.is_package("en_core_web_sm"):
        return spacy.load("en_core_web_sm")
    else:
        print("🚀 [blue]Downloading spaCy model...[/blue]")
        spacy.cli.download("en_core_web_sm")
        return spacy.load("en_core_web_sm")


def parse_git_diff(diff_file):
    """Parses a Git diff and categorizes added, deleted, and modified objects/attributes."""

    with open(diff_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    nlp = load_or_train_spacy_model()

    added_objects = set()
    deleted_objects = set()
    modified_objects = {}

    current_object = None
    changes = {}

    for i, line in enumerate(lines):
        line = line.strip()

        # Detect object changes
        if line.startswith("diff --git"):
            if current_object and changes:
                modified_objects[current_object] = changes
            current_object = None
            changes = {}

        elif line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            if ":" in content:
                key, value = map(str.strip, content.split(":", 1))
                if key in changes and changes[key]["old"] is not None:
                    changes[key]["new"] = value
                else:
                    changes[key] = {"old": None, "new": value}  # New attribute
            else:
                added_objects.add(content)

        elif line.startswith("-") and not line.startswith("---"):
            content = line[1:].strip()
            if ":" in content:
                key, value = map(str.strip, content.split(":", 1))
                if key in changes and changes[key]["new"] is not None:
                    changes[key]["old"] = value
                else:
                    changes[key] = {"old": value, "new": None}  # Deleted attribute
            else:
                deleted_objects.add(content)

        elif ":" in line:
            key, value = map(str.strip, line.split(":", 1))
            if key in changes and changes[key]["old"] is not None:
                changes[key]["new"] = value
            else:
                changes[key] = {"old": value, "new": None}  # Potentially changed later

    # Finalize modified objects
    if current_object and changes:
        modified_objects[current_object] = changes

    return sorted(list(added_objects)), sorted(list(deleted_objects)), modified_objects


def format_output(added, deleted, modified):
    """Formats the structured Git diff output in a readable manner."""

    print("\n🚀 [bold yellow]Git Diff Summary:[/bold yellow]\n")

    if added:
        print("[green]✅ Added Objects:[/green]")
        for obj in added:
            print(f"  - {obj}")

    if deleted:
        print("\n[red]❌ Deleted Objects:[/red]")
        for obj in deleted:
            print(f"  - {obj}")

    if modified:
        print("\n[blue]🔄 Modified Objects:[/blue]")
        for obj, changes in modified.items():
            print(f"  - {obj}")
            for field, change in changes.items():
                if change["old"] is None:
                    print(f"    • {field}: ADDED {change['new']}")
                elif change["new"] is None:
                    print(f"    • {field}: REMOVED {change['old']}")
                else:
                    print(f"    • {field}: {change['old']} → {change['new']}")


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with your actual Git diff file
    added, deleted, modified = parse_git_diff(diff_file)
    format_output(added, deleted, modified)
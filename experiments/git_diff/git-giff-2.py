import re
from rich import print


def parse_git_diff(diff_file):
    """Parses a Git diff and categorizes added, deleted, and modified objects/attributes."""

    with open(diff_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    added_objects = set()
    deleted_objects = set()
    modified_objects = {}

    object_changes = {}  # Tracks changes within an object

    current_object = None

    for i, line in enumerate(lines):
        line = line.strip()

        # Detect new file change
        if line.startswith("diff --git"):
            if current_object and object_changes:
                modified_objects[current_object] = object_changes
            current_object = None
            object_changes = {}

        elif line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            if ":" in content:
                key, value = map(str.strip, content.split(":", 1))
                if current_object:
                    if key in object_changes and "old" in object_changes[key]:
                        object_changes[key]["new"] = value
                    else:
                        object_changes[key] = {"old": None, "new": value}  # New attribute added
            else:
                added_objects.add(content)

        elif line.startswith("-") and not line.startswith("---"):
            content = line[1:].strip()
            if ":" in content:
                key, value = map(str.strip, content.split(":", 1))
                if current_object:
                    if key in object_changes and "new" in object_changes[key]:
                        object_changes[key]["old"] = value
                    else:
                        object_changes[key] = {"old": value, "new": None}  # Attribute removed
            else:
                deleted_objects.add(content)

        elif ":" in line:
            key, value = map(str.strip, line.split(":", 1))
            if current_object:
                if key in object_changes:
                    object_changes[key]["new"] = value
                else:
                    object_changes[key] = {"old": value, "new": None}  # Track changes

    # Finalize last modified object
    if current_object and object_changes:
        modified_objects[current_object] = object_changes

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
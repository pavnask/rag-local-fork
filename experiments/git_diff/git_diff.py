import re


def parse_git_diff(diff_file):
    with open(diff_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    readable_output = []
    file_changes = []
    removed_lines = []
    added_lines = []
    old_line_num = 1  # Default to 1 to prevent NoneType issues
    new_line_num = 1  # Default to 1 to prevent NoneType issues

    for line in lines:
        if line.startswith("diff --git"):
            if file_changes:
                readable_output.append(format_columns(removed_lines, added_lines))
            file_changes = [f"\nFile: {line.split()[-1]}"]
            removed_lines = []
            added_lines = []
            old_line_num = 1
            new_line_num = 1

        elif line.startswith("---") or line.startswith("+++"):
            continue  # Ignore file index headers

        elif line.startswith("@@"):
            if file_changes:
                readable_output.append(format_columns(removed_lines, added_lines))
            file_changes.append(f"\nSection: {line.strip()}")
            match = re.search(r'-(\d+),?\d* \+(\d+),?\d*', line)
            if match:
                old_line_num = int(match.group(1))
                new_line_num = int(match.group(2))
            else:
                old_line_num = 1
                new_line_num = 1
            removed_lines = []
            added_lines = []

        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(f"{new_line_num}: {line[1:].strip()}")
            new_line_num += 1  # Ensure it's always an integer

        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(f"{old_line_num}: {line[1:].strip()}")
            old_line_num += 1  # Ensure it's always an integer

        else:
            if old_line_num is not None and new_line_num is not None:
                removed_lines.append(f"{old_line_num}: {line.strip()}")
                added_lines.append(f"{new_line_num}: {line.strip()}")
                old_line_num += 1
                new_line_num += 1

    if file_changes:
        readable_output.append(format_columns(removed_lines, added_lines))

    return "\n".join(readable_output)


def format_columns(removed, added):
    """Formats removed and added lines into two aligned columns."""
    max_width = max([len(line) for line in removed] + [len(line) for line in added] + [10])
    header = f"{'OLD (Removed)':<{max_width}} | {'NEW (Added)':<{max_width}}"
    separator = "-" * (max_width * 2 + 3)

    formatted_lines = [header, separator]
    for old, new in zip(removed + [""] * (len(added) - len(removed)), added + [""] * (len(removed) - len(added))):
        formatted_lines.append(f"{old:<{max_width}} | {new:<{max_width}}")

    return "\n".join(formatted_lines)


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with your actual diff file
    human_readable_diff = parse_git_diff(diff_file)
    print(human_readable_diff)
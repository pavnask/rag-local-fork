import fnmatch
def is_ignored(file_path, ignore_patterns):
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def load_requirements(requirements_path):
    import json
    if not os.path.exists(requirements_path):
        print(Fore.RED + f"[ERROR] Requirements file not found: {requirements_path}")
        return {}
    with open(requirements_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_standards(path):
    import json
    if not os.path.exists(path):
        print(Fore.RED + f"[ERROR] Standards file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_against_standards(parsed_yaml, standards):
    results = []

    def get_systems_block(yaml_data):
        if not isinstance(yaml_data, dict):
            print(Fore.RED + "[ERROR] Parsed YAML is not a dictionary.")
            return {}

        print(Fore.CYAN + f"[DEBUG] Top-level keys: {list(yaml_data.keys())}")

        # Explicitly access the systems block if present
        if "kadzo.v2023.systems" in yaml_data:
            block = yaml_data["kadzo.v2023.systems"]
            if isinstance(block, dict):
                return block

        # Fallback: find first dict-of-dicts block
        def find_deep_dict(d):
            if all(isinstance(v, dict) for v in d.values()):
                return d
            for v in d.values():
                if isinstance(v, dict):
                    result = find_deep_dict(v)
                    if result:
                        return result
            return None

        return find_deep_dict(yaml_data) or {}

    systems_block = parsed_yaml.get("kadzo.v2023.systems", {})

    if not isinstance(systems_block, dict):
        return results

    print(Fore.CYAN + f"[DEBUG] Evaluating {len(systems_block)} systems for standards compliance...")

    for sys_id, sys_data in systems_block.items():
        if sys_id in {"title", "description", "class", "group", "criticality"}:
            print(Fore.LIGHTBLACK_EX + f"[SKIP] {sys_id} is a metadata field, skipping.")
            continue

        if not isinstance(sys_data, dict):
            print(Fore.LIGHTBLACK_EX + f"[SKIP] {sys_id} is a {type(sys_data).__name__}, skipping.")
            continue

        if "criticality" not in sys_data or "group" not in sys_data:
            print(Fore.YELLOW + f"[DEBUG] {sys_id} missing required fields, skipping.")
            continue

        print(Fore.LIGHTBLUE_EX + f"[DEBUG] Checking {sys_id}: criticality={sys_data['criticality']}, group={sys_data['group']}")

        for item in standards:
            levels = item.get("sber", {}).get("applicability_level", [])
            required_obj = item.get("sber", {}).get("obj_und_ctrl", [])
        if (
            str(sys_data["criticality"]).strip().lower() in [lvl.strip().lower() for lvl in levels] and
            str(sys_data["group"]).strip().lower() in [grp.strip().lower() for grp in required_obj]
        ):
                results.append(f"🟢 **{sys_id}** matches standard:\n> _{item['statement']}_")
    return results

def validate_yaml_against_requirements(yaml_lines, requirements):
    import yaml
    cleaned_yaml = "\n".join(
        l.lstrip("+-").strip()
        for l in yaml_lines
        if (l.strip().startswith("+") and ":" in l) or (not l.strip().startswith("-") and not l.strip().startswith("@@") and ":" in l)
    )
    try:
        parsed = yaml.safe_load(cleaned_yaml)
    except yaml.YAMLError as e:
        return [f"❌ YAML parse error: {e}"]

    report = []
    if not parsed or not isinstance(parsed, dict):
        return ["❌ YAML content is not a valid dictionary"]

    req_fields = requirements.get("required_fields", [])
    constraints = requirements.get("field_constraints", {})

    for field in req_fields:
        if field not in str(parsed):
            report.append(f"❌ Missing required field: {field}")

    def find_field_value(yaml_obj, field):
        if isinstance(yaml_obj, dict):
            for k, v in yaml_obj.items():
                if k == field:
                    return v
                found = find_field_value(v, field)
                if found is not None:
                    return found
        elif isinstance(yaml_obj, list):
            for item in yaml_obj:
                found = find_field_value(item, field)
                if found is not None:
                    return found
        return None

    for field, rules in constraints.items():
        val = find_field_value(parsed, field)
        if val is not None:
            try:
                val = int(val)
                if "min" in rules and val < rules["min"]:
                    report.append(f"⚠️ {field} value {val} is below the minimum of {rules['min']}")
                if "max" in rules and val > rules["max"]:
                    report.append(f"⚠️ {field} value {val} exceeds the maximum of {rules['max']}")
            except Exception as e:
                report.append(f"⚠️ Could not evaluate {field}: {e}")

    return report or ["✅ YAML meets all requirements"]


from pathlib import Path

def load_local_schemas(schema_paths):
    schema_files = {}
    for schema_dir in schema_paths:
        dir_path = Path(schema_dir)
        if not dir_path.exists() or not dir_path.is_dir():
            print(Fore.YELLOW + f"[WARNING] Schema directory not found: {dir_path}")
            continue
        for yaml_file in dir_path.rglob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    schema_files[str(yaml_file)] = f.read()
                    print(Fore.MAGENTA + f"[DEBUG] Loaded schema from: {yaml_file}")
            except Exception as e:
                print(Fore.RED + f"[ERROR] Failed to read schema file {yaml_file}: {e}")
    return schema_files



import yaml

def load_config(config_path):
    if not config_path or not os.path.exists(config_path):
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}



import git
import argparse
import os
import sqlite3
import ollama
import mimetypes
import colorama
from colorama import Fore, Style
import os
from datetime import datetime
import re

colorama.init(autoreset=True)


def init_repo(repo_path):
    return git.Repo(repo_path)


def fetch_commit_history(repo, limit=10):
    commits = list(repo.iter_commits('main', max_count=limit))
    commit_data = []
    for commit in commits:
        commit_data.append({
            'hash': commit.hexsha,
            'author': commit.author.name,
            'date': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
            'message': commit.message.strip()
        })
    return commits, commit_data


def generate_commit_report(commit_data):
    print(Fore.CYAN + "\nCommit History Report:")
    print(Fore.CYAN + "=" * 50)
    for commit in commit_data:
        print(Fore.YELLOW + f"Commit: {commit['hash']}")
        print(Fore.GREEN + f"Author: {commit['author']}")
        print(Fore.MAGENTA + f"Date: {commit['date']}")
        print(Fore.WHITE + f"Message: {commit['message']}")
        print(Fore.CYAN + "-" * 50)


def is_binary_file(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type is None or mime_type.startswith("application/")


def sanitize_text(text):
    return text.encode("utf-8", "ignore").decode("utf-8")


def get_readme_content(repo_path):
    for readme in ["README.md", "README.txt", "README.rst"]:
        path = os.path.join(repo_path, readme)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return "No README file found."




def get_diff(repo, commits, index1, index2, yaml_only=False, use_schema=False, schema_paths=None, ignore_patterns=None):
    num_commits = len(commits)
    schema_files = {}  # (will be loaded from local paths later)

    if num_commits == 1:
        initial_diff = sanitize_text(repo.git.show(commits[0].hexsha))
        return {"initial_commit": {"new_files": [initial_diff]}}, schema_files

    index1 = (num_commits + index1) if index1 < 0 else index1
    index2 = (num_commits + index2) if index2 < 0 else index2

    if index1 >= num_commits or index2 >= num_commits or index1 < 0 or index2 < 0:
        return "Invalid commit index specified.", {}

    commit1 = commits[index1]
    commit2 = commits[index2]
    raw_diff = sanitize_text(repo.git.diff(commit1.hexsha, commit2.hexsha, '--patch', '--diff-filter=AM'))


    grouped_diffs = {}
    current_file = None
    file_ext = None
    lines = raw_diff.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git"):
            match = re.search(r'diff --git a/(.*?) b/(.*?)$', line)
            if not match:
                i += 1
                continue
            file_path = os.path.normpath(match.group(2))
            print(Fore.BLUE + f"[DEBUG] Considering: {file_path}")

            if not file_path.endswith(('.yaml', '.yml')):
                print(Fore.YELLOW + f"[SKIP] Not a YAML file: {file_path}")
                current_file = None
                i += 1
                continue

            if lines[i+1].startswith("new file mode") and lines[i+3].startswith("+++ b/"):
                # New file, fetch from disk
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        contents = f.readlines()
                    print(Fore.GREEN + f"[ADD] New file detected, loaded from disk: {file_path}")
                    file_ext = os.path.splitext(file_path)[-1].lower() or "no_extension"
                    if file_ext not in grouped_diffs:
                        grouped_diffs[file_ext] = {}
                    grouped_diffs[file_ext][file_path] = contents
                except Exception as e:
                    print(Fore.RED + f"[ERROR] Failed to load new file {file_path}: {e}")
                current_file = None
                i += 5
                continue

            # Otherwise, begin collecting diff lines for this file
            current_file = file_path
            file_ext = os.path.splitext(file_path)[-1].lower() or "no_extension"
            if file_ext not in grouped_diffs:
                grouped_diffs[file_ext] = {}
            grouped_diffs[file_ext][current_file] = []
            print(Fore.GREEN + f"[ADD] Tracking changes for: {file_path}")
        elif current_file and line.strip():
            grouped_diffs[file_ext][current_file].append(sanitize_text(line))
        i += 1


    if not grouped_diffs:
        print(Fore.RED + "[DEBUG] No diffs were captured. Raw diff below:")
        print(raw_diff)
    return grouped_diffs, schema_files


def summarize_diff_ollama(diff_groups, readme_content, language, model="mistral", schema_files=None):
    summaries = {}
    for file_type, files in diff_groups.items():
        file_summaries = {}
        for file_path, changes in files.items():
            diff_text = sanitize_text("\n".join(changes[:1000]))
            schema_context = "\n\nSchema Context:\n" + "\n\n".join(schema_files.values()) if schema_files else ""
            prompt = f"""
Repository README:
{readme_content}

This is a YAML configuration file: {file_path}

Below is the git diff of recent changes:

{diff_text}

Please summarize the YAML changes in {language}. Explain what keys, sections, or values were added, removed, or modified. If possible, highlight any impact these changes may have on behavior or configurations. Please provide the output in Russian.
"""
            response = ollama.chat(model=model, messages=[
                {"role": "system", "content": "You are a precise assistant that summarizes YAML configuration changes."},
                {"role": "user", "content": prompt}
            ])
            file_summaries[file_path] = sanitize_text(response["message"]["content"].strip())
        summaries[file_type] = file_summaries
    return summaries


def main():


    parser = argparse.ArgumentParser(description="Git Commit Analyzer CLI")
    parser.add_argument('--repo', type=str, help='Path to the Git repository')
    parser.add_argument('--limit', type=int, default=10, help='Number of commits to fetch')
    parser.add_argument('--compare', type=int, nargs=2, metavar=('INDEX1', 'INDEX2'),
                        help='Compare two commits by index (e.g., 0 -1 for latest vs previous)')
    parser.add_argument('--ai-summary', action='store_true', help='Use Ollama AI to summarize the diff')
    parser.add_argument('--language', type=str, default='English',
                        help='Language for AI-generated summary (default: English)')
    parser.add_argument('--yaml', action='store_true', help='Only include YAML files in the summary')
    parser.add_argument('--markdown', type=str, help='Path to save AI summary as Markdown')
    parser.add_argument('--use-schema', action='store_true', help='Use schema files to improve summaries')
    parser.add_argument('--schema-paths', type=str, default='schema', help='Comma-separated list of schema paths')
    parser.add_argument('--config', type=str, help='Path to config YAML file')
    parser.add_argument('--output', type=str, help='Path to save full CLI output')
    parser.add_argument('--mode', type=str, help='Mode of operation')
    parser.add_argument('--requirements-file', type=str, help='Path to requirements JSON file')
    args = parser.parse_args()

    config = load_config(args.config)
    args_dict = vars(args)
    for k, v in config.items():
        if v is not None:
            args_dict[k] = v
    schema_paths = [os.path.normpath(p.strip()) for p in args_dict.get("schema_paths", "schema").split(",")]

    ignore_patterns = args_dict.get("git_ignore", [])

    requirements = {}
    standards = []
    if args_dict.get("standards_file"):
        standards = load_standards(args_dict["standards_file"])
    if args_dict.get("mode") == "requirements":
        requirements_file = args_dict.get("requirements_file")
        if requirements_file:
            requirements = load_requirements(requirements_file)

    if not args_dict.get("repo"):
        parser.error("Missing required argument: --repo (or provide it in the config file)")



    if args_dict.get("output"):
        import sys
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    f.write(obj)
            def flush(self):
                for f in self.files:
                    f.flush()
        sys.stdout = Tee(sys.stdout, open(args_dict["output"], "w", encoding="utf-8"))

    repo = init_repo(args.repo)
    commits, commit_data = fetch_commit_history(repo, args.limit)
    generate_commit_report(commit_data)

    if args.compare:
        print(Fore.CYAN + f"\nDiff between commit {args.compare[0]} and {args.compare[1]}:")
        print(Fore.CYAN + "=" * 50)
        diff_groups, _ = get_diff(repo, commits, args.compare[0], args.compare[1], yaml_only=args.yaml, use_schema=False, schema_paths=schema_paths, ignore_patterns=ignore_patterns)
        schema_files = load_local_schemas(schema_paths) if args.use_schema else {}
        print(Fore.YELLOW + "\n[DEBUG] Diff Groups:")
        print(diff_groups)
        readme_content = get_readme_content(args.repo)

        if args.ai_summary:
            print(Fore.CYAN + "\nAI Summary of Changes:")
            print(Fore.CYAN + "=" * 50)
            summaries = summarize_diff_ollama(diff_groups, readme_content, args.language, schema_files=schema_files if args.use_schema else None)
            if standards:
                print(Fore.CYAN + "\nStandards Evaluation:")
                for file_type, file_entries in diff_groups.items():
                    for file_path, content_lines in file_entries.items():
                        yaml_lines = content_lines
                        if all(not line.strip().startswith(("+", "-", "@@")) for line in yaml_lines):
                            cleaned_yaml = "\n".join(l.strip() for l in yaml_lines)
                        else:
                            cleaned_yaml = "\n".join(
                                l.lstrip("+-").strip()
                                for l in yaml_lines
                                if (l.strip().startswith("+") and ":" in l) or (not l.strip().startswith("-") and not l.strip().startswith("@@") and ":" in l)
                            )
                        try:
                            parsed_yaml = yaml.safe_load(cleaned_yaml)
                            if not isinstance(parsed_yaml, dict):
                                print(Fore.RED + f"[ERROR] Parsed YAML is not a dict for {file_path}. Skipping standards check.")
                                continue
                            hits = check_against_standards(parsed_yaml, standards)
                            print(Fore.WHITE + f"File: {file_path}")
                            if hits:
                                for h in hits:
                                    print(Fore.YELLOW + f"  - {h}")
                            else:
                                print(Fore.LIGHTBLACK_EX + "  No standards matched.")
                        except Exception as e:
                            print(Fore.RED + f"[ERROR] Standards check failed for {file_path}: {e}")

        if args_dict.get("markdown"):
            md_lines = ["# AI Summary of Changes\\n"]
            total = 0
            for file_type, file_summaries in summaries.items():
                md_lines.append(f"## {file_type.upper()} Files\\n")
                for file_path, summary in file_summaries.items():
                    total += 1
                    md_lines.append(f"### {file_path}\\n")

                    if any(kw in summary.lower() for kw in ['removed', 'deleted', 'required', 'breaking']):
                        md_lines.append("**🚨 Potential Breaking Change Detected**\\n")

                    if not summary:
                        summary = "*No summary generated.*"
                    md_lines.append(summary)

                    if requirements:
                        validation = validate_yaml_against_requirements(diff_groups[file_type][file_path], requirements)
                        print(Fore.CYAN + f"[DEBUG] Requirements validation for {file_path}:")
                        for v in validation:
                            print(Fore.YELLOW + f"  - {v}")
                        md_lines.append("#### Requirements Check\\n")
                        for v in validation:
                            md_lines.append(f"- {v}")
                        md_lines.append("\\n")

                if total > 0:
                    md_path = os.path.abspath(args_dict["markdown"])
                    print(Fore.CYAN + f"[DEBUG] Saving markdown to: {md_path}")
                    with open(md_path, "w", encoding="utf-8") as md_file:
                        md_file.write("\\n".join(md_lines))
                else:
                    print(Fore.YELLOW + "[WARNING] No summaries found. Markdown not saved.")

                for file_type, file_summaries in summaries.items():
                    print(Fore.GREEN + f"\nSummary for {file_type} files:")
                    for file_path, summary in file_summaries.items():
                        print(Fore.WHITE + f"{file_path}:\n{summary}\n")


if __name__ == "__main__":
    main()

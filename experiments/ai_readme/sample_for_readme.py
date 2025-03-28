import git
import argparse
import os
import sqlite3
import ollama
import mimetypes
import colorama
from colorama import Fore, Style
from datetime import datetime
import re

colorama.init(autoreset=True)


def init_repo(repo_path):
    """Initialize Git repository object."""
    return git.Repo(repo_path)


def fetch_commit_history(repo, limit=10):
    """Fetch only the last `limit` commits and return their metadata."""
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
    """Generate and print a report of commit history with colors."""
    print(Fore.CYAN + "\nCommit History Report:")
    print(Fore.CYAN + "=" * 50)
    for commit in commit_data:
        print(Fore.YELLOW + f"Commit: {commit['hash']}")
        print(Fore.GREEN + f"Author: {commit['author']}")
        print(Fore.MAGENTA + f"Date: {commit['date']}")
        print(Fore.WHITE + f"Message: {commit['message']}")
        print(Fore.CYAN + "-" * 50)


def is_binary_file(filename):
    """Determine if a file is binary based on its MIME type."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type is None or mime_type.startswith("application/")


def sanitize_text(text):
    """Ensure text is UTF-8 encoded and remove problematic characters."""
    return text.encode("utf-8", "ignore").decode("utf-8")


def get_readme_content(repo_path):
    """Retrieve README file content if available."""
    readme_files = ["README.md", "README.txt", "README.rst"]
    for readme in readme_files:
        readme_path = os.path.join(repo_path, readme)
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                return f.read()
    return "No README file found."


def get_diff(repo, commits, index1, index2):
    """Get the diff between two commits, handling initial commit correctly."""
    num_commits = len(commits)

    # Handle single commit case (first commit has no parent to compare)
    if num_commits == 1:
        initial_diff = sanitize_text(repo.git.show(commits[0].hexsha))
        return {"initial_commit": {"new_files": [initial_diff]}}

    # Convert negative indices to positive indices relative to the fetched commits
    index1 = (num_commits + index1) if index1 < 0 else index1
    index2 = (num_commits + index2) if index2 < 0 else index2

    if index1 >= num_commits or index2 >= num_commits or index1 < 0 or index2 < 0:
        return "Invalid commit index specified."

    commit1 = commits[index1]
    commit2 = commits[index2]
    raw_diff = sanitize_text(repo.git.diff(commit2.hexsha, commit1.hexsha))

    if not raw_diff.strip():
        return "No changes detected between these commits."

    grouped_diffs = {}
    current_file = None

    for line in raw_diff.split('\n'):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) > 2:
                file_path = parts[-1][2:]
                if not is_binary_file(file_path) or file_path.endswith(
                        ('.txt', '.md', '.yaml', '.json', '.py', '.js', '.html', '.css')):
                    current_file = file_path
                    file_ext = os.path.splitext(file_path)[-1].lower() or "no_extension"
                    if file_ext not in grouped_diffs:
                        grouped_diffs[file_ext] = {}
                    grouped_diffs[file_ext][current_file] = []
        elif current_file and line.strip():
            grouped_diffs[file_ext][current_file].append(sanitize_text(line))

    return grouped_diffs


def summarize_diff_ollama(diff_groups, readme_content, language, model="mistral"):
    """Use Ollama to generate a summary of code changes with README context and selected language."""
    summaries = {}
    for file_type, files in diff_groups.items():
        file_summaries = {}
        for file_path, changes in files.items():
            diff_text = sanitize_text("\n".join(changes[:1000]))  # Limit input to avoid overloading model
            prompt = f"""
            Repository README:
            {readme_content}

            Here is a git diff for the file: {file_path}

            {diff_text}

            Summarize these changes in {language}, specifying what functions, variables, or logic were modified.
            Focus on what changed rather than listing filenames.
            """
            response = ollama.chat(model=model, messages=[
                {"role": "system", "content": "You are a precise assistant that summarizes specific code changes."},
                {"role": "user", "content": prompt}
            ])
            file_summaries[file_path] = sanitize_text(response["message"]["content"].strip())
        summaries[file_type] = file_summaries
    return summaries


def main():
    parser = argparse.ArgumentParser(description="Git Commit Analyzer CLI")
    parser.add_argument('--repo', type=str, required=True, help='Path to the Git repository')
    parser.add_argument('--limit', type=int, default=10, help='Number of commits to fetch')
    parser.add_argument('--compare', type=int, nargs=2, metavar=('INDEX1', 'INDEX2'),
                        help='Compare two commits by index (e.g., 0 -1 for latest vs previous)')
    parser.add_argument('--ai-summary', action='store_true', help='Use Ollama AI to summarize the diff')
    parser.add_argument('--language', type=str, default='English',
                        help='Language for AI-generated summary (default: English)')
    args = parser.parse_args()

    repo = init_repo(args.repo)
    commits, commit_data = fetch_commit_history(repo, args.limit)
    generate_commit_report(commit_data)

    if args.compare:
        print(Fore.CYAN + f"\nDiff between commit {args.compare[0]} and {args.compare[1]}:")
        print(Fore.CYAN + "=" * 50)
        diff_groups = get_diff(repo, commits, args.compare[0], args.compare[1])
        readme_content = get_readme_content(args.repo)

        if args.ai_summary:
            print(Fore.CYAN + "\nAI Summary of Changes:")
            print(Fore.CYAN + "=" * 50)
            summaries = summarize_diff_ollama(diff_groups, readme_content, args.language)
            for file_type, file_summaries in summaries.items():
                print(Fore.GREEN + f"\nSummary for {file_type} files:")
                for file_path, summary in file_summaries.items():
                    print(Fore.WHITE + f"{file_path}:\n{summary}\n")


if __name__ == "__main__":
    main()

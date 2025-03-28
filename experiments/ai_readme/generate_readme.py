import os
import sys
import ast
import subprocess
import argparse
from pathlib import Path

README_TEMPLATE = """# 📘 Project: {title}

{description}

## 🚀 What It Does
{summary_section}

## ✅ Features
{features_section}

{requirements_section}

## 🧰 CLI Usage
{cli_usage_section}

## 📘 API Reference
{api_reference}

## 🤝 Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

{license_section}
"""

def extract_requirements(py_files):
    stdlib_modules = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
    imports = set()
    for file_path in py_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split('.')[0])
    return sorted({imp for imp in imports if imp not in stdlib_modules})

def ollama_summarize(prompt, model="mistral", language="English"):
    prompt = f"Respond in {language}.\n\n{prompt}"
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except Exception as e:
        return f"AI Summary failed: {e}"

def translate_section(label, content, language):
    print(f"🧠 [AI] Translating {label} to {language}")
    return ollama_summarize(f"Translate the following section to {language}. Do not alter any code or parameter names:\n\n{content}", language=language)

def extract_docstring(file_path, ai_fallback=False, language="English"):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            code = f.read()
            module = ast.parse(code)
            doc = ast.get_docstring(module)
            if ai_fallback:
                if not doc or len(doc.strip()) < 10:
                    print(f"🧠 [AI] Enhancing top-level description via Ollama for: {file_path}")
                    return ollama_summarize("Summarize the purpose of this Python file:\n\n" + code, language=language)
            return doc
        except Exception:
            return None

def extract_api_reference(file_path, ai_fallback=False, language="English"):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
        tree = ast.parse(code)
    api_lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if ai_fallback and (not doc or len(doc.strip()) < 10):
                source = ast.get_source_segment(code, node)
                print(f"🧠 [AI] Summarizing function `{node.name}`")
                doc = ollama_summarize("Explain clearly what this Python function does:\n\n" + source, language=language)
            doc = doc or "No description"
            args = [arg.arg for arg in node.args.args]
            api_lines.append(f"### `{node.name}({', '.join(args)})`\n{doc}\n")
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if ai_fallback and (not doc or len(doc.strip()) < 10):
                print(f"🧠 [AI] Summarizing class `{node.name}`")
                source = ast.get_source_segment(code, node)
                doc = ollama_summarize("Explain the purpose of this class in simple terms:\n\n" + source, language=language)
            doc = doc or "No description"
            api_lines.append(f"## Class `{node.name}`\n{doc}\n")
    return "\n".join(api_lines)

def detect_usage_example(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    inside_main = False
    example = []
    for line in lines:
        if '__name__' in line and '__main__' in line:
            inside_main = True
            continue
        if inside_main:
            if line.strip().startswith("def ") or line.strip().startswith("class "):
                break  # Stop at the next function/class definition
            if line.strip():
                example.append(line)

    code = ''.join(example).strip()
    return code if code else "# Add usage example here"

def extract_cli_args(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    cli_lines = []
    if "argparse.ArgumentParser" in code:
        cli_lines.append("This script accepts the following command-line arguments:")
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr == 'add_argument':
                    args = []
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            args.append(arg.value)
                    for kw in node.keywords:
                        if kw.arg == 'help' and isinstance(kw.value, ast.Constant):
                            help_text = kw.value.value
                            if args:
                                cli_lines.append(f"- `{args[0]}`: {help_text}")
        except Exception as e:
            cli_lines.append(f"⚠️ Failed to parse CLI arguments: {e}")
    return "\n".join(cli_lines) if cli_lines else ""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate README.md for a Python project.")
    parser.add_argument("project_path", help="Path to the project folder")
    parser.add_argument("--ai", action="store_true", help="Use Ollama AI to enrich descriptions")
    parser.add_argument("--language", type=str, default="English", help="Language for README content generation")

    args = parser.parse_args()
    def generate_readme_with_ai(path, use_ai=False, language="English"):
        path = Path(path)
        py_files = [path] if path.is_file() and path.suffix == ".py" else list(path.rglob("*.py"))
        if not py_files:
            print("❌ No Python files found at the specified path.")
            return

        title = path.name.replace('_', ' ').title()
        script_name = py_files[0].name
        description = extract_docstring(py_files[0], ai_fallback=use_ai, language=language) or f"{title} is a Python project."

        summary_section = description if description else "This script performs core logic as described above."

        req_file = path / 'requirements.txt'
        install_instructions = f"pip install -r requirements.txt" if req_file.exists() else "pip install <package-name>"

        usage_example = f"python {py_files[0].name}"

        imports = extract_requirements(py_files)
        features = [
            "- Written in Python",
        ]
        if "os" in imports or "dotenv" in imports:
            features.append("- Uses environment variables for secrets or configs")
        if any("try" in line and "except" in line for f in py_files for line in open(f, encoding="utf-8")):
            features.append("- Handles exceptions and prints errors clearly")
        if "requests" in imports or "openai" in imports:
            features.append("- Connects to an API or external service")
        features_section = "\n".join(features)

        requirements_section = (
            "## 📦 Requirements\n"
            "Install the following with pip:\n"
            "```bash\n" + "\n".join(imports) + "\n```"
        ) if imports else ""

        api_parts = [extract_api_reference(f, ai_fallback=use_ai, language=language) for f in py_files]
        api_reference = "\n".join(api_parts) if api_parts else "# API docs not available"

        license_path = path / 'LICENSE'
        license_section = f"## 📄 License\nThis project is licensed under the terms of the license found in the [LICENSE](LICENSE) file." if license_path.exists() else ""

        cli_usage_section = extract_cli_args(py_files[0])

        translated_description = translate_section("description", description, language) if use_ai else description
        translated_summary = translate_section("summary", summary_section, language) if use_ai else summary_section
        translated_cli = translate_section("CLI usage", cli_usage_section, language) if use_ai else cli_usage_section

        readme_content = README_TEMPLATE.format(
            title=title,
            description=translated_description,
            summary_section=translated_summary,
            install_instructions=install_instructions,
            usage_example=usage_example,
            script_name=script_name,
            api_reference=api_reference,
            license_section=license_section,
            requirements_section=requirements_section,
            features_section=features_section,
            cli_usage_section=translated_cli,
        )

        output_dir = path.parent if path.is_file() else path
        with open(output_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ README.md generated at {output_dir / 'README.md'}")

    generate_readme_with_ai(args.project_path, use_ai=args.ai, language=args.language)
import os
import re
import json
import ollama
from rich import print


def analyze_git_diff_with_ai(diff_text):
    """Uses AI to extract structured changes (Added, Deleted, Modified) from a Git diff."""

    prompt = f"""
    You are an AI that analyzes Git diffs and extracts structured changes.

    **Rules:**
    - Only return valid JSON. Do NOT include any extra text, explanations, or formatting.
    - If no changes are found, return:
      {{"added_objects": [], "deleted_objects": [], "modified_objects": []}}
    - Ensure JSON formatting is valid.

    **JSON format:**
    {{
      "added_objects": ["List of added objects"],
      "deleted_objects": ["List of deleted objects"],
      "modified_objects": [
        {{
          "object": "Modified Object Name",
          "changes": {{
            "attribute": "Old Value → New Value"
          }}
        }}
      ]
    }}

    **Example Output:**
    {{
      "added_objects": ["dvportgroup-3456", "dvswitch-24"],
      "deleted_objects": ["dvportgroup-1019", "vdc_title: Old_Datacenter"],
      "modified_objects": [
        {{
          "object": "dvportgroup-42577",
          "changes": {{
            "Title": "Legacy_Group → New_Group"
          }}
        }},
        {{
          "object": "vlan-504",
          "changes": {{
            "VLAN ID": "10 → 20"
          }}
        }}
      ]
    }}

    **Git Diff to Analyze:**
    {diff_text}
    """

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])

    raw_output = response.get("message", {}).get("content", "").strip()

    # Ensure AI returned something
    if not raw_output:
        print("⚠️ AI returned an empty response. Falling back to raw diff output.")
        return {"error": "AI response was empty."}

    # Attempt to parse AI's response as JSON
    try:
        structured_response = json.loads(raw_output)  # Parse JSON
        return structured_response
    except json.JSONDecodeError:
        print("⚠️ AI returned invalid JSON. Attempting manual extraction.")
        return extract_changes_manually(raw_output)


def extract_changes_manually(ai_output):
    """Fallback: Extracts structured changes from AI's unstructured response."""
    added = re.findall(r"Added:\s*(.+)", ai_output, re.IGNORECASE)
    deleted = re.findall(r"Deleted:\s*(.+)", ai_output, re.IGNORECASE)
    modified_matches = re.findall(r"Modified:\s*(.+)", ai_output, re.IGNORECASE)

    modified_objects = []
    for mod in modified_matches:
        parts = mod.split("→")
        if len(parts) == 2:
            modified_objects.append({
                "object": parts[0].strip(),
                "changes": {"Attribute": f"{parts[0].strip()} → {parts[1].strip()}"}
            })

    return {
        "added_objects": added,
        "deleted_objects": deleted,
        "modified_objects": modified_objects
    }


def format_ai_output(ai_output):
    """Formats AI-generated structured output into a human-readable report."""

    print("\n🚀 [bold yellow]AI-Powered Git Diff Analysis:[/bold yellow]\n")

    if "error" in ai_output:
        print(f"[red]❌ Error:[/red] {ai_output['error']}")
        return

    if ai_output.get("added_objects"):
        print("[green]✅ Added Objects:[/green]")
        for obj in ai_output["added_objects"]:
            print(f"  - {obj}")

    if ai_output.get("deleted_objects"):
        print("\n[red]❌ Deleted Objects:[/red]")
        for obj in ai_output["deleted_objects"]:
            print(f"  - {obj}")

    if ai_output.get("modified_objects"):
        print("\n[blue]🔄 Modified Objects:[/blue]")
        for obj in ai_output["modified_objects"]:
            print(f"  - {obj['object']}")
            for attr, change in obj["changes"].items():
                print(f"    • {attr}: {change}")


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with your actual Git diff file

    with open(diff_file, "r", encoding="utf-8") as file:
        diff_text = file.read()

    ai_generated_changes = analyze_git_diff_with_ai(diff_text)
    format_ai_output(ai_generated_changes)
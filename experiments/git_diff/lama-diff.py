import re
import ollama  # Ensure Ollama is installed


def call_llama_to_format(diff_text):
    """
    Sends the Git diff text to Ollama's Llama model and ensures a clear format.
    """
    prompt = f"""
    You are a Git diff expert. Convert the following Git diff into a **human-readable format**.

    **Format Rules:**
    - Label added lines as: **[ADDED]**
    - Label removed lines as: **[REMOVED]**
    - Label changed lines as: **[CHANGED]**
    - Show **line numbers**.
    - **DO NOT use tables, YAML, JSON, or Markdown**.
    - **Output must be raw text only**.

    **Example Output:**
    ```
    [REMOVED] 12: print("Hello World")
    [ADDED]   12: print("Hi World")
    [CHANGED] 14: old_function() → new_function()
    ```

    **Git Diff to Process:**
    {diff_text}

    Please return only the formatted text.
    """

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()


def parse_git_diff_with_llama(diff_file):
    """Reads a Git diff file and processes it using Ollama's Llama AI."""
    with open(diff_file, 'r', encoding='utf-8') as file:
        diff_text = file.read()

    raw_ai_output = call_llama_to_format(diff_text)

    # If AI fails, return raw output
    if not raw_ai_output or "[ADDED]" not in raw_ai_output and "[REMOVED]" not in raw_ai_output and "[CHANGED]" not in raw_ai_output:
        print("⚠️ AI response did not contain expected formatting. Using raw output.")
        return raw_ai_output

    return raw_ai_output  # AI response should now be correctly formatted


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with your actual Git diff file
    human_readable_diff = parse_git_diff_with_llama(diff_file)
    print(human_readable_diff)
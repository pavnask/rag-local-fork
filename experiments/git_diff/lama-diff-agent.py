import os
import re
import spacy
import ollama
from rich import print
from langchain.llms import Ollama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory

# Load or train spaCy model
MODEL_DIR = "spacy_model"


def load_or_train_spacy_model():
    if os.path.exists(MODEL_DIR):
        print("✅ [green]Loading existing spaCy model...[/green]")
        return spacy.load(MODEL_DIR)
    else:
        print("🚀 [blue]Training and saving new spaCy model...[/blue]")
        nlp = spacy.blank("en")
        nlp.to_disk(MODEL_DIR)
        return nlp


# Load Local Llama 3.2 Model
llm = Ollama(model="llama3.2")


@tool
def analyze_git_diff(diff_text: str):
    """Extracts a structured report of Added, Deleted, and Modified objects from a Git diff."""
    prompt = f"""
    You are analyzing a Git diff for vCenter objects (dvportgroup, dvswitch, etc.).
    Generate a structured report that only states what has changed.

    **Report Format (DO NOT DEVIATE)**:

    **Added Objects:**
    - List all newly added objects.

    **Deleted Objects:**
    - List all removed objects.

    **Modified Objects:**
    - List modified objects and specify **only the attributes that changed**.

    **RULES:**
    - Do NOT reformat or rewrite data.
    - Do NOT explain or analyze the objects.
    - Do NOT suggest improvements.
    - Only state **WHAT CHANGED** and **HOW IT CHANGED**.
    - Do NOT output Markdown, JSON, or tables—just plain text.

    **Git Diff to Analyze:**
    {diff_text}

    **STRICT FORMAT ENFORCEMENT:**  
    Only return the structured report. Do NOT include any extra explanations, assumptions, or formatting suggestions.
    """

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])

    return response["message"]["content"].strip()


# Initialize LangChain Agent
tools = [analyze_git_diff]
memory = ConversationBufferMemory(memory_key="history")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True  # Enables auto-retry if output parsing fails
)


def parse_git_diff(diff_file):
    """Reads and processes the Git diff file using the local AI model."""
    with open(diff_file, "r", encoding="utf-8") as file:
        diff_text = file.read()

    try:
        result = agent.run(diff_text)
        return result
    except Exception as e:
        print(f"⚠️ Agent Error: {e}")
        return "Error analyzing Git diff."


if __name__ == "__main__":
    diff_file = "example.diff"  # Replace with your actual Git diff file
    insights = parse_git_diff(diff_file)

    print("\n🚀 [bold yellow]AI-Powered Git Diff Analysis:[/bold yellow]\n")
    print(insights)
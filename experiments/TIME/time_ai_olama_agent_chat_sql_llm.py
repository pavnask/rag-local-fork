import pandas as pd
import sqlite3
import ollama
import json
from rich.console import Console
from rich.table import Table

# Load TIME framework rules
rules_file = "rules_multi_factor_TIME.xlsx"
observations_free_text_file = "observations_free_text_TIME.xlsx"
observations_with_entities_file = "observations_with_entities_TIME.xlsx"
db_file = "chat_memory.db"

# Read Excel files
df_rules = pd.read_excel(rules_file)
df_observations_free_text = pd.read_excel(observations_free_text_file)
df_observations_with_entities = pd.read_excel(observations_with_entities_file)

# Ensure "OLLAMA_Suggestion" column exists
if "OLLAMA_Suggestion" not in df_observations_free_text.columns:
    df_observations_free_text["OLLAMA_Suggestion"] = df_observations_free_text["Observation_Text"].apply(
        lambda text: ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": "You are an IT analyst specializing in system evaluations."},
                {"role": "user", "content": f"Classify and provide a recommendation for this observation: {text}"}
            ]
        )["message"]["content"] if text else "No AI response"
    )

# SQLite Database Setup
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT,
    ai_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


def save_memory(user_query, ai_response):
    cursor.execute("INSERT INTO chat_memory (user_query, ai_response) VALUES (?, ?)", (user_query, ai_response))
    conn.commit()


def retrieve_memory(limit=5):
    cursor.execute("SELECT user_query, ai_response FROM chat_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
    return cursor.fetchall()


def clear_memory():
    cursor.execute("DELETE FROM chat_memory")
    conn.commit()


def get_relevant_observations(query):
    """Filter observations relevant to the user query and ensure columns exist."""
    if "Observation_Text" not in df_observations_free_text.columns or "OLLAMA_Suggestion" not in df_observations_free_text.columns:
        return "No relevant observations found."

    filtered_df = df_observations_free_text[
        df_observations_free_text["Observation_Text"].str.contains(query, case=False, na=False)]
    return filtered_df[['Observation_Text', 'OLLAMA_Suggestion']].to_string(
        index=False) if not filtered_df.empty else "No relevant observations found."


def ollama_classify(query):
    """Use OLLAMA to analyze and classify user queries with local IT context and relevant observations first."""
    relevant_observations = get_relevant_observations(query)

    prompt = f"""
    You are an AI IT analyst. The user has asked the following question:
    "{query}"

    Consider the following local IT policies first:
    - Security is the top priority. Any vulnerabilities must be flagged immediately.
    - Legacy systems should be evaluated for migration every 6 months.
    - Cloud-based solutions are preferred over on-premise infrastructure.
    - Performance degradation beyond 10% over 3 months is considered critical.
    - Compliance with ISO 27001 is mandatory for all systems.

    Based on these policies and the most relevant IT system observations, find the best classification and recommendation.

    Relevant Observations:
    {relevant_observations}
    """
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "system", "content": "You are an IT analyst specializing in system evaluations."},
                  {"role": "user", "content": prompt}]
    )

    return response["message"]["content"] if "message" in response and "content" in response[
        "message"] else "No AI response"


# AI Chatbot with LLM-Based Query Handling & Error Handling
def chatbot():
    console = Console()
    console.print("\n🤖 [bold cyan]IT Systems Chatbot Ready![/bold cyan] Type your question or 'exit' to quit.\n",
                  style="bold green")
    exit_commands = ["exit", "quit", "stop", "bye", "goodbye", "see you", "later"]

    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in exit_commands:
            console.print("[bold red]Goodbye! Have a great day! 👋[/bold red]")
            break

        # Retrieve past session
        if "retrieve past session" in user_input.lower():
            past_conversations = retrieve_memory()
            if past_conversations:
                console.print("\n🤖 [bold cyan]Past Conversations:[/bold cyan]", style="bold green")
                for i, (q, a) in enumerate(past_conversations, 1):
                    console.print(f"{i}. 👤 You: {q}\n   🤖 AI Agent: {a}\n", style="bold yellow")
            else:
                console.print("🤖 [bold cyan]AI Agent:[/bold cyan] No past session found.", style="bold yellow")
            continue

        # Clear memory
        if "clear memory" in user_input.lower():
            clear_memory()
            console.print("🤖 [bold cyan]AI Agent:[/bold cyan] Memory cleared!", style="bold yellow")
            continue

        # Process query using OLLAMA with relevant observations first
        response_text = ollama_classify(user_input)
        save_memory(user_input, response_text)
        console.print(f"🤖 [bold cyan]AI Agent:[/bold cyan] {response_text}\n", style="bold yellow")


# Start chatbot interaction
if __name__ == "__main__":
    chatbot()
    conn.close()

import pandas as pd
import sqlite3
import ollama
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
from rich.console import Console
from rich.table import Table

# Load NLP Model for Embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load TIME framework rules
rules_file = "rules_multi_factor_TIME.xlsx"
observations_free_text_file = "observations_free_text_TIME.xlsx"
observations_with_entities_file = "observations_with_entities_TIME.xlsx"
db_file = "chat_memory.db"

# Read Excel files
df_rules = pd.read_excel(rules_file)
df_observations_free_text = pd.read_excel(observations_free_text_file)
df_observations_with_entities = pd.read_excel(observations_with_entities_file)

# Local IT Context
local_context = """
Company XYZ IT Guidelines:
- Security is the top priority. Any vulnerabilities must be flagged immediately.
- Legacy systems should be evaluated for migration every 6 months.
- Cloud-based solutions are preferred over on-premise infrastructure.
- Performance degradation beyond 10% over 3 months is considered critical.
- Compliance with ISO 27001 is mandatory for all systems.
"""

# Define AI Expert Roles
roles = {
    "Security Analyst": "Focus on identifying security vulnerabilities, compliance risks, and mitigation strategies.",
    "Cloud Engineer": "Evaluate cloud-based solutions, performance, and scalability recommendations.",
    "IT Manager": "Balance cost, risk, and long-term IT strategy for efficient system operations.",
    "DevOps Specialist": "Optimize CI/CD pipelines, automation, and system performance.",
    "Database Administrator": "Analyze database performance, integrity, and scalability issues."
}

# SQLite Database Setup
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT,
    ai_response TEXT,
    role TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


def save_memory(user_query, ai_response, role):
    cursor.execute("INSERT INTO chat_memory (user_query, ai_response, role) VALUES (?, ?, ?)",
                   (user_query, ai_response, role))
    conn.commit()


def retrieve_memory(limit=5):
    cursor.execute("SELECT user_query, ai_response, role FROM chat_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
    return cursor.fetchall()


def clear_memory():
    cursor.execute("DELETE FROM chat_memory")
    conn.commit()


def find_most_relevant_observation(query):
    """Find the most relevant observation using embeddings and cosine similarity, ensuring dtype consistency."""
    if "Embedding" not in df_observations_free_text.columns or df_observations_free_text.empty:
        return "No relevant observations found.", "", 0

    query_embedding = embedding_model.encode(query, convert_to_tensor=False).astype(np.float32)
    similarities = []

    for _, row in df_observations_free_text.iterrows():
        if row.get("Embedding") is not None:
            stored_embedding = np.array(row["Embedding"], dtype=np.float32)
            similarity = util.cos_sim(torch.tensor(query_embedding), torch.tensor(stored_embedding)).item()
            similarities.append(
                (row.get("Observation_Text", "Unknown"), row.get("OLLAMA_Suggestion", "No suggestion"), similarity))

    similarities.sort(key=lambda x: x[2], reverse=True)  # Sort by similarity score
    return similarities[0] if similarities else ("No relevant observations found.", "", 0)


def ollama_classify(query, role):
    """Use OLLAMA to analyze and classify user queries with relevant observations from vector search, considering the AI role."""
    best_observation, best_suggestion, similarity_score = find_most_relevant_observation(query)
    role_context = roles.get(role, "General IT Analyst.")

    prompt = f"""
    You are an AI {role}. Your role is to {role_context}

    The user has asked the following question:
    "{query}"

    Consider the following local IT policies first:
    {local_context}

    Based on these policies and the most relevant IT system observation found via semantic search, provide a classification and recommendation.

    Most Relevant Observation (Similarity {similarity_score:.2f}):
    {best_observation}

    Suggested Action:
    {best_suggestion}
    """
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "system", "content": f"You are an AI {role} specialized in IT evaluations."},
                  {"role": "user", "content": prompt}]
    )

    return response["message"].get("content", "No AI response")


# AI Chatbot with Role-Based Personas
def chatbot():
    console = Console()
    console.print("\n🤖 [bold cyan]IT Systems Chatbot Ready![/bold cyan] Select your AI role:", style="bold green")
    for i, role in enumerate(roles.keys(), 1):
        console.print(f"{i}. {role}", style="bold yellow")

    role_selection = input("\n👤 Choose a role (enter number): ")
    role_keys = list(roles.keys())
    selected_role = role_keys[int(role_selection) - 1] if role_selection.isdigit() and 1 <= int(role_selection) <= len(
        roles) else "General IT Analyst"

    console.print(f"\n🤖 [bold cyan]AI Role Selected: {selected_role}[/bold cyan]", style="bold green")
    console.print("Type your question or 'exit' to quit.\n", style="bold green")
    exit_commands = ["exit", "quit", "stop", "bye", "goodbye", "see you", "later"]

    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in exit_commands:
            console.print("[bold red]Goodbye! Have a great day! 👋[/bold red]")
            break

        # Process query using OLLAMA with vector search and selected AI role
        response_text = ollama_classify(user_input, selected_role)
        save_memory(user_input, response_text, selected_role)
        console.print(f"🤖 [bold cyan]AI {selected_role}:[/bold cyan] {response_text}\n", style="bold yellow")


# Start chatbot interaction
if __name__ == "__main__":
    chatbot()
    conn.close()


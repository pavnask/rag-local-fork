import pandas as pd
import sqlite3
import ollama
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
from rich.console import Console
from rich.table import Table
import threading

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

# Response Formatting Tip
response_tip = """
[Tip for AI Response:]
1️⃣ Start with a **clear classification** of the issue (e.g., Security Risk, Performance Concern, Cost Optimization, etc.).
2️⃣ Provide **a structured response** with specific recommendations.
3️⃣ List **at least 3 actionable steps** to address the issue.
4️⃣ Ensure compliance with **Company XYZ IT Guidelines**.
5️⃣ Keep responses **concise yet informative**.
"""

# SQLite Database Setup with Adaptive Memory
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Ensure chat_memory table has required columns for adaptive memory
cursor.execute("PRAGMA table_info(chat_memory)")
columns = [col[1] for col in cursor.fetchall()]
if "role" not in columns:
    cursor.execute("ALTER TABLE chat_memory ADD COLUMN role TEXT")
if "feedback" not in columns:
    cursor.execute("ALTER TABLE chat_memory ADD COLUMN feedback INTEGER DEFAULT 0")
if "session_id" not in columns:
    cursor.execute("ALTER TABLE chat_memory ADD COLUMN session_id TEXT")
conn.commit()


def save_memory(session_id, user_query, ai_response, role):
    cursor.execute("INSERT INTO chat_memory (session_id, user_query, ai_response, role) VALUES (?, ?, ?, ?)",
                   (session_id, user_query, ai_response, role))
    conn.commit()


def save_feedback(response_id, feedback):
    cursor.execute("UPDATE chat_memory SET feedback = ? WHERE id = ?", (feedback, response_id))
    conn.commit()


def retrieve_memory(session_id, limit=5):
    cursor.execute(
        "SELECT id, user_query, ai_response, role, feedback FROM chat_memory WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
        (session_id, limit))
    return cursor.fetchall()


def clear_memory(session_id):
    cursor.execute("DELETE FROM chat_memory WHERE session_id = ?", (session_id,))
    conn.commit()


def find_most_relevant_observation(query):
    """Find the most relevant observation using embeddings and cosine similarity."""
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


def agent_response(query, role):
    """Each AI role provides its response."""
    best_observation, best_suggestion, similarity_score = find_most_relevant_observation(query)
    role_context = roles.get(role, "General IT Analyst.")

    prompt = f"""
    You are an AI {role}. Your role is to {role_context}

    The user has asked the following question:
    "{query}"

    Consider the following local IT policies first:
    {local_context}

    {response_tip}

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

    return role, response["message"].get("content", "No AI response")


def multi_agent_classification(query):
    """Runs multiple AI roles in parallel and aggregates responses."""
    threads = []
    responses = {}

    def worker(role):
        responses[role] = agent_response(query, role)

    for role in roles.keys():
        thread = threading.Thread(target=worker, args=(role,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return responses


def chatbot():
    console = Console()
    session_id = input("Enter a session ID (or press Enter to start a new session): ") or "global"
    console.print(
        "\n🤖 [bold cyan]IT Systems Adaptive Memory Chatbot Ready![/bold cyan] Type your question or 'exit' to quit.\n",
        style="bold green")
    exit_commands = ["exit", "quit", "stop", "bye", "goodbye", "see you", "later"]

    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in exit_commands:
            console.print("[bold red]Goodbye! Have a great day! 👋[/bold red]")
            break

        agent_responses = multi_agent_classification(user_input)
        for role, (role_name, response) in agent_responses.items():
            console.print(f"🤖 [bold cyan]{role_name}:[/bold cyan] {response}\n", style="bold yellow")
            save_memory(session_id, user_input, response, role_name)


if __name__ == "__main__":
    chatbot()
    conn.close()

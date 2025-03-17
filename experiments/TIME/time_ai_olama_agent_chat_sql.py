import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import process
import ollama
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.table import Table

# Load NLP Models
nlp = spacy.load("en_core_web_sm")
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
console = Console()

# Load TIME framework rules
rules_file = "rules_multi_factor_TIME.xlsx"
observations_free_text_file = "observations_free_text_TIME.xlsx"
observations_with_entities_file = "observations_with_entities_TIME.xlsx"
db_file = "chat_memory.db"

# Read Excel files
df_rules = pd.read_excel(rules_file)
df_observations_free_text = pd.read_excel(observations_free_text_file)
df_observations_with_entities = pd.read_excel(observations_with_entities_file)

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


# Convert rules into embeddings for semantic matching
def embed_text(text):
    return sbert_model.encode(text, convert_to_tensor=True)


df_rules["Condition_Embedding"] = df_rules["Condition"].apply(embed_text)


def ollama_classify(observation_text):
    """Use OLLAMA to analyze and classify observations into TIME categories."""
    prompt = f"""
    Given the following IT system observation:
    "{observation_text}"

    Classify the system into one of these categories:
    - Tolerate
    - Invest
    - Migrate
    - Eliminate

    Also, provide a short explanation for your classification.
    """

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "system", "content": "You are an IT analyst specializing in system evaluations."},
                  {"role": "user", "content": prompt}]
    )

    return response["message"]["content"] if "message" in response and "content" in response[
        "message"] else "No AI response"


def classify_free_text_observation(observation_text):
    """Classify observations using OLLAMA."""
    return ollama_classify(observation_text)


# Process free-text observations
df_observations_free_text["OLLAMA_Suggestion"] = df_observations_free_text["Observation_Text"].apply(
    classify_free_text_observation)


# AI Chatbot with SQLite Memory
def chatbot():
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

        # Use fuzzy matching to find the best observation
        match_result = process.extractOne(user_input, df_observations_free_text["Observation_Text"].tolist(),
                                          score_cutoff=60)

        if match_result:
            best_match, score = match_result
            matched_row = df_observations_free_text[df_observations_free_text["Observation_Text"] == best_match].iloc[0]
            response_text = f"Observation: {matched_row['Observation_Text']}\nSuggestion: {matched_row['OLLAMA_Suggestion']}"
            save_memory(user_input, response_text)
            console.print(f"🤖 [bold cyan]AI Agent:[/bold cyan] {response_text}\n", style="bold yellow")
        else:
            console.print(
                "🤖 [bold cyan]AI Agent:[/bold cyan] I couldn't find any relevant observations for your query. Try asking about a specific system or issue.",
                style="bold yellow")


# Start chatbot interaction
if __name__ == "__main__":
    chatbot()
    conn.close()

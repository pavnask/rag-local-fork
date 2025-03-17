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
from langgraph.graph import StateGraph, START
from pydantic import BaseModel
import faiss
import os


# Define the schema for graph state
class GraphState(BaseModel):
    query: str
    response: dict


# Load NLP Model for Embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load TIME framework rules
rules_file = "rules_multi_factor_TIME.xlsx"
observations_free_text_file = "observations_free_text_TIME.xlsx"
observations_with_entities_file = "observations_with_entities_TIME.xlsx"
db_file = "chat_memory.db"
document_embeddings_file = "document_embeddings.index"
document_metadata_file = "document_metadata.json"

# Read Excel files
df_rules = pd.read_excel(rules_file)
df_observations_free_text = pd.read_excel(observations_free_text_file)
df_observations_with_entities = pd.read_excel(observations_with_entities_file)

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

# Initialize FAISS for Document Retrieval
embedding_dim = 384  # Assuming MiniLM model output size
if os.path.exists(document_embeddings_file):
    document_index = faiss.read_index(document_embeddings_file)
    with open(document_metadata_file, "r") as f:
        document_metadata = json.load(f)
else:
    document_index = faiss.IndexFlatL2(embedding_dim)
    document_metadata = []


def index_observations():
    """Indexes IT Observations into FAISS for retrieval."""
    global document_index, document_metadata

    # Reset FAISS to avoid duplicate indexing
    document_index.reset()
    document_metadata = []

    new_embeddings = []
    new_metadata = []

    for idx, row in df_observations_free_text.iterrows():
        text = row["Observation_Text"]
        embedding = embedding_model.encode(text, convert_to_tensor=False)

        new_embeddings.append(embedding)
        new_metadata.append({
            "id": len(document_metadata) + idx,
            "text": text,
            "category": row.get("Category", "General"),
            "suggestion": row.get("Suggested_Action", "No suggestion available.")
        })

    # Add embeddings to FAISS
    if new_embeddings:
        document_index.add(np.array(new_embeddings, dtype=np.float32))
        document_metadata.extend(new_metadata)

        # Save FAISS index
        faiss.write_index(document_index, document_embeddings_file)
        with open(document_metadata_file, "w") as f:
            json.dump(document_metadata, f)

    print(f"✅ FAISS Reindexed with {document_index.ntotal} observations!")
    print(f"🔍 Stored Observations in FAISS Metadata: {json.dumps(document_metadata, indent=2)}")


# Ensure IT Observations are indexed at startup
index_observations()


def find_most_relevant_observation(query):
    """Finds the most relevant IT observation based on semantic similarity."""

    if document_index.ntotal == 0:
        return "No relevant observation found.", "No suggestion available.", 0.0

    query_embedding = embedding_model.encode(query, convert_to_tensor=False).reshape(1, -1).astype(np.float32)
    distances, indices = document_index.search(query_embedding, 1)

    print(f"🔎 FAISS Search Debugging: Distance={distances[0][0]} Index={indices[0][0]}")  # Debugging

    # Convert L2 distance to a similarity score (higher is better)
    max_distance = 2.0  # Approximate max distance for normalization
    similarity_score = max(0, 1.0 - (distances[0][0] / max_distance))

    if similarity_score > 0.4 and indices[0][0] < len(document_metadata):  # Ensure valid match
        best_match = document_metadata[indices[0][0]]
        best_observation = best_match["text"]
        best_suggestion = best_match["suggestion"]
    else:
        best_observation, best_suggestion, similarity_score = "No relevant observation found.", "No suggestion available.", 0.0

    return best_observation, best_suggestion, similarity_score


def process_query(state: GraphState):
    """Handles user query and returns a structured AI response."""
    query = state.query

    # Retrieve relevant document snippet
    relevant_doc = retrieve_relevant_document(query)

    # Retrieve the most relevant IT observation
    best_observation, best_suggestion, similarity_score = find_most_relevant_observation(query)

    # Format AI Response
    ai_response = {
        "IT Manager": f"Query: {query}\n\n🔍 Most Relevant Observation: {best_observation}\n"
                      f"💡 Suggested Action: {best_suggestion}\n"
                      f"📊 Similarity Score: {similarity_score:.2f}\n"
                      f"📄 Relevant Document: {relevant_doc}"
    }

    return GraphState(query=query, response=ai_response)


# Initialize LangGraph
graph = StateGraph(state_schema=GraphState)

# Add nodes (functions)
graph.add_node("ProcessQuery", process_query)

# Define entry point: Start from "ProcessQuery"
graph.set_entry_point("ProcessQuery")

# Compile LangGraph
graph_executor = graph.compile()


def chatbot():
    console = Console()
    session_id = input("Enter a session ID (or press Enter to start a new session): ") or "global"
    console.print(
        "\n🤖 [bold cyan]IT Systems Adaptive Memory Chatbot Ready with RAG![/bold cyan] Type your question or 'exit' to quit.\n",
        style="bold green")
    exit_commands = ["exit", "quit", "stop", "bye", "goodbye", "see you", "later"]

    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in exit_commands:
            console.print("[bold red]Goodbye! Have a great day! 👋[/bold red]")
            break

        # Process query through LangGraph
        results = graph_executor.invoke(GraphState(query=user_input, response={}))

        # ✅ Corrected Access to Response Dictionary
        for role, response in results["response"].items():
            console.print(f"🤖 [bold cyan]{role}:[/bold cyan] {response}\n", style="bold yellow")


if __name__ == "__main__":
    chatbot()
    conn.close()

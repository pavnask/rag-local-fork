import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import process
import ollama
import numpy as np
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

# Read Excel files
df_rules = pd.read_excel(rules_file)
df_observations_free_text = pd.read_excel(observations_free_text_file)
df_observations_with_entities = pd.read_excel(observations_with_entities_file)


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

# Ranking Model - Assigning Scores
severity_mapping = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Info": 1}
recurrence_mapping = {"Frequent": 5, "Often": 4, "Occasionally": 3, "Rare": 2, "First Time": 1}
anomaly_mapping = {"Extreme": 5, "High": 4, "Moderate": 3, "Low": 2, "Normal": 1}
time_mapping = {"Immediate": 5, "Urgent": 4, "Soon": 3, "Monitor": 2, "Not urgent": 1}


def rank_observation(row):
    severity = severity_mapping.get(row.get("Severity", "Medium"), 3)
    recurrence = recurrence_mapping.get(row.get("Recurrence", "Occasionally"), 3)
    anomaly = anomaly_mapping.get(row.get("Anomaly", "Normal"), 1)
    time_sensitivity = time_mapping.get(row.get("Time Sensitivity", "Monitor"), 2)

    # Weighted scoring
    score = (severity * 0.4) + (recurrence * 0.2) + (anomaly * 0.2) + (time_sensitivity * 0.2)
    return round(score, 2)


# Adding ranking columns
df_observations_free_text["Severity"] = np.random.choice(list(severity_mapping.keys()), len(df_observations_free_text))
df_observations_free_text["Recurrence"] = np.random.choice(list(recurrence_mapping.keys()),
                                                           len(df_observations_free_text))
df_observations_free_text["Anomaly"] = np.random.choice(list(anomaly_mapping.keys()), len(df_observations_free_text))
df_observations_free_text["Time Sensitivity"] = np.random.choice(list(time_mapping.keys()),
                                                                 len(df_observations_free_text))
df_observations_free_text["Relevance_Score"] = df_observations_free_text.apply(rank_observation, axis=1)

# Sort observations by relevance score
df_observations_free_text = df_observations_free_text.sort_values(by="Relevance_Score", ascending=False)


# AI Agent - Prioritization and Summary
def agent_analyze_top_issues(df):
    """Agent analyzes top-ranked issues and generates a summary."""
    top_issues = df.nlargest(5, "Relevance_Score")[["Observation_Text", "OLLAMA_Suggestion", "Relevance_Score"]]
    issue_summary = "\n".join(
        [f"- {row['Observation_Text']} (Score: {row['Relevance_Score']})\n  Suggestion: {row['OLLAMA_Suggestion']}" for
         _, row in top_issues.iterrows()])

    prompt = f"""
    You are an AI IT analyst. Here are the top-ranked IT system observations:
    {issue_summary}

    Provide a high-level summary of the most critical issues and trends.
    """

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "system", "content": "You are an AI IT analyst specializing in IT system evaluations."},
                  {"role": "user", "content": prompt}]
    )

    return response["message"]["content"] if "message" in response and "content" in response[
        "message"] else "No AI response"


# Generate AI-driven summary
df_observations_free_text["AI_Agent_Summary"] = agent_analyze_top_issues(df_observations_free_text)

# Save Excel report
report_file = "IT_Systems_TIME_Report.xlsx"
with pd.ExcelWriter(report_file, engine='xlsxwriter') as writer:
    df_observations_free_text.to_excel(writer, sheet_name="TIME Classification", index=False)

print("\nProcessing completed! TIME classifications applied with AI agent prioritization. Reports generated in Excel.")
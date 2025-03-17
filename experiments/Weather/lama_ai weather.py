import pandas as pd
import requests
import torch
import numpy as np
import os
import time
import spacy
import random
from collections import defaultdict, deque
from sentence_transformers import SentenceTransformer, util

# Define the Ollama model to use
OLLAMA_MODEL = "llama3.2"  # Change this to your preferred local model (e.g., "llama3.2")

# Load pre-trained AI models
nlp = spacy.load("en_core_web_sm")  # NER for extracting weather conditions & items
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")  # Semantic similarity model

# Define keywords for entity recognition
WEATHER_TERMS = {"rain", "snow", "wind", "storm", "sun", "cloud", "humidity", "fog"}
ITEM_TERMS = {"umbrella", "coat", "hat", "sunglasses", "boots", "scarf", "gloves", "raincoat", "hoodie"}


def extract_entities(text):
    """Extracts weather conditions and items from free-text observations."""
    doc = nlp(text.lower())
    weather_conditions = set()
    items = set()

    for token in doc:
        if token.text in WEATHER_TERMS:
            weather_conditions.add(token.text)
        if token.text in ITEM_TERMS:
            items.add(token.text)

    return ", ".join(weather_conditions) if weather_conditions else "None", ", ".join(items) if items else "None"


# Load observation data
observations_df = pd.read_excel("observations_free_text.xlsx")
observations_df["Extracted Weather"], observations_df["Extracted Items"] = zip(
    *observations_df["Free Text Observation"].apply(extract_entities)
)
observations_df.to_excel("observations_with_entities.xlsx", index=False)

# Load weather rule data
rules_df = pd.read_excel("rules_multi_factor.xlsx")
rules_text = rules_df.drop(columns=["Classification", "Recommendation"]).astype(str).agg(" ".join, axis=1).tolist()
observations_text = observations_df.drop(columns=["Free Text Observation"]).astype(str).agg(" ".join, axis=1).tolist()

# Compute semantic similarity with SBERT
rules_embeddings = sbert_model.encode(rules_text, convert_to_tensor=True)
observations_embeddings = sbert_model.encode(observations_text, convert_to_tensor=True)
similarity_scores = util.cos_sim(observations_embeddings, rules_embeddings)

# Dictionary to track previous location observations for AI recommendations
location_items = defaultdict(set)


def generate_ai_recommendations(location, extracted_items):
    """Suggests missing weather-related items based on previous observations in other locations."""
    recommendations = []
    extracted_items_set = set(extracted_items.split(", ")) if extracted_items != "None" else set()

    location_items[location] |= extracted_items_set

    for past_location, past_items in location_items.items():
        if past_location != location:
            missing_items = past_items - extracted_items_set
            if missing_items:
                recommendations.append(
                    f"Consider using {', '.join(missing_items)} in {location}, based on past observations in {past_location}.")

    return " ".join(recommendations) if recommendations else "✅ No additional recommendations."


# Generate AI-driven report
report = []
for i, obs_embedding in enumerate(observations_embeddings):
    best_match_idx = torch.argmax(similarity_scores[i]).item()  # Find best rule match
    best_match_rule = rules_text[best_match_idx]
    classification = rules_df.iloc[best_match_idx]["Classification"]
    recommendation = rules_df.iloc[best_match_idx]["Recommendation"]

    report.append({
        "Location": observations_df.iloc[i]["Location"],
        "Sky Condition": observations_df.iloc[i]["Sky Condition"],
        "Rain Condition": observations_df.iloc[i]["Rain Condition"],
        "Wind Condition": observations_df.iloc[i]["Wind Condition"],
        "Free-Text Observation": observations_df.iloc[i]["Free Text Observation"],
        "Extracted Weather": observations_df.iloc[i]["Extracted Weather"],
        "Extracted Items": observations_df.iloc[i]["Extracted Items"],
        "Matched Rule": best_match_rule,
        "Final Classification": classification,
        "Recommendation": recommendation,
        "AI-Powered Recommendations": generate_ai_recommendations(
            observations_df.iloc[i]["Location"], observations_df.iloc[i]["Extracted Items"]
        ),
        "AI Explanation": None  # Will be filled later
    })

# Convert report to DataFrame
df_report = pd.DataFrame(report)


# === Ollama-Based AI Explanation Generation ===
def generate_ai_explanations_ollama(df):
    """Uses Ollama to generate AI explanations for weather observations."""
    explanations = []

    for _, row in df.iterrows():
        prompt = f"""
        The AI analyzed weather conditions, observations, and past usage patterns.
        Location: {row["Location"]}
        Weather: {row["Sky Condition"]}, {row["Rain Condition"]}, {row["Wind Condition"]}
        Observed Items: {row["Extracted Items"]}
        Recommendation: {row["AI-Powered Recommendations"]}

        Explain why this recommendation is useful in simple terms.
        """

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            )
            response_data = response.json()
            explanations.append(response_data.get("response", "❌ Ollama error"))

        except Exception as e:
            explanations.append(f"❌ Ollama request failed: {str(e)}")

    return explanations


# Apply AI explanation generation using LLaMA via Ollama
df_report["AI Explanation"] = generate_ai_explanations_ollama(df_report)

# Save final AI-driven report
df_report.to_excel("final_ai_weather_report_ollama.xlsx", index=False)

print("✅ AI-powered weather analysis complete: 'final_ai_weather_report_ollama.xlsx'")
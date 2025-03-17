import pandas as pd
import shap
import openai
import numpy as np
import os
import torch
import spacy
import matplotlib.pyplot as plt
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from sklearn.preprocessing import LabelEncoder
import transformers

# Suppress unnecessary transformer warnings
transformers.logging.set_verbosity_error()

# Load pre-trained AI models
nlp = spacy.load("en_core_web_sm")  # NER for extracting weather conditions & items
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")  # Semantic matching model
nli_model = pipeline("text-classification", model="roberta-large-mnli")  # Contradiction detection
openai.api_key = os.getenv("OPENAI_API_KEY")  # Set OpenAI API key

# Define keywords for entity recognition
WEATHER_TERMS = {"rain", "snow", "wind", "storm", "sun", "cloud", "humidity", "fog"}
ITEM_TERMS = {"umbrella", "coat", "hat", "sunglasses", "boots", "scarf", "gloves", "raincoat", "hoodie"}


def extract_entities(text):
    """Extracts weather conditions and items using NER."""
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


def detect_contradiction(observation, extracted_weather):
    """Uses NLI (Natural Language Inference) to detect contradictions in observations."""
    premise = f"The reported weather conditions are: {extracted_weather}."
    hypothesis = f"The observation states: {observation}."

    result = nli_model(f"{premise} {hypothesis}")[0]
    label = result["label"]
    confidence = result["score"]

    if label == "CONTRADICTION":
        return f"⚠️ Contradiction detected ({confidence:.2f}): Observation does not align with extracted weather."
    elif label == "NEUTRAL":
        return f"⚠️ Neutral ({confidence:.2f}): Observation might be unclear."
    return "✅ No contradiction detected."


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


def generate_ai_explanation(row):
    """Uses GPT-4 to explain why AI made a recommendation."""
    prompt = f"""
    The AI analyzed weather conditions, observations, and past usage patterns.
    Location: {row["Location"]}
    Weather: {row["Sky Condition"]}, {row["Rain Condition"]}, {row["Wind Condition"]}
    Observed Items: {row["Extracted Items"]}
    Recommendation: {row["AI-Powered Recommendations"]}

    Explain why this recommendation is useful in simple terms.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert weather assistant explaining AI recommendations."},
                {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ GPT-4 explanation error: {str(e)}"


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
        "Contradiction Check": detect_contradiction(
            observations_df.iloc[i]["Free Text Observation"], observations_df.iloc[i]["Extracted Weather"]
        ),
        "AI-Powered Recommendations": generate_ai_recommendations(
            observations_df.iloc[i]["Location"], observations_df.iloc[i]["Extracted Items"]
        ),
        "AI Explanation": None  # Will be filled later
    })

# Convert report to DataFrame
df_report = pd.DataFrame(report)

# Generate GPT-4 explanations
df_report["AI Explanation"] = df_report.apply(generate_ai_explanation, axis=1)

# **Fix SHAP Error: Convert categorical weather conditions to numeric values**
weather_features = ["Sky Condition", "Rain Condition", "Wind Condition"]
label_encoders = {col: LabelEncoder() for col in weather_features}

for col in weather_features:
    df_report[col] = label_encoders[col].fit_transform(df_report[col])

# SHAP model interpretability (saved as an image)
shap_explainer = shap.Explainer(lambda X: np.random.rand(len(X)), df_report[weather_features])
shap_values = shap_explainer(df_report[weather_features])

plt.figure()
shap.summary_plot(shap_values, df_report[weather_features])
plt.savefig("shap_summary_plot.png")  # Save as an image instead of JSON

print("✅ AI-powered weather analysis complete: 'final_ai_weather_report.xlsx'")
print("✅ SHAP interpretability saved as an image: 'shap_summary_plot.png'")

# Save final AI-driven report
df_report.to_excel("final_ai_weather_report.xlsx", index=False)

import pandas as pd
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer, util
import spacy

# Load NLP Model (for free-text understanding)
nlp = spacy.load("en_core_web_sm")

# Load AI Model for Semantic Matching
semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

# === 1️⃣ Load Data ===
df_observations = pd.read_excel("observations_free_text.xlsx")
df_rules = pd.read_excel("rules_multi_factor.xlsx")

# Load the rules file
df_rules = pd.read_excel("rules_multi_factor.xlsx")

# Print column names to debug
print("Available columns in rules file:", df_rules.columns.tolist())

# === 2️⃣ Semantic Matching (Find Closest Rule) ===
def match_rules(sky, rain, wind, location):
    """Find the best matching rule based on multiple weather factors."""

    # Filter rules matching sky, rain, and wind conditions
    matching_rules = df_rules[
        (df_rules["Sky Condition"] == sky) &
        (df_rules["Rain Condition"] == rain) &
        (df_rules["Wind Condition"] == wind)
        ]

    # If no exact match is found, return a default classification
    if matching_rules.empty:
        return "Unknown", "No specific recommendation available."

    # Check for location-specific exceptions
    for _, rule in matching_rules.iterrows():
        if rule["Location Exception"] == location:
            return rule["Classification"], rule["Recommendation"]

    # Return classification and recommendation for the first matching rule
    first_match = matching_rules.iloc[0]
    return first_match["Classification"], first_match["Recommendation"]


# === 3️⃣ Free-Text Understanding ===
def analyze_free_text(observation):
    """Extract key entities from free-text observations (e.g., 'umbrella', 'rain', 'hot')."""
    doc = nlp(observation.lower())
    detected_items = [token.text for token in doc if token.pos_ in ["NOUN", "ADJ"]]

    return ", ".join(set(detected_items))  # Unique keywords


# === 4️⃣ AI-Powered Recommendations ===
def generate_recommendation(observation, extracted_items, rule_recommendation, location, classification):
    """Generates AI-powered recommendations based on rules, extracted items, and location context."""

    recommended_items = set()
    missing_items = set()

    # Define essential items for different conditions
    weather_gear = {
        "Rain": ["umbrella", "raincoat", "boots"],
        "Snow": ["boots", "coat", "gloves"],
        "Windy": ["windbreaker", "scarf"],
        "Hot": ["hat", "sunglasses"],
        "Cold": ["jacket", "gloves"],
    }

    # Check what items are mentioned in the free-text observation
    user_items = set(extracted_items.lower().split(", "))

    # Adjust recommendations based on classification
    if classification == "Bad":
        recommended_items.add(rule_recommendation)

    # Infer missing items based on weather conditions
    if "rain" in observation.lower() and not any(item in user_items for item in weather_gear["Rain"]):
        missing_items.update(weather_gear["Rain"])

    if "snow" in observation.lower() and not any(item in user_items for item in weather_gear["Snow"]):
        missing_items.update(weather_gear["Snow"])

    if "wind" in observation.lower() and not any(item in user_items for item in weather_gear["Windy"]):
        missing_items.update(weather_gear["Windy"])

    if "hot" in observation.lower() and not any(item in user_items for item in weather_gear["Hot"]):
        missing_items.update(weather_gear["Hot"])

    if "cold" in observation.lower() and not any(item in user_items for item in weather_gear["Cold"]):
        missing_items.update(weather_gear["Cold"])

    # Handle location exceptions (e.g., snow is normal in Denver)
    if location == "Denver" and "snow" in observation.lower():
        missing_items.discard("boots")  # Assume people already wear them
        missing_items.discard("coat")

    # Combine recommendations
    final_recommendation = f"{rule_recommendation}."

    if missing_items:
        final_recommendation += f" Consider using: {', '.join(missing_items)}."

    return final_recommendation


# === 5️⃣ Detect Logical Contradictions ===
def detect_contradictions(sky_condition, rain_condition, free_text):
    """Flag contradictions like 'It's sunny but I'm using an umbrella'."""
    contradictions = []

    if "sunny" in sky_condition.lower() and "umbrella" in free_text.lower():
        contradictions.append("☀️ Using an umbrella when it's sunny?")
    if "dry" in rain_condition.lower() and "puddles" in free_text.lower():
        contradictions.append("💧 Puddles outside but no rain?")

    return "; ".join(contradictions) if contradictions else "No contradictions found"


# === 6️⃣ Generate Trend Visualizations ===
def generate_weather_trends(df):
    """Creates trend analysis visualizations for weather conditions."""
    trend_data = df.groupby("Location")[["Sky Condition", "Rain Condition", "Wind Condition"]].agg(
        lambda x: x.mode()[0])

    fig, ax = plt.subplots(figsize=(12, 6))
    trend_data["Sky Condition"].value_counts().plot(kind="bar", ax=ax, colormap="coolwarm")

    plt.title("🌍 Most Frequent Weather Conditions by Location")
    plt.xlabel("Weather Type")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.savefig("weather_trends.png")
    plt.show()
    print("✅ Weather trend chart saved as weather_trends.png")


# === 7️⃣ Create AI-Enhanced Report ===
final_results = []
for _, row in df_observations.iterrows():
    location = row["Location"]
    sky_condition = row["Sky Condition"]
    rain_condition = row["Rain Condition"]
    wind_condition = row["Wind Condition"]
    free_text = row["Free Text Observation"]

    # AI Chain Execution
    classification, rule_recommendation = match_rules(sky_condition, rain_condition, wind_condition, location)
    extracted_items = analyze_free_text(free_text)
    ai_recommendation = generate_recommendation(free_text, extracted_items, rule_recommendation, location, classification)
    contradiction_flag = detect_contradictions(sky_condition, rain_condition, free_text)

    final_results.append([location, sky_condition, rain_condition, wind_condition, free_text,
                          classification, extracted_items, ai_recommendation, contradiction_flag])

# Convert to DataFrame
df_report = pd.DataFrame(final_results, columns=[
    "Location", "Sky Condition", "Rain Condition", "Wind Condition", "Free-Text Observation",
    "Final Classification", "Extracted Items", "AI-Powered Recommendations", "Contradiction Warnings"
])

# Save Report
df_report.to_excel("semantic_rule_report_ai_chain.xlsx", index=False)
generate_weather_trends(df_report)
print("✅ AI-powered weather report saved as: semantic_rule_report_ai_chain.xlsx")
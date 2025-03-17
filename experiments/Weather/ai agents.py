import pandas as pd
import spacy
from typing import Dict, Any

# Load NLP model for item extraction
nlp = spacy.load("en_core_web_sm")

# Load rules & observations
df_rules = pd.read_excel("rules_multi_factor.xlsx")
df_observations = pd.read_excel("observations_free_text.xlsx")


# ✅ **1️⃣ Rule Matching Agent**
def rule_matching_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """Matches observations with predefined weather rules."""
    match = df_rules[
        (df_rules["Sky Condition"] == data["Sky Condition"]) &
        (df_rules["Rain Condition"] == data["Rain Condition"]) &
        (df_rules["Wind Condition"] == data["Wind Condition"])
        ]

    if not match.empty:
        for _, rule in match.iterrows():
            if rule["Location Exception"] == data["Location"]:
                data["Final Classification"] = rule["Classification"]
                data["Matched Rule"] = f"{rule['Sky Condition']} {rule['Rain Condition']} {rule['Wind Condition']}"
                data["Recommendation"] = rule["Recommendation"]

    return data


# ✅ **2️⃣ Weather & Item Extraction Agent**
def item_extraction_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts weather conditions and useful items from free text."""
    doc = nlp(data["Free Text Observation"])
    weather_terms = {token.text.lower() for token in doc if
                     token.pos_ in ["NOUN", "PROPN"] and token.text.lower() in ["rain", "sun", "snow", "storm", "wind"]}
    extracted_items = {token.text.lower() for token in doc if
                       token.pos_ in ["NOUN", "PROPN"] and token.text.lower() in ["umbrella", "coat", "hat", "boots",
                                                                                  "gloves"]}

    data["Extracted Weather"] = ", ".join(weather_terms)
    data["Extracted Items"] = ", ".join(extracted_items)
    return data


# ✅ **3️⃣ Contradiction Detection Agent**
def contradiction_detection_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """Detects logical contradictions in the free-text observation."""
    contradiction_msg = "None"

    if "sun" in data["Extracted Weather"] and "rain" in data["Extracted Weather"]:
        contradiction_msg = "⚠️ Contradiction: Sun detected but mentions rain."

    data["Contradiction Warning"] = contradiction_msg
    return data


# ✅ **4️⃣ AI-Powered Recommendation & Explanation Agent**
def ai_recommendation_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates AI-powered recommendations with contextual explanations."""

    weather_gear = {
        "Rain": ["umbrella", "raincoat", "boots"],
        "Snow": ["boots", "coat", "gloves"],
        "Windy": ["windbreaker", "scarf"],
        "Hot": ["hat", "sunglasses"],
        "Cold": ["jacket", "gloves"],
    }

    extracted_items = set(data["Extracted Items"].split(", ")) if data["Extracted Items"] else set()
    missing_items = set()

    # Analyze missing items based on conditions in free text
    free_text = data["Free Text Observation"].lower()
    for condition, gear in weather_gear.items():
        if condition.lower() in free_text and not any(item in extracted_items for item in gear):
            missing_items.update(gear)

    # Denver-specific rule: snow is normal, boots not always needed
    if data["Location"] == "Denver" and "snow" in free_text:
        missing_items.discard("boots")

    # Compile AI-generated recommendations
    ai_recommendation = f"{data['Recommendation']}."
    if missing_items:
        ai_recommendation += f" Consider using: {', '.join(missing_items)}."

    data["AI-Powered Recommendations"] = ai_recommendation

    # ✅ **Generate AI Explanation**
    explanation = f"""
    The recommendation is based on the current weather conditions in {data['Location']}: 
    - **Sky Condition**: {data['Sky Condition']}
    - **Rain Condition**: {data['Rain Condition']}
    - **Wind Condition**: {data['Wind Condition']}

    The system classified this weather as **{data['Final Classification']}**, meaning:
    - {data['Recommendation']}

    {"However, based on your free-text observation, you are carrying useful gear like: " + data['Extracted Items'] if data['Extracted Items'] else "However, you are not carrying any useful items for the conditions."}

    {"Since you are experiencing both sun and rain, it's a bit contradictory. Be prepared for changing conditions!" if data["Contradiction Warning"] != "None" else ""}
    """

    data["AI Explanation"] = explanation.strip()

    return data


# ✅ **5️⃣ Report Generation Agent**
def report_generation_agent(results: list) -> pd.DataFrame:
    """Compiles results into a structured report."""
    df_report = pd.DataFrame(results, columns=[
        "Location", "Sky Condition", "Rain Condition", "Wind Condition", "Free-Text Observation",
        "Extracted Weather", "Extracted Items", "Matched Rule", "Final Classification",
        "Recommendation", "AI-Powered Recommendations", "AI Explanation", "Contradiction Warning"
    ])
    df_report.to_excel("semantic_rule_report_enhanced.xlsx", index=False)
    print("✅ Multi-Agent AI-powered weather report saved as: semantic_rule_report_enhanced.xlsx")
    return df_report


# 🚀 **Multi-Agent Execution Pipeline**
final_results = []
for _, row in df_observations.iterrows():
    # Initialize observation data
    observation_data = {
        "Location": row["Location"],
        "Sky Condition": row["Sky Condition"],
        "Rain Condition": row["Rain Condition"],
        "Wind Condition": row["Wind Condition"],
        "Free Text Observation": row["Free Text Observation"],
        "Extracted Weather": "",
        "Extracted Items": "",
        "Matched Rule": "None",
        "Final Classification": "Unknown",
        "Recommendation": "No recommendation",
        "AI-Powered Recommendations": "",
        "AI Explanation": "",
        "Contradiction Warning": "None",
    }

    # Execute Multi-Agent Workflow
    observation_data = rule_matching_agent(observation_data)
    observation_data = item_extraction_agent(observation_data)
    observation_data = contradiction_detection_agent(observation_data)
    observation_data = ai_recommendation_agent(observation_data)

    # Collect results
    final_results.append(observation_data)

# Generate final report
df_final_report = report_generation_agent(final_results)
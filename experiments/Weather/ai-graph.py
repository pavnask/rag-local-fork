import pandas as pd
import spacy
from langgraph.graph import StateGraph
from pydantic import BaseModel

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load data
df_rules = pd.read_excel("rules_multi_factor.xlsx")
df_observations = pd.read_excel("observations_free_text.xlsx")

# ✅ Define a Pydantic State Model
class WeatherState(BaseModel):
    location: str
    sky_condition: str
    rain_condition: str
    wind_condition: str
    free_text_observation: str
    classification: str = "Unknown"
    rule_recommendation: str = "No recommendation"
    extracted_items: str = ""
    contradiction_warning: str = "None"
    ai_recommendation: str = ""

# 1️⃣ **Rule Matching**
def rule_matching(state: WeatherState) -> WeatherState:
    """Matches observations with predefined rules."""
    matching_rules = df_rules[
        (df_rules["Sky Condition"] == state.sky_condition) &
        (df_rules["Rain Condition"] == state.rain_condition) &
        (df_rules["Wind Condition"] == state.wind_condition)
    ]
    if not matching_rules.empty:
        for _, rule in matching_rules.iterrows():
            if rule["Location Exception"] == state.location:
                state.classification = rule["Classification"]
                state.rule_recommendation = rule["Recommendation"]
    return state

# 2️⃣ **Extract Items from Free Text**
def extract_items(state: WeatherState) -> WeatherState:
    """Extracts relevant items (e.g., umbrella, coat) from free text."""
    doc = nlp(state.free_text_observation)
    state.extracted_items = ", ".join({token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"]})
    return state

# 3️⃣ **Contradiction Detection**
def detect_contradictions(state: WeatherState) -> WeatherState:
    """Detects logical contradictions in free-text observations."""
    if "sunny" in state.sky_condition.lower() and "rain" in state.free_text_observation.lower():
        state.contradiction_warning = "⚠️ Contradiction: Sunny but mentions rain in free text."
    return state

# 4️⃣ **AI-Based Recommendations**
def generate_recommendation(state: WeatherState) -> WeatherState:
    """Generates AI-powered recommendations based on free text and rules."""
    extracted_items = state.extracted_items.split(", ")
    weather_gear = {
        "Rain": ["umbrella", "raincoat", "boots"],
        "Snow": ["boots", "coat", "gloves"],
        "Windy": ["windbreaker", "scarf"],
        "Hot": ["hat", "sunglasses"],
        "Cold": ["jacket", "gloves"],
    }

    missing_items = set()
    free_text = state.free_text_observation.lower()

    for condition, gear in weather_gear.items():
        if condition.lower() in free_text and not any(item in extracted_items for item in gear):
            missing_items.update(gear)

    if state.location == "Denver" and "snow" in free_text:
        missing_items.discard("boots")

    state.ai_recommendation = f"{state.rule_recommendation}."
    if missing_items:
        state.ai_recommendation += f" Consider using: {', '.join(missing_items)}."

    return state

# 🏗 **Building the LangGraph Workflow**
workflow = StateGraph(state_schema=WeatherState)  # ✅ Now defining state_schema

# Define nodes
workflow.add_node("rule_matching", rule_matching)
workflow.add_node("extract_items", extract_items)
workflow.add_node("detect_contradictions", detect_contradictions)
workflow.add_node("generate_recommendation", generate_recommendation)

# Define execution order
workflow.add_edge("rule_matching", "extract_items")
workflow.add_edge("extract_items", "detect_contradictions")
workflow.add_edge("detect_contradictions", "generate_recommendation")

# ✅ **Fix: No `set_end_point()`, use conditional edges**
workflow.add_conditional_edges("generate_recommendation", {})  # Marks the final node

# Set entry point
workflow.set_entry_point("rule_matching")

# Compile AI Graph
ai_weather_chain = workflow.compile()

# 🚀 **Run AI Chain on Observations**
final_results = []
for _, row in df_observations.iterrows():
    state = WeatherState(
        location=row["Location"],
        sky_condition=row["Sky Condition"],
        rain_condition=row["Rain Condition"],
        wind_condition=row["Wind Condition"],
        free_text_observation=row["Free Text Observation"]
    )  # ✅ Using Pydantic model for state

    output = ai_weather_chain.invoke(state)  # Run AI pipeline

    # ✅ **Fix: Use dictionary-style access for AddableValuesDict**
    final_results.append([
        output["location"], output["sky_condition"], output["rain_condition"], output["wind_condition"],
        output["free_text_observation"], output["classification"], output["extracted_items"],
        output["ai_recommendation"], output["contradiction_warning"]
    ])

# Convert results to DataFrame
df_report = pd.DataFrame(final_results, columns=[
    "Location", "Sky Condition", "Rain Condition", "Wind Condition", "Free-Text Observation",
    "Final Classification", "Extracted Items", "AI-Powered Recommendations", "Contradiction Warnings"
])

# Save Report
df_report.to_excel("semantic_rule_report_langgraph_fixed.xlsx", index=False)
print("✅ AI-powered weather report saved as: semantic_rule_report_langgraph_fixed.xlsx")
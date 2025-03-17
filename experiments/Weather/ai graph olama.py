import ollama
import pandas as pd
from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import List, Dict, Optional

# ✅ AI Model Setup
OLLAMA_MODEL = "llama3.2"


# ✅ Define the State Model
class WeatherState(BaseModel):
    location: str
    sky_condition: str
    rain_condition: str
    wind_condition: str
    free_text_observation: Optional[str] = None
    extracted_weather: Optional[List[str]] = []
    extracted_items: Optional[List[str]] = []
    matched_rule: Optional[str] = None
    final_classification: Optional[str] = None
    recommendation: Optional[str] = None
    ai_powered_recommendations: Optional[str] = None
    ai_explanation: Optional[str] = None
    contradiction_warning: Optional[str] = None


# ✅ AI Agent: Extract Weather Information
def extract_weather_info(state: WeatherState) -> WeatherState:
    """Uses Ollama AI to extract key weather conditions from the free text observation."""
    if not state.free_text_observation:
        return state  # No change if no observation

    prompt = f"Extract key weather conditions from this text: '{state.free_text_observation}'. List only the keywords."
    response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])

    state.extracted_weather = response['message']['content'].split(", ")
    return state


# ✅ AI Agent: Extract Useful Items (e.g., umbrella, coat)
def extract_items(state: WeatherState) -> WeatherState:
    """Identifies items from free-text observations (e.g., umbrella, coat, boots)."""
    if not state.free_text_observation:
        return state  # No change if no observation

    prompt = f"Extract items (e.g., umbrella, coat, boots) from this text: '{state.free_text_observation}'."
    response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])

    state.extracted_items = response['message']['content'].split(", ")
    return state


# ✅ Rule Matching Agent
def match_rules(state: WeatherState) -> WeatherState:
    """Matches observations to predefined weather rules."""
    rules_df = pd.read_excel("rules_multi_factor.xlsx")  # Load rule set

    for _, row in rules_df.iterrows():
        if (
                row["Sky Condition"] == state.sky_condition
                and row["Rain Condition"] == state.rain_condition
                and row["Wind Condition"] == state.wind_condition
        ):
            state.matched_rule = f"{row['Sky Condition']} {row['Rain Condition']} {row['Wind Condition']}"
            state.final_classification = row["Classification"]
            state.recommendation = row["Recommendation"]
            return state

    # If no exact match found, classify as 'Unknown'
    state.matched_rule = "No exact match found"
    state.final_classification = "Unknown"
    state.recommendation = "No specific recommendation"
    return state


# ✅ AI Recommendation Agent
def generate_ai_recommendation(state: WeatherState) -> WeatherState:
    """Uses AI to provide additional recommendations based on extracted insights."""
    prompt = f"""Based on the weather classification '{state.final_classification}', 
    sky: '{state.sky_condition}', rain: '{state.rain_condition}', wind: '{state.wind_condition}', 
    and extracted weather: '{state.extracted_weather}', provide a detailed recommendation including precautions and activity suggestions."""

    response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])

    state.ai_powered_recommendations = response['message']['content']
    return state


# ✅ AI Explanation Agent
def generate_ai_explanation(state: WeatherState) -> WeatherState:
    """Provides AI-powered explanation for the recommendation."""
    prompt = f"""Explain why the recommendation '{state.recommendation}' was given for classification '{state.final_classification}', 
    and how it relates to the extracted weather: '{state.extracted_weather}'."""

    response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])

    state.ai_explanation = response['message']['content']
    return state


# ✅ Contradiction Detector
def detect_contradictions(state: WeatherState) -> WeatherState:
    """Detects logical contradictions in observations (e.g., 'It's sunny but I have an umbrella')."""
    if state.free_text_observation:
        prompt = f"Check if there are contradictions in this weather report: '{state.free_text_observation}'. Provide 'None' if there are no contradictions."
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])

        state.contradiction_warning = response['message']['content']
    return state


# ✅ Final Report Generator
def generate_report(state: WeatherState) -> Dict:
    """Generates a final structured report."""
    return dict(state)


# ✅ LangGraph Workflow Definition
workflow = StateGraph(WeatherState)

# ✅ Define the Nodes
workflow.add_node("extract_weather_info", extract_weather_info)
workflow.add_node("extract_items", extract_items)
workflow.add_node("match_rules", match_rules)
workflow.add_node("generate_ai_recommendation", generate_ai_recommendation)
workflow.add_node("generate_ai_explanation", generate_ai_explanation)
workflow.add_node("detect_contradictions", detect_contradictions)
workflow.add_node("generate_report", generate_report)

# ✅ Define the Workflow Edges
workflow.add_edge("extract_weather_info", "extract_items")
workflow.add_edge("extract_items", "match_rules")
workflow.add_edge("match_rules", "generate_ai_recommendation")
workflow.add_edge("generate_ai_recommendation", "generate_ai_explanation")
workflow.add_edge("generate_ai_explanation", "detect_contradictions")
workflow.add_edge("detect_contradictions", "generate_report")

# ✅ Set the Entry & Exit Points
workflow.set_entry_point("extract_weather_info")
workflow.set_finish_point("generate_report")

# ✅ Compile the Workflow
executor = workflow.compile()

# ✅ Load Observations and Run Pipeline
observations_df = pd.read_excel("observations_free_text.xlsx")  # Load test observations
processed_results = []

for _, row in observations_df.iterrows():
    input_state = WeatherState(
        location=row["Location"],
        sky_condition=row["Sky Condition"],
        rain_condition=row["Rain Condition"],
        wind_condition=row["Wind Condition"],
        free_text_observation=row["Free Text Observation"]
    )

    output = executor.invoke(input_state)
    processed_results.append(output)

# ✅ Convert Processed Results to DataFrame
df_report = pd.DataFrame([dict(result) for result in processed_results])  # 🔥 FIXED!

# ✅ Save Report to Excel
df_report.to_excel("AI_Weather_Report.xlsx", index=False)

print("🚀 AI Weather Report Generated Successfully! Check 'AI_Weather_Report.xlsx' 🎉")
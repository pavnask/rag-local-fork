import re
import ollama
import pandas as pd

# ✅ Load observations from Excel
observations_file = "observations_free_text.xlsx"
df = pd.read_excel(observations_file)

# ✅ Initialize results list
results = []


### 🚀 **Multi-Agent System**
class WeatherClassificationAgent:
    """Classifies weather conditions based on AI processing"""

    @staticmethod
    def classify_weather(sky, rain, wind, free_text):
        prompt = f"""
        Classify the weather conditions and provide recommendations:
        - Sky: {sky}
        - Rain: {rain}
        - Wind: {wind}
        - Observation: {free_text}

        Provide:
        1. Weather Classification
        2. Specific Recommendations
        3. Explanation in simple terms
        """
        response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
        return response.message.content


class RecommendationAgent:
    """Extracts AI-generated recommendations and explanations"""

    @staticmethod
    def extract_details(ai_response_text):
        details = {
            "Final Classification": "",
            "AI-Powered Recommendations": "",
            "AI Explanation": ""
        }

        # 🧩 Extract classification using regex
        classification_match = re.search(r'classify it as "(.*?)"', ai_response_text, re.IGNORECASE)
        if classification_match:
            details["Final Classification"] = classification_match.group(1)

        # 📌 Extract recommendations section (after "Recommendations:")
        recommendation_match = re.search(r'Recommendations:\n\n(.*?)\n\n', ai_response_text, re.DOTALL)
        if recommendation_match:
            details["AI-Powered Recommendations"] = recommendation_match.group(1).strip()

        # 📖 Extract full AI Explanation
        details["AI Explanation"] = ai_response_text.strip()
        return details


class ContradictionDetectionAgent:
    """Identifies contradictions in observations"""

    @staticmethod
    def detect_contradiction(sky, rain, free_text):
        contradictions = []
        if "sun" in free_text.lower() and "rain" in free_text.lower():
            contradictions.append("☀️🌧️ Sun & Rain Contradiction Detected")
        if "umbrella" in free_text.lower() and "dry" in free_text.lower():
            contradictions.append("☂️❌ Umbrella mentioned but 'dry' stated")
        return " | ".join(contradictions) if contradictions else "None"


class ReportGeneratorAgent:
    """Formats structured weather insights for final reporting"""

    @staticmethod
    def generate_report(df):
        report_filename = "ai_weather_multi_agent_report.xlsx"
        df.to_excel(report_filename, index=False)
        print(f"✅ AI-powered multi-agent weather report saved as {report_filename}")


# ✅ Process each observation
for index, row in df.iterrows():
    location = row["Location"]
    sky_condition = row["Sky Condition"]
    rain_condition = row["Rain Condition"]
    wind_condition = row["Wind Condition"]
    free_text_observation = row["Free Text Observation"]

    # 🌦️ **Step 1: Classify Weather**
    ai_response_text = WeatherClassificationAgent.classify_weather(sky_condition, rain_condition, wind_condition,
                                                                   free_text_observation)

    # 🎯 **Step 2: Extract AI Details**
    extracted_data = RecommendationAgent.extract_details(ai_response_text)

    # ⚡ **Step 3: Detect Contradictions**
    contradiction_warning = ContradictionDetectionAgent.detect_contradiction(sky_condition, rain_condition,
                                                                             free_text_observation)

    # 📝 **Step 4: Append data to results list**
    results.append({
        "Location": location,
        "Sky Condition": sky_condition,
        "Rain Condition": rain_condition,
        "Wind Condition": wind_condition,
        "Free-Text Observation": free_text_observation,
        "Final Classification": extracted_data["Final Classification"],
        "AI-Powered Recommendations": extracted_data["AI-Powered Recommendations"],
        "AI Explanation": extracted_data["AI Explanation"],
        "Contradiction Warning": contradiction_warning
    })

# ✅ Convert results to DataFrame
df_report = pd.DataFrame(results)

# 📊 Generate final AI-powered weather report
ReportGeneratorAgent.generate_report(df_report)
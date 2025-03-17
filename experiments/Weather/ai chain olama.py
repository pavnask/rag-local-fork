import re
import pandas as pd
import ollama
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.prompts import PromptTemplate
from langchain.llms import Ollama

# ✅ Load observations from Excel
observations_file = "observations_free_text.xlsx"
df = pd.read_excel(observations_file)

# ✅ Initialize Ollama Model
llm = Ollama(model="llama3.2")

### 🚀 **Define LangChain Agents as Chains**

# 🎯 **Weather Classification Chain**
classification_prompt = PromptTemplate(
    input_variables=["sky", "rain", "wind", "observation"],
    template="""
    Classify the weather conditions:
    - Sky: {sky}
    - Rain: {rain}
    - Wind: {wind}
    - Observation: {observation}

    Provide:
    1. Weather Classification
    2. Specific Recommendations
    3. Explanation in simple terms
    """
)
weather_classification_chain = LLMChain(llm=llm, prompt=classification_prompt)

# 🎯 **Contradiction Detection Chain**
contradiction_prompt = PromptTemplate(
    input_variables=["sky", "rain", "observation"],
    template="""
    Analyze the given weather observation and check for contradictions:
    - Sky Condition: {sky}
    - Rain Condition: {rain}
    - Free-Text Observation: {observation}

    Identify if there are inconsistencies (e.g., mentions of 'sun' while also reporting 'rain').
    """
)
contradiction_chain = LLMChain(llm=llm, prompt=contradiction_prompt)

# 🎯 **Chain Sequence (Classification → Contradiction)**
weather_analysis_chain = SimpleSequentialChain(
    chains=[weather_classification_chain, contradiction_chain],
    input_key="weather_data"
)

### 🚀 **Process Each Weather Observation**
results = []

for _, row in df.iterrows():
    location = row["Location"]
    sky_condition = row["Sky Condition"]
    rain_condition = row["Rain Condition"]
    wind_condition = row["Wind Condition"]
    free_text_observation = row["Free Text Observation"]

    # 🔄 **Step 1: Classify Weather via Chain**
    weather_input = {
        "sky": sky_condition,
        "rain": rain_condition,
        "wind": wind_condition,
        "observation": free_text_observation
    }
    ai_response_text = weather_classification_chain.run(weather_input)

    # 🎯 **Step 2: Extract AI Details**
    details = {
        "Final Classification": "",
        "AI-Powered Recommendations": "",
        "AI Explanation": ""
    }

    classification_match = re.search(r'classify it as "(.*?)"', ai_response_text, re.IGNORECASE)
    if classification_match:
        details["Final Classification"] = classification_match.group(1)

    recommendation_match = re.search(r'Recommendations:\n\n(.*?)\n\n', ai_response_text, re.DOTALL)
    if recommendation_match:
        details["AI-Powered Recommendations"] = recommendation_match.group(1).strip()

    details["AI Explanation"] = ai_response_text.strip()

    # ⚡ **Step 3: Detect Contradictions via Chain**
    contradiction_warning = contradiction_chain.run({
        "sky": sky_condition,
        "rain": rain_condition,
        "observation": free_text_observation
    }).strip()

    # 📝 **Step 4: Append Data to Results**
    results.append({
        "Location": location,
        "Sky Condition": sky_condition,
        "Rain Condition": rain_condition,
        "Wind Condition": wind_condition,
        "Free-Text Observation": free_text_observation,
        "Final Classification": details["Final Classification"],
        "AI-Powered Recommendations": details["AI-Powered Recommendations"],
        "AI Explanation": details["AI Explanation"],
        "Contradiction Warning": contradiction_warning
    })

# ✅ Convert results to DataFrame
df_report = pd.DataFrame(results)

# 📊 **Export AI Weather Analysis Report**
report_filename = "ai_weather_chain_report.xlsx"
df_report.to_excel(report_filename, index=False)
print(f"✅ AI-powered weather report saved as {report_filename}")
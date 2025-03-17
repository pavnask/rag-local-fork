import re
import ollama

# 🛠 Query Llama 3.2
prompt = "Classify the weather: Gray sky, Drizzle, Calm wind. Provide recommendations and explanation."
response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])

# Extract AI message content
ai_response_text = response.message.content

# ✅ Initialize empty dictionary for data
data = {
    "Final Classification": "",
    "AI-Powered Recommendations": "",
    "AI Explanation": ""
}

# 🛠 Debugging: Print AI's full response
print("🧠 Extracted AI Text:\n", ai_response_text)

# 🧩 Extract classification using pattern matching
classification_match = re.search(r'classify it as "(.*?)"', ai_response_text, re.IGNORECASE)
if classification_match:
    data["Final Classification"] = classification_match.group(1)

# 📌 Extract recommendations section (after "Recommendations:")
recommendation_match = re.search(r'Recommendations:\n\n(.*?)\n\n', ai_response_text, re.DOTALL)
if recommendation_match:
    data["AI-Powered Recommendations"] = recommendation_match.group(1).strip()

# 📖 Extract full AI Explanation (rest of the content)
data["AI Explanation"] = ai_response_text.strip()

# 🔍 Debugging: Print extracted data
print("🔍 Final Classification:", data["Final Classification"])
print("🎯 AI-Powered Recommendations:", data["AI-Powered Recommendations"])
print("📖 AI Explanation:", data["AI Explanation"])
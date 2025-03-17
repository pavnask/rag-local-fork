import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import process
import ollama
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


# Process structured observations based on direct mapping with fuzzy matching
def classify_structured_observation(row):
    best_match, score = process.extractOne(row["Metric"], df_rules["Condition"].tolist())

    if score > 75:  # Fuzzy match threshold adjusted
        matched_rule = df_rules[df_rules["Condition"] == best_match]
        return matched_rule["Action"].values[0] if not matched_rule.empty else "No Strong Match Found"

    return "No Strong Match Found"


df_observations_with_entities["Suggested_Action"] = df_observations_with_entities.apply(classify_structured_observation,
                                                                                        axis=1)

# Combine results for reporting
df_results = pd.concat([
    df_observations_free_text[['Observation_ID', 'Observation_Text', 'OLLAMA_Suggestion']].rename(
        columns={'Observation_Text': 'Description'}),
    df_observations_with_entities[['Observation_ID', 'Entity', 'Metric', 'Value', 'Suggested_Action']].rename(
        columns={'Entity': 'Description'})
])

# Generate classification summary
classification_counts = df_results['OLLAMA_Suggestion'].value_counts()

# Display colorful summary table in console
table = Table(title="IT Systems TIME Classification Summary")
table.add_column("Category", style="bold blue")
table.add_column("Count", style="bold yellow")
for category, count in classification_counts.items():
    table.add_row(category, str(count))
console.print(table)

# Generate Markdown report
md_report = "# IT Systems TIME Classification Report\n\n"
md_report += "## Summary\n\n"
md_report += "| Category | Count |\n|----------|-------|\n"
for category, count in classification_counts.items():
    md_report += f"| {category} | {count} |\n"

md_report += "\n## Detailed Observations\n\n"
md_report += df_results.to_markdown(index=False)

# Save Markdown file
md_report_file = "IT_Systems_TIME_Report.md"
with open(md_report_file, "w", encoding="utf-8") as f:
    f.write(md_report)

# Save Excel report
report_file = "IT_Systems_TIME_Report.xlsx"
with pd.ExcelWriter(report_file, engine='xlsxwriter') as writer:
    df_results.to_excel(writer, sheet_name="TIME Classification", index=False)
    workbook = writer.book
    worksheet = writer.sheets["TIME Classification"]

    # Insert classification chart into Excel
    chart = workbook.add_chart({'type': 'pie'})
    chart.add_series({
        'categories': ['TIME Classification', 1, 2, len(classification_counts), 2],
        'values': ['TIME Classification', 1, 3, len(classification_counts), 3],
        'data_labels': {'percentage': True},
    })
    chart.set_title({'name': 'IT System Classification Distribution'})
    worksheet.insert_chart('F2', chart)

print(
    "\nProcessing completed! TIME classifications applied with OLLAMA insights. Reports generated in Excel and Markdown.")

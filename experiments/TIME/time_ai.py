import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import process
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


def keyword_match(observation_text):
    """Simple keyword-based matching to improve classification accuracy."""
    keywords = {
        "performance": "Migrate",
        "security": "Eliminate",
        "legacy": "Eliminate",
        "stable": "Tolerate",
        "high cost": "Migrate"
    }
    for keyword, action in keywords.items():
        if keyword in observation_text.lower():
            return action
    return None


def classify_free_text_observation(observation_text):
    obs_embedding = embed_text(observation_text)
    best_match = None
    best_score = 0
    threshold = 0.3  # Lowered threshold for better classification

    for _, row in df_rules.iterrows():
        score = util.pytorch_cos_sim(obs_embedding, row["Condition_Embedding"]).item()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = row["Action"]

    # Use keyword matching if SBERT confidence is low
    if not best_match or best_score < 0.35:
        best_match = keyword_match(observation_text)

    return best_match if best_match else "No Strong Match Found"


# Process free-text observations
df_observations_free_text["Suggested_Action"] = df_observations_free_text["Observation_Text"].apply(
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
    df_observations_free_text[['Observation_ID', 'Observation_Text', 'Suggested_Action']].rename(
        columns={'Observation_Text': 'Description'}),
    df_observations_with_entities[['Observation_ID', 'Entity', 'Metric', 'Value', 'Suggested_Action']].rename(
        columns={'Entity': 'Description'})
])

# Generate classification summary
classification_counts = df_results['Suggested_Action'].value_counts()

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

print("\nProcessing completed! TIME classifications applied. Reports generated in Excel and Markdown.")

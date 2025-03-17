import pandas as pd
import matplotlib.pyplot as plt

# Load the AI-generated weather report
df_report = pd.read_excel("final_ai_weather_report_ollama.xlsx")


# === 📊 Generate Weather Trends ===
def generate_weather_trends(df):
    """Creates trend analysis visualizations for weather conditions."""

    # Convert categorical weather conditions into numerical counts per location
    trend_data = df.groupby("Location")[["Sky Condition", "Rain Condition", "Wind Condition"]].agg(
        lambda x: x.mode()[0])

    # Count occurrences of each condition type
    condition_counts = df.groupby(["Location", "Sky Condition"]).size().unstack(fill_value=0)

    # Plot bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    condition_counts.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")

    plt.title("🌍 Most Frequent Sky Conditions by Location")
    plt.xlabel("Location")
    plt.ylabel("Number of Occurrences")
    plt.xticks(rotation=45)
    plt.legend(title="Sky Condition")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Save chart as image
    plt.savefig("weather_trends.png")
    plt.show()

    print("✅ Weather trend chart saved as weather_trends.png")


# === 📄 Generate HTML Report with Charts ===
def generate_html_report(df):
    """Generates an enhanced HTML report with trends and visualizations."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Weather Report</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body { padding: 20px; }
            .good { color: green; font-weight: bold; }
            .bad { color: red; font-weight: bold; }
            .neutral { color: gray; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; border: 1px solid #ddd; }
            th { background-color: #f4f4f4; }
            img { max-width: 100%; }
        </style>
    </head>
    <body>
        <h1 class="text-center">🌤 AI Weather Analysis Report</h1>
        <h2 class="text-center">📊 Weather Trends</h2>
        <img src="weather_trends.png" alt="Weather Trends" class="img-fluid">
        <br><br>
        <h2 class="text-center">📍 Detailed Weather Data</h2>
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>📍 Location</th>
                    <th>🌦 Weather</th>
                    <th>📝 Observation</th>
                    <th>📢 AI Suggestion</th>
                    <th>🏷️ Classification</th>
                </tr>
            </thead>
            <tbody>
    """

    for _, row in df.iterrows():
        classification = row["Final Classification"]
        color_class = "good" if classification == "Good" else "bad"

        html_content += f"""
        <tr>
            <td>{row['Location']}</td>
            <td>{row['Sky Condition']}, {row['Rain Condition']}, {row['Wind Condition']}</td>
            <td>{row['Free-Text Observation']}</td>
            <td>{row['AI-Powered Recommendations']}</td>
            <td class="{color_class}">{classification}</td>
        </tr>
        """

    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ HTML report with trends generated: report.html")


# === RUN REPORT GENERATORS ===
generate_weather_trends(df_report)
generate_html_report(df_report)
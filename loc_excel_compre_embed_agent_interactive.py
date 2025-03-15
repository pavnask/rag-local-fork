import re
from sentence_transformers import SentenceTransformer, util
import pandas as pd

import torch

def cosine_similarity(embedding1, embedding2):
    """Computes cosine similarity using PyTorch."""
    return torch.nn.functional.cosine_similarity(embedding1, embedding2, dim=0)

class EmbeddingAgent:
    def __init__(self, model_name, file_name='default_file.xlsx', sheet_name='Sheet1'):
        #self.model = SentenceTransformer(model_name)
        self.model = SentenceTransformer("./models/all-MiniLM-L6-v2")  # Load from local directory
        self.file_name = file_name
        self.sheet_name = sheet_name

        self.df = None
        self.descriptions = []

    def ask_for_file(self):
        # Ask for file and sheet name if not already provided
        modify_file = input(
            f"Do you want to modify the default file name '{self.file_name}'? (yes/no): ").strip().lower()
        if modify_file == 'yes':
            self.file_name = input("Enter the new file name: ").strip()

        modify_sheet = input(
            f"Do you want to modify the default sheet name '{self.sheet_name}'? (yes/no): ").strip().lower()
        if modify_sheet == 'yes':
            self.sheet_name = input("Enter the new sheet name: ").strip()

        # Load the data
        self.df = pd.read_excel(self.file_name, sheet_name=self.sheet_name, dtype=str).dropna()
        # Concatenate all columns into a single string per row
        self.df['combined'] = self.df.astype(str).agg(' '.join, axis=1)
        self.descriptions = self.df['combined'].tolist()

    def encode(self):
        return self.model.encode(self.descriptions, convert_to_tensor=True)

    def extract_keys(self, text):
        # Regular expression to find patterns like TACIR_1-Ч03.01.1-01
        key_pattern = r'\bTACIR_\d+-.+?\b'
        return re.findall(key_pattern, text)

    def remove_keys(self, text):
        # Remove keys (e.g., TACIR_1-Ч03.01.1-01) from the text for similarity comparison
        key_pattern = r'\bTACIR_\d+-.+?\b'
        return re.sub(key_pattern, '', text)


class SemanticMatcher:
    def __init__(self, agent1, agent2, threshold=0.8):
        self.agent1 = agent1  # Embedding agent for file1
        self.agent2 = agent2  # Embedding agent for file2
        self.threshold = threshold

    def find_semantic_matches(self):
        # Each agent asks for its file and sheet name
        print("\n[Agent 1]")
        self.agent1.ask_for_file()
        print("\n[Agent 2]")
        self.agent2.ask_for_file()

        # Preprocess descriptions to remove keys and extract them separately
        processed_descriptions1 = [self.agent1.remove_keys(description) for description in self.agent1.descriptions]
        processed_descriptions2 = [self.agent2.remove_keys(description) for description in self.agent2.descriptions]

        # Encode descriptions with different agents (after removing keys)
        embeddings1 = self.agent1.encode()
        embeddings2 = self.agent2.encode()

        # Compute cosine similarity
        #similarity_scores = util.cos_sim(embeddings1, embeddings2)
        #similarity_scores = cosine_similarity(embeddings1, embeddings2)
        # Compute cosine similarity using PyTorch
        similarity_scores = cosine_similarity(embeddings1, embeddings2)

        # Ensure similarity_scores is a 1D tensor (not a single value)
        # Compute cosine similarity

        print(f"Shape of embeddings1: {embeddings1.shape}")
        print(f"Shape of embeddings2: {embeddings2.shape}")
        print(f"Shape of similarity_scores: {similarity_scores.shape}")
        print(f"Length of descriptions1: {len(self.agent1.descriptions)}")
        print(f"Length of descriptions2: {len(self.agent2.descriptions)}")

        similarity_scores = cosine_similarity(embeddings1, embeddings2.unsqueeze(0))  # Ensure correct shape

        # Find matches above threshold
        matches = []
        for i in range(similarity_scores.shape[0]):  # ✅ Iterate over rows
            for j in range(similarity_scores.shape[1]):  # ✅ Iterate over columns
                score = similarity_scores[i, j].item()  # ✅ Extract actual value
                if score >= self.threshold:
                    description1 = self.agent1.descriptions[i]  # ✅ Use correct index
                    description2 = self.agent2.descriptions[j]  # ✅ Use correct index
                    matches.append((description1, description2, score))

        # Find matches above threshold
        matches = []
        report_lines = []
        report_lines.append("Semantic Matching Analysis Report\n")
        report_lines.append("====================================\n")

        match_found = False
        for i, row in enumerate(similarity_scores):
            for j, score in enumerate(row):
                if score.item() >= self.threshold:
                    description1 = self.agent1.descriptions[i]
                    description2 = self.agent2.descriptions[j]
                    # Extract keys for both descriptions
                    keys1 = self.agent1.extract_keys(description1)
                    keys2 = self.agent2.extract_keys(description2)
                    differences = set(description1.split()) ^ set(description2.split())
                    explanation = self.generate_human_readable_explanation(description1, description2, keys1, keys2,
                                                                           score.item(), differences)
                    matches.append((description1, description2, score.item(), explanation))
                    report_lines.append(explanation)
                    match_found = True

        # If no matches found, indicate that
        if not match_found:
            report_lines.append("No matches found above the threshold.")

        # Convert to DataFrame and save
        matches_df = pd.DataFrame(matches, columns=['File1_Row', 'File2_Row', 'Similarity', 'Explanation'])
        matches_df.to_excel('semantic_matches_with_keys_and_report.xlsx', index=False)

        # Print formatted report
        print("\n".join(report_lines))

        print("Matching completed. Results saved to 'semantic_matches_with_keys_and_report.xlsx'")
        return matches_df

    def generate_human_readable_explanation(self, description1, description2, keys1, keys2, score, differences):
        # Create a human-readable explanation, including the keys
        explanation = (
            f"Match Found (Similarity: {score:.2f})\n"
            f"File 1: {description1}\n"
            f"File 2: {description2}\n"
            f"Differences: {', '.join(differences)}\n\n"
            f"Keys Found in File 1: {', '.join(keys1)}\n"
            f"Keys Found in File 2: {', '.join(keys2)}\n\n"
            "Explanation: The descriptions from both files match with a high similarity score.\n"
            f"Key differences in wording or details are highlighted above.\n"
            "This suggests that these entries may be related but contain slight differences in phrasing."
        )
        return explanation


# Example usage:
# Initialize agents with different embedding models
agent1 = EmbeddingAgent('all-MiniLM-L6-v2', 'Таблица_оценочного_балла.xlsx', 'Sheet1')  # Agent for file1
agent2 = EmbeddingAgent('all-MiniLM-L6-v2', 'Таблица_оценочного_балла2.xlsx', 'Sheet1')  # Agent for file2

# Initialize the matcher with the two agents
matcher = SemanticMatcher(agent1, agent2, threshold=0.8)

# Run the matching process
matcher.find_semantic_matches()
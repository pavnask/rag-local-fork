from sentence_transformers import SentenceTransformer

# Define the local path to save the model
model_path = "./models/all-MiniLM-L6-v2"

# Download and save the model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model.save(model_path)

print(f"✅ Model saved locally at {model_path}")
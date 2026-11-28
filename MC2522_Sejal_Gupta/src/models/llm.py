from transformers import pipeline

print("Loading FLAN-T5 model...")

generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

print("FLAN-T5 Loaded Successfully!")

def load_llm():
    return generator
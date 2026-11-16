from transformers import pipeline

print("Loading AI model... (This may take a few minutes the first time)")

pipe = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-1.5B-Instruct"
)

print("Model loaded successfully!")

response = pipe(
    "Hello! Introduce yourself in one sentence.",
    max_new_tokens=50
)

print("\nAI Response:\n")
print(response[0]["generated_text"])
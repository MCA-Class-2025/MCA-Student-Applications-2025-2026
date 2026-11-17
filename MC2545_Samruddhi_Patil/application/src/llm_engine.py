"""
MovieMind AI
LLM Recommendation Engine
"""

from transformers import pipeline

print("=" * 60)
print("Loading FLAN-T5 Model...")
print("=" * 60)

generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

print("Model Loaded Successfully!")

while True:

    prompt = input("\nAsk something (type 'exit' to quit): ")

    if prompt.lower() == "exit":
        break

    response = generator(
        prompt,
        max_new_tokens=140,
    min_new_tokens=10,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
    repetition_penalty=1.8,
    no_repeat_ngram_size=2,

    )

    print("\nAI Response:\n")

    print(response[0]["generated_text"])
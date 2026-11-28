from services.llm_service import generate_response


prompt = """
You are an AI travel planner.

Create a simple 3-day travel itinerary
for London, United Kingdom.

Keep it concise and beginner-friendly.
"""


result = generate_response(prompt)

print("\n================================")
print("LLM RESPONSE")
print("================================")

print(result)
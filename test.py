from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list()

    print("Available Models:\n")

    for model in models.data:
        print(model.id)

except Exception as e:
    print("Error:", e)
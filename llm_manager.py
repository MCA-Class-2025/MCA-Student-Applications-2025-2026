import os
from dotenv import load_dotenv

load_dotenv()


# ==========================================================
# GROQ
# ==========================================================

def generate_groq(prompt):
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Groq API key is missing."

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert AI interior designer. "
                    "Give practical, creative and budget-conscious "
                    "interior design recommendations."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=2000
    )

    return response.choices[0].message.content


# ==========================================================
# GEMINI
# ==========================================================

def generate_gemini(prompt):
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "Gemini API key is missing."

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-2.0-flash")

    response = model.generate_content(prompt)

    return response.text


# ==========================================================
# OPENAI
# ==========================================================

def generate_openai(prompt):
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "OpenAI API key is missing."

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert interior designer. "
                    "Create practical and attractive interior "
                    "design recommendations."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


# ==========================================================
# CLAUDE
# ==========================================================

def generate_claude(prompt):
    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return "Anthropic API key is missing."

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=2000,
        temperature=0.7,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are an expert interior designer. "
                    "Provide detailed and practical recommendations.\n\n"
                    + prompt
                )
            }
        ]
    )

    return response.content[0].text


# ==========================================================
# HUGGING FACE
# ==========================================================

def generate_huggingface(prompt):
    from huggingface_hub import InferenceClient

    api_key = os.getenv("HF_TOKEN")

    if not api_key:
        return "Hugging Face token is missing."

    client = InferenceClient(
        api_key=api_key
    )

    response = client.chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert AI interior designer. "
                    "Give useful interior design recommendations."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="meta-llama/Llama-3.1-8B-Instruct",
        max_tokens=2000
    )

    return response.choices[0].message.content


# ==========================================================
# MAIN LLM FUNCTION
# ==========================================================

def generate_design(prompt, provider):

    provider = provider.lower()

    try:

        if provider == "groq":
            return generate_groq(prompt)

        elif provider == "gemini":
            return generate_gemini(prompt)

        elif provider == "openai":
            return generate_openai(prompt)

        elif provider == "claude":
            return generate_claude(prompt)

        elif provider == "hugging face":
            return generate_huggingface(prompt)

        else:
            return "Invalid AI provider selected."

    except Exception as e:

        return f"{provider.title()} Error: {str(e)}"
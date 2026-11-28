import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_response(comment, similar_comments=""):
    prompt = f"""
You are an AI Social Media Moderator.

Analyze this comment:

{comment}

Similar examples:
{similar_comments}

Return:
1. Toxic or Not Toxic
2. Category (Insult, Hate Speech, Threat, etc.)
3. Explanation
4. Suggested Polite Version
"""

    response = model.generate_content(prompt)

    return response.text
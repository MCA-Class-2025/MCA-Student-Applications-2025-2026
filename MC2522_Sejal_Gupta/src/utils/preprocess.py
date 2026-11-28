import re
import emoji
from bs4 import BeautifulSoup


def preprocess_text(text):

    if not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Remove HTML
    text = BeautifulSoup(text, "html.parser").get_text()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove emojis
    text = emoji.replace_emoji(text, replace="")

    # Remove punctuation and numbers
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text
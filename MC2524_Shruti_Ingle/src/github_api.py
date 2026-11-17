import os
import requests
import pandas as pd
from dotenv import load_dotenv
from langchain.schema import Document

load_dotenv()

# Your GitHub username from .env
USERNAME = os.getenv("GITHUB_USERNAME")


def export_github_dataset():
    """
    Export GitHub repositories into a CSV dataset.
    """

    url = f"https://api.github.com/users/{USERNAME}/repos"

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.status_code} - {response.text}")

    repos = response.json()

    data = []

    for repo in repos:
        data.append({
            "repo_name": repo.get("name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count"),
            "forks": repo.get("forks_count"),
            "updated_at": repo.get("updated_at"),
            "url": repo.get("html_url")
        })

    os.makedirs("datasets", exist_ok=True)

    df = pd.DataFrame(data)

    df.to_csv("datasets/github_dataset.csv", index=False)

    print("GitHub dataset saved successfully.")

    return data


def load_github_documents():
    """
    Load GitHub CSV as LangChain documents.
    """

    df = pd.read_csv("datasets/github_dataset.csv")

    documents = []

    for _, row in df.iterrows():
        text = (
            f"GitHub Repository\n"
            f"Repository: {row.get('repo_name', '')}\n"
            f"Description: {row.get('description', '')}\n"
            f"Language: {row.get('language', '')}\n"
            f"Stars: {row.get('stars', '')}\n"
            f"Forks: {row.get('forks', '')}\n"
            f"Updated: {row.get('updated_at', '')}\n"
            f"URL: {row.get('url', '')}"
        )

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source_file": row.get("repo_name", "GitHub"),
                    "source": "GitHub"
                }
            )
        )

    return documents


if __name__ == "__main__":
    repos = export_github_dataset()

    print("\nRepositories Found:\n")

    for repo in repos:
        print(repo["repo_name"])
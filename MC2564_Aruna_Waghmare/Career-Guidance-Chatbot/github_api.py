import requests


GITHUB_API_URL = "https://api.github.com"


def get_github_profile(username):

    url = f"{GITHUB_API_URL}/users/{username}"

    response = requests.get(url, timeout=10)

    if response.status_code == 404:
        return {
            "success": False,
            "message": "GitHub user not found."
        }

    if response.status_code != 200:
        return {
            "success": False,
            "message": f"GitHub API error: {response.status_code}"
        }

    data = response.json()

    return {
        "success": True,
        "username": data.get("login"),
        "name": data.get("name"),
        "bio": data.get("bio"),
        "followers": data.get("followers", 0),
        "following": data.get("following", 0),
        "repositories": data.get("public_repos", 0),
        "created_at": data.get("created_at"),
        "location": data.get("location"),
        "profile_url": data.get("html_url"),
        "avatar": data.get("avatar_url")
    }


def get_github_repositories(username):

    url = f"{GITHUB_API_URL}/users/{username}/repos"

    params = {
        "per_page": 100,
        "sort": "updated"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        return []

    repositories = response.json()

    repo_list = []

    for repo in repositories:

        repo_list.append({
            "name": repo.get("name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "url": repo.get("html_url")
        })

    return repo_list
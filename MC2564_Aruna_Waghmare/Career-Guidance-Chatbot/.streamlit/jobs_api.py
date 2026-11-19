import requests


JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"


def search_jobs(query, location, api_key, max_results=10):

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    params = {
        "query": f"{query} in {location}",
        "page": "1",
        "num_pages": "1"
    }

    try:

        response = requests.get(
            JSEARCH_URL,
            headers=headers,
            params=params,
            timeout=15
        )

        if response.status_code == 401:

            return {
                "success": False,
                "message": "Invalid RapidAPI key.",
                "jobs": []
            }

        if response.status_code == 403:

            return {
                "success": False,
                "message": "JSearch API access is not available for this key.",
                "jobs": []
            }

        if response.status_code == 429:

            return {
                "success": False,
                "message": "JSearch API quota exceeded.",
                "jobs": []
            }

        if response.status_code != 200:

            return {
                "success": False,
                "message": f"JSearch API error: {response.status_code}",
                "jobs": []
            }

        data = response.json()

        jobs = []

        for job in data.get("data", [])[:max_results]:

            jobs.append({

                "title": job.get(
                    "job_title",
                    "Unknown"
                ),

                "company": job.get(
                    "employer_name",
                    "Unknown Company"
                ),

                "location": job.get(
                    "job_location",
                    "Unknown Location"
                ),

                "type": job.get(
                    "job_employment_type",
                    "Not specified"
                ),

                "description": job.get(
                    "job_description",
                    "No description available."
                ),

                "apply_link": job.get(
                    "job_apply_link",
                    ""
                ),

                "remote": job.get(
                    "job_is_remote",
                    False
                )
            })

        return {
            "success": True,
            "message": "Jobs found successfully.",
            "jobs": jobs
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "message": str(e),
            "jobs": []
        }
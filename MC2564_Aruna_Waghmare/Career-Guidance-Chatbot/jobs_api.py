import requests
import re

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


def search_jobs(query="", max_results=10):

    try:

        response = requests.get(
            REMOTIVE_URL,
            params={
                "search": query
            },
            timeout=15
        )

        if response.status_code != 200:

            return {
                "success": False,
                "message": f"Remotive API error: {response.status_code}",
                "jobs": []
            }

        data = response.json()

        all_jobs = data.get("jobs", [])

        query_words = [
            word.lower()
            for word in re.findall(
                r"\b\w+\b",
                query
            )
            if len(word) > 2
        ]

        matched_jobs = []

        for job in all_jobs:

            title = job.get(
                "title",
                ""
            ).lower()

            description = job.get(
                "description",
                ""
            ).lower()

            category = job.get(
                "category",
                ""
            ).lower()

            company = job.get(
                "company_name",
                ""
            ).lower()

            # Combine job information
            searchable_text = (
                title
                + " "
                + description
                + " "
                + category
                + " "
                + company
            )

            # Count matching keywords
            match_count = sum(
                1
                for word in query_words
                if word in searchable_text
            )

            if match_count > 0:

                description_clean = re.sub(
                    r"<.*?>",
                    " ",
                    job.get(
                        "description",
                        ""
                    )
                )

                matched_jobs.append({

                    "title": job.get(
                        "title",
                        "Unknown Job"
                    ),

                    "company": job.get(
                        "company_name",
                        "Unknown Company"
                    ),

                    "location": job.get(
                        "candidate_required_location",
                        "Remote"
                    ),

                    "type": job.get(
                        "job_type",
                        "Not specified"
                    ),

                    "description": description_clean,

                    "apply_link": job.get(
                        "url",
                        ""
                    ),

                    "category": job.get(
                        "category",
                        "IT"
                    ),

                    "published": job.get(
                        "publication_date",
                        ""
                    ),

                    "match_score": match_count
                })

        # Sort by relevance
        matched_jobs.sort(
            key=lambda x: x["match_score"],
            reverse=True
        )

        return {

            "success": True,

            "message": "Jobs found successfully.",

            "jobs": matched_jobs[:max_results]

        }

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "message": str(e),

            "jobs": []

        }
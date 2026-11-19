import requests


OPENALEX_URL = "https://api.openalex.org/works"


def search_research(topic, max_results=10):

    try:

        params = {
            "search": topic,
            "per-page": max_results,
            "sort": "relevance_score:desc"
        }

        response = requests.get(
            OPENALEX_URL,
            params=params,
            timeout=15
        )

        if response.status_code != 200:

            return {
                "success": False,
                "message": f"OpenAlex API Error: {response.status_code}",
                "papers": []
            }

        data = response.json()

        papers = []

        for work in data.get("results", []):

            # --------------------------------
            # TITLE
            # --------------------------------

            title = work.get(
                "display_name",
                "Untitled Research Paper"
            )

            # --------------------------------
            # AUTHORS
            # --------------------------------

            authors = []

            for author in work.get(
                "authorships",
                []
            ):

                author_name = author.get(
                    "author",
                    {}
                ).get(
                    "display_name"
                )

                if author_name:

                    authors.append(
                        author_name
                    )

            # --------------------------------
            # YEAR
            # --------------------------------

            year = work.get(
                "publication_year",
                "N/A"
            )

            # --------------------------------
            # CITATIONS
            # --------------------------------

            citations = work.get(
                "cited_by_count",
                0
            )

            # --------------------------------
            # DOI
            # --------------------------------

            doi = work.get(
                "doi"
            )

            # --------------------------------
            # URL
            # --------------------------------

            url = work.get(
                "primary_location",
                {}
            )

            if url:

                url = url.get(
                    "landing_page_url"
                )

            # --------------------------------
            # ABSTRACT
            # --------------------------------

            abstract = ""

            inverted_index = work.get(
                "abstract_inverted_index"
            )

            if inverted_index:

                words = []

                for word, positions in inverted_index.items():

                    for position in positions:

                        words.append(
                            (position, word)
                        )

                words.sort()

                abstract = " ".join(
                    word
                    for position, word
                    in words
                )

            if not abstract:

                abstract = (
                    "Abstract not available."
                )

            papers.append({

                "title": title,

                "authors": (
                    ", ".join(authors[:5])
                    if authors
                    else "Unknown"
                ),

                "year": year,

                "citations": citations,

                "doi": doi
                if doi
                else "Not available",

                "url": url
                if url
                else "",

                "abstract": abstract

            })

        return {

            "success": True,

            "message": (
                f"Found {len(papers)} "
                f"research papers."
            ),

            "papers": papers

        }

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "message": str(e),

            "papers": []

        }
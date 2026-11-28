import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

OPENALEX_BASE_URL = "https://api.openalex.org"

CSV_FILE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "datasets",
        "research_project_advisor.csv"
    )
)


# ============================================================
# CSV SETUP
# ============================================================

def ensure_csv():
    """
    Check whether the Research Project Advisor CSV already exists.

    If it exists:
        Keep the existing file and append new records to it.

    If it does not exist:
        Create the file inside the datasets folder with
        the required CSV columns.
    """

    os.makedirs(
        os.path.dirname(CSV_FILE),
        exist_ok=True
    )

    if not os.path.exists(CSV_FILE):

        with open(
            CSV_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "programming_languages",
                "research_field",
                "domain",
                "experience_level",
                "query",
                "title",
                "doi",
                "eid",
                "authors",
                "publication_name",
                "publication_date",
                "abstract",
                "cited_by_count",
                "document_type"
            ])


# ============================================================
# CSV STORAGE
# ============================================================

def save_advisor_result(
    languages,
    field,
    domain,
    interests,
    methodology,
    experience_level,
    query,
    selected_topic,
    supporting_works,
    total_results
):
    """
    Save the Research Project Advisor response
    as dataset records.

    If the CSV does not exist, it is created first.

    If the CSV already exists, new records are appended.

    Each supporting OpenAlex paper becomes a separate
    dataset record.
    """

    ensure_csv()

    if isinstance(languages, list):

        programming_languages = ", ".join(
            str(item).strip()
            for item in languages
            if item and str(item).strip()
        )

    else:

        programming_languages = str(
            languages or ""
        ).strip()

    field = str(
        field or ""
    ).strip()

    domain = str(
        domain or ""
    ).strip()

    interests = str(
        interests or ""
    ).strip()

    methodology = str(
        methodology or ""
    ).strip()

    experience_level = str(
        experience_level or ""
    ).strip()

    query = str(
        query or ""
    ).strip()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        # ----------------------------------------------------
        # STORE SUPPORTING OPENALEX PAPERS
        # ----------------------------------------------------

        if supporting_works:

            for work in supporting_works:

                authors = work.get(
                    "authors",
                    []
                )

                if isinstance(authors, list):

                    authors_value = ", ".join(
                        str(author).strip()
                        for author in authors
                        if author and str(author).strip()
                    )

                else:

                    authors_value = str(
                        authors or ""
                    ).strip()

                # ------------------------------------------------
                # IMPORTANT:
                # The CSV contains exactly 15 columns.
                # Therefore this row must also contain exactly
                # 15 values.
                # ------------------------------------------------

                writer.writerow([
                    timestamp,
                    programming_languages,
                    field,
                    domain,
                    experience_level,
                    query,
                    work.get(
                        "title",
                        ""
                    ),
                    work.get(
                        "doi",
                        ""
                    ),
                    work.get(
                        "eid",
                        ""
                    ),
                    authors_value,
                    work.get(
                        "publication_name",
                        ""
                    ),
                    work.get(
                        "publication_date",
                        ""
                    ),
                    work.get(
                        "abstract",
                        ""
                    ),
                    work.get(
                        "cited_by_count",
                        0
                    ),
                    work.get(
                        "document_type",
                        ""
                    )
                ])

        # ----------------------------------------------------
        # STORE ADVISOR REQUEST EVEN IF NO PAPERS ARE RETURNED
        # ----------------------------------------------------

        else:

            writer.writerow([
                timestamp,
                programming_languages,
                field,
                domain,
                experience_level,
                query,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                0,
                ""
            ])

    return True


# ============================================================
# OPENALEX REQUEST
# ============================================================

def search_openalex(
    search_query,
    limit=10
):
    """
    Search OpenAlex for scholarly works.
    """

    if not search_query:

        return {
            "success": False,
            "error": "OpenAlex search query is required.",
            "results": []
        }

    url = f"{OPENALEX_BASE_URL}/works"

    params = {
        "search": search_query,
        "per-page": limit,
        "sort": "cited_by_count:desc"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "results": data.get(
                "results",
                []
            ),
            "meta": data.get(
                "meta",
                {}
            )
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "OpenAlex request timed out.",
            "results": []
        }

    except requests.exceptions.HTTPError as e:

        return {
            "success": False,
            "error": (
                f"OpenAlex HTTP error: {str(e)}"
            ),
            "results": []
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": (
                f"OpenAlex request failed: {str(e)}"
            ),
            "results": []
        }

    except Exception as e:

        return {
            "success": False,
            "error": (
                f"Unexpected OpenAlex error: {str(e)}"
            ),
            "results": []
        }


# ============================================================
# FORMAT OPENALEX WORK
# ============================================================

def format_work(work):
    """
    Convert an OpenAlex work into a clean
    ResearchIQ format.
    """

    authors = []

    for authorship in work.get(
        "authorships",
        []
    ):

        author = authorship.get(
            "author",
            {}
        )

        name = author.get(
            "display_name",
            ""
        )

        if name:

            authors.append(name)

    topics = []

    for topic in work.get(
        "topics",
        []
    ):

        topic_name = topic.get(
            "display_name",
            ""
        )

        if topic_name:

            topics.append(topic_name)

    concepts = []

    for concept in work.get(
        "concepts",
        []
    ):

        concept_name = concept.get(
            "display_name",
            ""
        )

        if concept_name:

            concepts.append(concept_name)

    primary_topic = ""

    primary_topic_data = work.get(
        "primary_topic"
    )

    if isinstance(
        primary_topic_data,
        dict
    ):

        primary_topic = (
            primary_topic_data.get(
                "display_name",
                ""
            )
        )

    # --------------------------------------------------------
    # PUBLICATION NAME
    # --------------------------------------------------------

    publication_name = ""

    primary_location = work.get(
        "primary_location",
        {}
    )

    if isinstance(
        primary_location,
        dict
    ):

        source = primary_location.get(
            "source",
            {}
        )

        if isinstance(
            source,
            dict
        ):

            publication_name = source.get(
                "display_name",
                ""
            )

    # --------------------------------------------------------
    # PUBLICATION DATE
    # --------------------------------------------------------

    publication_date = work.get(
        "publication_date",
        ""
    )

    # --------------------------------------------------------
    # ABSTRACT
    # --------------------------------------------------------

    abstract = ""

    abstract_inverted_index = work.get(
        "abstract_inverted_index"
    )

    if isinstance(
        abstract_inverted_index,
        dict
    ):

        abstract_words = []

        for word, positions in abstract_inverted_index.items():

            if isinstance(
                positions,
                list
            ):

                for position in positions:

                    abstract_words.append(
                        (
                            position,
                            word
                        )
                    )

        abstract_words.sort(
            key=lambda item: item[0]
        )

        abstract = " ".join(
            word
            for _, word in abstract_words
        )

    # --------------------------------------------------------
    # OPENALEX / SCOPUS IDENTIFIERS
    # --------------------------------------------------------

    openalex_id = work.get(
        "id",
        ""
    )

    # OpenAlex does not provide a Scopus EID
    # for every work, so leave EID blank unless
    # one is explicitly available.

    eid = work.get(
        "eid",
        ""
    )

    # OpenAlex does not guarantee a Scopus URL.
    # Use it only if one is explicitly available.

    scopus_url = work.get(
        "scopus_url",
        ""
    )

    # --------------------------------------------------------
    # DOCUMENT TYPE
    # --------------------------------------------------------

    document_type = work.get(
        "type",
        ""
    )

    # OpenAlex does not expose the Scopus-style
    # subtype consistently, so use an explicitly
    # available subtype when present.

    subtype = work.get(
        "subtype",
        ""
    )

    return {

        "openalex_id": openalex_id,

        "title": work.get(
            "title",
            ""
        ),

        "doi": work.get(
            "doi",
            ""
        ),

        "eid": eid,

        "authors": authors,

        "publication_name": publication_name,

        "publication_date": publication_date,

        "abstract": abstract,

        "cited_by_count": work.get(
            "cited_by_count",
            0
        ),

        "document_type": document_type,

        "subtype": subtype,

        "scopus_url": scopus_url,

        "primary_topic": primary_topic,

        "topics": topics,

        "concepts": concepts,

        "type": work.get(
            "type",
            ""
        ),

        "landing_page_url": work.get(
            "primary_location",
            {}
        ).get(
            "landing_page_url",
            ""
        )
    }


# ============================================================
# BUILD SEARCH QUERY
# ============================================================

def build_search_query(
    languages,
    field,
    domain,
    interests
):
    """
    Build a scholarly OpenAlex search query
    from the user's advisor inputs.
    """

    parts = []

    if languages:

        if isinstance(
            languages,
            list
        ):

            parts.extend(
                languages
            )

        else:

            parts.append(
                str(languages)
            )

    if field:

        parts.append(field)

    if domain:

        parts.append(domain)

    if interests:

        parts.append(interests)

    return " ".join(
        part.strip()
        for part in parts
        if part and str(part).strip()
    )


# ============================================================
# EXTRACT RESEARCH AREAS
# ============================================================

def extract_research_areas(
    works
):
    """
    Extract the most relevant research areas
    from OpenAlex results.
    """

    areas = []

    for work in works:

        if work.get(
            "primary_topic"
        ):

            areas.append(
                work["primary_topic"]
            )

        for topic in work.get(
            "topics",
            []
        ):

            areas.append(topic)

        for concept in work.get(
            "concepts",
            []
        ):

            areas.append(concept)

    # Remove duplicates while preserving order

    unique_areas = []

    for area in areas:

        clean_area = area.strip()

        if (
            clean_area
            and clean_area.lower()
            not in [
                x.lower()
                for x in unique_areas
            ]
        ):

            unique_areas.append(
                clean_area
            )

    return unique_areas


# ============================================================
# GENERATE TOPIC SUGGESTIONS
# ============================================================

def generate_topic_suggestions(
    languages,
    field,
    domain,
    interests,
    methodology,
    research_areas
):
    """
    Generate 5 research-topic suggestions.

    OpenAlex supplies the scholarly research areas.
    The suggestions are constructed around the user's
    selected language, field, domain and interests.
    """

    language_text = (
        ", ".join(languages)
        if isinstance(
            languages,
            list
        )
        else str(languages or "")
    )

    field_text = (
        field
        or "the selected field"
    )

    domain_text = (
        domain
        or "the selected domain"
    )

    interest_text = (
        interests
        if interests
        else "emerging research challenges"
    )

    method_text = (
        methodology
        if methodology
        else "experimental evaluation"
    )

    suggestions = []

    # --------------------------------------------------------
    # USE OPENALEX RESEARCH AREAS
    # --------------------------------------------------------

    for area in research_areas:

        if len(suggestions) >= 5:

            break

        if language_text:

            topic = (
                f"Applications of {area} "
                f"using {language_text} "
                f"in {domain_text}"
            )

        else:

            topic = (
                f"Applications of {area} "
                f"in {domain_text}"
            )

        suggestions.append(
            topic
        )

    # --------------------------------------------------------
    # FALLBACK TOPICS
    # --------------------------------------------------------

    fallback_topics = [

        (
            f"An investigation of "
            f"{interest_text} in "
            f"{domain_text}"
        ),

        (
            f"Comparative analysis of "
            f"{interest_text} for "
            f"{field_text}"
        ),

        (
            f"Evaluation of {interest_text} "
            f"using {method_text} "
            f"in {domain_text}"
        ),

        (
            f"Developing an intelligent "
            f"{field_text} solution for "
            f"{domain_text}"
        ),

        (
            f"Emerging challenges and future "
            f"directions in {interest_text} "
            f"for {domain_text}"
        )
    ]

    for topic in fallback_topics:

        if len(suggestions) >= 5:

            break

        if topic not in suggestions:

            suggestions.append(
                topic
            )

    return suggestions[:5]


# ============================================================
# SAVE SELECTED TOPIC
# ============================================================

def save_selected_topic(
    languages,
    field,
    domain,
    interests,
    methodology,
    experience_level,
    query,
    selected_topic,
    supporting_works,
    total_results
):
    """
    Store the generated advisor response and the
    actual user-selected research direction.
    """

    return save_advisor_result(
        languages=languages,
        field=field,
        domain=domain,
        interests=interests,
        methodology=methodology,
        experience_level=experience_level,
        query=query,
        selected_topic=selected_topic,
        supporting_works=supporting_works,
        total_results=total_results
    )


# ============================================================
# MAIN RESEARCH PROJECT ADVISOR
# ============================================================

def research_project_advisor(
    languages,
    field,
    domain=None,
    interests=None,
    methodology=None,
    experience_level=None,
    selected_topic=None
):
    """
    Main ResearchIQ Research Project Advisor.

    The advisor generates five suggestions.

    The CSV is automatically created inside the
    datasets folder if it does not already exist.

    New advisor records are appended to the existing
    CSV file.
    """

    # --------------------------------------------------------
    # MAKE SURE CSV EXISTS
    # --------------------------------------------------------

    ensure_csv()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not languages:

        return {
            "success": False,
            "error": "At least one programming language is required.",
            "suggestions": []
        }

    if not field:

        return {
            "success": False,
            "error": "Research field is required.",
            "suggestions": []
        }

    # --------------------------------------------------------
    # BUILD SEARCH QUERY
    # --------------------------------------------------------

    search_query = build_search_query(
        languages=languages,
        field=field,
        domain=domain,
        interests=interests
    )

    # --------------------------------------------------------
    # SEARCH OPENALEX
    # --------------------------------------------------------

    openalex_result = search_openalex(
        search_query=search_query,
        limit=10
    )

    if not openalex_result["success"]:

        return {
            "success": False,
            "error": openalex_result["error"],
            "suggestions": []
        }

    # --------------------------------------------------------
    # FORMAT WORKS
    # --------------------------------------------------------

    formatted_works = []

    for work in openalex_result[
        "results"
    ]:

        formatted_works.append(
            format_work(work)
        )

    # --------------------------------------------------------
    # EXTRACT RESEARCH AREAS
    # --------------------------------------------------------

    research_areas = extract_research_areas(
        formatted_works
    )

    # --------------------------------------------------------
    # GENERATE TOPICS
    # --------------------------------------------------------

    suggestions = generate_topic_suggestions(
        languages=languages,
        field=field,
        domain=domain,
        interests=interests,
        methodology=methodology,
        research_areas=research_areas
    )

    # --------------------------------------------------------
    # SAVE ADVISOR RESULT
    # --------------------------------------------------------

    saved = save_advisor_result(
        languages=languages,
        field=field,
        domain=domain,
        interests=interests,
        methodology=methodology,
        experience_level=experience_level,
        query=search_query,
        selected_topic=selected_topic,
        supporting_works=formatted_works,
        total_results=openalex_result.get(
            "meta",
            {}
        ).get(
            "count",
            0
        )
    )

    # --------------------------------------------------------
    # TOTAL RESULTS
    # --------------------------------------------------------

    total_results = openalex_result.get(
        "meta",
        {}
    ).get(
        "count",
        0
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "success": True,

        "inputs": {

            "languages": languages,

            "field": field,

            "domain": domain,

            "interests": interests,

            "methodology": methodology,

            "experience_level": experience_level
        },

        "search_query": search_query,

        "suggestions": suggestions,

        "supporting_works": formatted_works,

        "selected_topic": selected_topic,

        "saved": saved,

        "total_results": total_results
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n======================================"
    )

    print(
        "   RESEARCH IQ OPENALEX ADVISOR TEST"
    )

    print(
        "======================================\n"
    )

    result = research_project_advisor(

        languages=[
            "Python",
            "JavaScript"
        ],

        field="Artificial Intelligence",

        domain="Healthcare",

        interests=(
            "generative AI and medical diagnosis"
        ),

        methodology="experimental evaluation",

        experience_level="Intermediate"
    )

    if result["success"]:

        print(
            "Research Topic Suggestions:\n"
        )

        for index, topic in enumerate(
            result["suggestions"],
            start=1
        ):

            print(
                f"{index}. {topic}"
            )

        print(
            "\nSupporting OpenAlex works:\n"
        )

        for work in result[
            "supporting_works"
        ][:5]:

            print(
                f"- {work['title']}"
            )

        print(
            "\nCSV path:"
        )

        print(
            CSV_FILE
        )

        print(
            "\nCSV has been created if it did not "
            "exist, or the new records have been "
            "appended if it already existed."
        )

        print(
            f"\nCSV saved: {result['saved']}"
        )

    else:

        print(
            "ERROR:",
            result["error"]
        )
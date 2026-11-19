
import os
import re
import json
import time
import html
import unicodedata
import pandas as pd
import requests
import toml

from bs4 import BeautifulSoup
from ftfy import fix_text


# ============================================================
# 1. CONFIGURATION
# ============================================================

JOB_DATASET = "dataset/IT_Job_Roles_Skills.csv"
RESUME_DATASET = "dataset/gpt_dataset.csv"

OUTPUT_CSV = "processed_data/career_fused_dataset.csv"
OUTPUT_EXCEL = "processed_data/career_fused_dataset.xlsx"

CACHE_DIR = "processed_data/api_cache"
SECRETS_FILE = ".streamlit/secrets.toml"

MAX_API_RESULTS = 5
REQUEST_TIMEOUT = 20

API_DELAY = 1.0
GITHUB_DELAY = 3.0

os.makedirs("processed_data", exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

USER_AGENT = {
    "User-Agent": "IT-Career-Guidance-Data-Fusion/1.0"
}


# ============================================================
# 2. LOAD YOUTUBE API KEY
# ============================================================

print("\n========== API CONFIGURATION ==========")

YOUTUBE_API_KEY = ""

try:
    secrets = toml.load(SECRETS_FILE)

    YOUTUBE_API_KEY = secrets.get(
        "YOUTUBE_API_KEY", ""
    )

    if YOUTUBE_API_KEY:
        print("YouTube API key loaded successfully.")
    else:
        print("YouTube API key not found.")

except FileNotFoundError:
    print("secrets.toml not found. YouTube API will be skipped.")

except Exception as e:
    print("Secrets loading error:", e)


# ============================================================
# 3. HTTP SESSION
# ============================================================

session = requests.Session()
session.headers.update(USER_AGENT)


# ============================================================
# 4. SAFE CSV LOADING
# ============================================================

def load_csv_safely(file_path):

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1"
    ]

    for encoding in encodings:

        try:

            df = pd.read_csv(
                file_path,
                encoding=encoding,
                keep_default_na=True
            )

            print(
                f"Loaded {file_path} using {encoding}"
            )

            return df

        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"Unable to decode CSV: {file_path}"
    )


# ============================================================
# 5. TEXT CLEANING AND EMOJI REMOVAL
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except (TypeError, ValueError):
        pass

    value = str(value)

    # Decode HTML entities
    value = html.unescape(value)

    # Remove HTML tags
    value = BeautifulSoup(
        value,
        "html.parser"
    ).get_text(" ", strip=True)

    # Fix common encoding problems
    value = fix_text(value)

    # Normalize Unicode
    value = unicodedata.normalize(
        "NFKC",
        value
    )

    # Remove invisible characters
    value = value.replace("\ufeff", "")
    value = value.replace("\u200b", "")
    value = value.replace("\u200c", "")
    value = value.replace("\u200d", "")
    value = value.replace("\xa0", " ")

    # Remove unwanted control characters
    value = "".join(
        char for char in value
        if unicodedata.category(char) != "Cc"
        or char in "\n\t"
    )

    # Remove emojis and decorative symbols
    value = re.sub(
        r"[\U0001F000-\U0001FAFF"
        r"\U00002700-\U000027BF"
        r"\U00002600-\U000026FF"
        r"\U0001F1E0-\U0001F1FF"
        r"\uFE0F"
        r"\u20E3]+",
        "",
        value
    )

    # Remove extra spaces
    value = " ".join(value.split())

    return value.strip()


# ============================================================
# 6. NORMALIZE CAREER ROLE
# ============================================================

def normalize_role(role):

    role = clean_text(role).lower()

    if not role:
        return ""

    role = role.replace("&", " and ")
    role = role.replace("/", " ")
    role = role.replace("-", " ")

    role = re.sub(
        r"[^a-z0-9\s]",
        " ",
        role
    )

    role = " ".join(role.split())

    return role


# ============================================================
# 7. COMBINE API VALUES
# ============================================================

def combine_values(values):

    cleaned = []

    for value in values:

        value = clean_text(value)

        if value and value not in cleaned:
            cleaned.append(value)

    return " || ".join(cleaned)


# ============================================================
# 8. CACHE FUNCTIONS
# ============================================================

def cache_filename(service, role):

    safe_role = normalize_role(role)

    safe_role = re.sub(
        r"[^a-z0-9]+",
        "_",
        safe_role
    )

    safe_role = safe_role[:100] or "unknown"

    return os.path.join(
        CACHE_DIR,
        f"{service}_{safe_role}.json"
    )


def load_cache(service, role):

    filename = cache_filename(
        service,
        role
    )

    if not os.path.exists(filename):
        return None

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (OSError, json.JSONDecodeError):
        return None


def save_cache(service, role, data):

    filename = cache_filename(
        service,
        role
    )

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print("Cache save error:", e)


# ============================================================
# 9. SAFE API REQUEST
# ============================================================

def safe_get(
    url,
    params=None,
    headers=None,
    service="api",
    role=""
):

    # Check cache first
    if service and role:

        cached = load_cache(
            service,
            role
        )

        if cached is not None:

            print(
                f"{service}: Using cached data for {role}"
            )

            return cached

    try:

        response = session.get(
            url,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 429:

            print(
                f"{service}: API rate limit reached."
            )

            return {}

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            print(f"{service}: Unexpected API response.")
            return {}

        if service and role:

            save_cache(
                service,
                role,
                data
            )

        return data

    except requests.exceptions.Timeout:

        print(f"{service}: Request timed out.")

    except requests.exceptions.HTTPError as e:

        print(f"{service}: HTTP error: {e}")

    except requests.exceptions.RequestException as e:

        print(f"{service}: Request error: {e}")

    except ValueError:

        print(f"{service}: Invalid JSON response.")

    except Exception as e:

        print(f"{service}: Unexpected error: {e}")

    return {}


# ============================================================
# 10. LOAD IT JOB DATASET
# ============================================================

print("\n========== 1. LOADING JOB DATASET ==========")

job_df = load_csv_safely(JOB_DATASET)

print("Job Dataset Shape:", job_df.shape)

required_job_columns = [
    "Job Title",
    "Job Description",
    "Skills",
    "Certifications"
]

for column in required_job_columns:

    if column not in job_df.columns:

        raise ValueError(
            f"Missing job dataset column: {column}"
        )

job_df = job_df[
    required_job_columns
].copy()

job_df = job_df.fillna("")

for column in required_job_columns:

    job_df[column] = job_df[column].apply(clean_text)

job_df["career_role"] = job_df["Job Title"].apply(clean_text)

job_df["role_key"] = job_df["career_role"].apply(normalize_role)

print("Original Job Records:", len(job_df))

print(
    "Unique Career Roles:",
    job_df["role_key"].nunique()
)


# ============================================================
# 11. LOAD RESUME DATASET
# ============================================================

print("\n========== 2. LOADING RESUME DATASET ==========")

resume_df = load_csv_safely(RESUME_DATASET)

print("Resume Dataset Shape:", resume_df.shape)

required_resume_columns = [
    "Category",
    "Resume"
]

for column in required_resume_columns:

    if column not in resume_df.columns:

        raise ValueError(
            f"Missing resume dataset column: {column}"
        )

resume_df = resume_df[
    required_resume_columns
].copy()

resume_df = resume_df.fillna("")

resume_df["Category"] = resume_df["Category"].apply(clean_text)

resume_df["Resume"] = resume_df["Resume"].apply(clean_text)

resume_df["role_key"] = resume_df["Category"].apply(
    normalize_role
)

print("Resume Records:", len(resume_df))


# ============================================================
# 12. GROUP RESUMES BY ROLE
# ============================================================

print("\n========== 3. GROUPING RESUMES ==========")

resume_grouped = (

    resume_df[
        resume_df["role_key"] != ""
    ]

    .groupby("role_key")

    .agg(
        resume_samples=(
            "Resume",
            lambda x: combine_values(
                list(x)[:10]
            )
        )

    )

    .reset_index()

)

print(
    "Resume Categories:",
    len(resume_grouped)
)


# ============================================================
# 13. FUSE JOB AND RESUME DATA
# ============================================================

print("\n========== 4. JOB + RESUME FUSION ==========")

fused_df = pd.merge(
    job_df,
    resume_grouped,
    on="role_key",
    how="left",
    sort=False
)

fused_df["resume_samples"] = fused_df[
    "resume_samples"
].fillna("")

print("After Job + Resume Fusion:", fused_df.shape)


# ============================================================
# 14. UNIQUE ROLES
# ============================================================

unique_roles = (

    fused_df[
        ["career_role", "role_key"]
    ]

    .drop_duplicates()

    .reset_index(drop=True)

)

unique_roles = unique_roles[
    unique_roles["role_key"] != ""
].reset_index(drop=True)

print(
    "Unique Roles for API Processing:",
    len(unique_roles)
)


# ============================================================
# 15. REMOTIVE API - REMOTE JOBS
# ============================================================

print("\n========== 5. FETCHING REMOTIVE DATA ==========")


def remotive_search(role):

    url = "https://remotive.com/api/remote-jobs"

    params = {
        "search": role,
        "limit": MAX_API_RESULTS
    }

    data = safe_get(
        url,
        params=params,
        service="remotive",
        role=role
    )

    results = []

    for job in data.get("jobs", [])[:MAX_API_RESULTS]:

        record = (

            f"Job Title: {clean_text(job.get('title'))} | "

            f"Company: {clean_text(job.get('company_name'))} | "

            f"Job Type: {clean_text(job.get('job_type'))} | "

            f"Location: {clean_text(job.get('candidate_required_location'))} | "

            f"Description: {clean_text(job.get('description'))} | "

            f"URL: {clean_text(job.get('url'))}"

        )

        results.append(record)

    return combine_values(results)


remotive_map = {}

for index, row in unique_roles.iterrows():

    role = row["career_role"]

    print(
        f"Remotive [{index + 1}/{len(unique_roles)}]: {role}"
    )

    remotive_map[row["role_key"]] = remotive_search(role)

    time.sleep(API_DELAY)


fused_df["remotive_jobs"] = fused_df["role_key"].map(
    remotive_map
).fillna("")


# ============================================================
# 16. YOUTUBE API - LEARNING RESOURCES
# ============================================================

print("\n========== 6. FETCHING YOUTUBE DATA ==========")


def youtube_search(role):

    if not YOUTUBE_API_KEY:
        return ""

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": role,
        "type": "video",
        "maxResults": MAX_API_RESULTS,
        "key": YOUTUBE_API_KEY
    }

    data = safe_get(
        url,
        params=params,
        service="youtube",
        role=role
    )

    results = []

    for video in data.get("items", []):

        video_id = video.get(
            "id", {}
        ).get("videoId", "")

        snippet = video.get("snippet", {})

        if not video_id:
            continue

        record = (

            f"Title: {clean_text(snippet.get('title'))} | "

            f"Channel: {clean_text(snippet.get('channelTitle'))} | "

            f"Description: {clean_text(snippet.get('description'))} | "

            f"URL: https://www.youtube.com/watch?v={video_id}"

        )

        results.append(record)

    return combine_values(results)


youtube_map = {}

if YOUTUBE_API_KEY:

    for index, row in unique_roles.iterrows():

        role = row["career_role"]

        print(
            f"YouTube [{index + 1}/{len(unique_roles)}]: {role}"
        )

        youtube_map[row["role_key"]] = youtube_search(role)

        time.sleep(API_DELAY)

else:

    print("YouTube API skipped: API key unavailable.")


fused_df["youtube_resources"] = fused_df["role_key"].map(
    youtube_map
).fillna("")


# ============================================================
# 17. GITHUB API - PROJECTS
# ============================================================

print("\n========== 7. FETCHING GITHUB DATA ==========")


def github_search(role):

    url = "https://api.github.com/search/repositories"

    params = {
        "q": f'"{role}"',
        "sort": "stars",
        "order": "desc",
        "per_page": MAX_API_RESULTS
    }

    data = safe_get(
        url,
        params=params,
        headers=USER_AGENT,
        service="github",
        role=role
    )

    results = []

    for repo in data.get("items", [])[:MAX_API_RESULTS]:

        record = (

            f"Repository: {clean_text(repo.get('full_name'))} | "

            f"Description: {clean_text(repo.get('description'))} | "

            f"Language: {clean_text(repo.get('language'))} | "

            f"Stars: {repo.get('stargazers_count', 0)} | "

            f"URL: {clean_text(repo.get('html_url'))}"

        )

        results.append(record)

    return combine_values(results)


github_map = {}

for index, row in unique_roles.iterrows():

    role = row["career_role"]

    print(
        f"GitHub [{index + 1}/{len(unique_roles)}]: {role}"
    )

    github_map[row["role_key"]] = github_search(role)

    time.sleep(GITHUB_DELAY)


fused_df["github_projects"] = fused_df["role_key"].map(
    github_map
).fillna("")


# ============================================================
# 18. OPEN LIBRARY API - TECHNICAL BOOKS
# ============================================================

print("\n========== 8. FETCHING OPEN LIBRARY DATA ==========")


def openlibrary_search(role):

    url = "https://openlibrary.org/search.json"

    params = {
        "q": role,
        "limit": MAX_API_RESULTS
    }

    data = safe_get(
        url,
        params=params,
        service="openlibrary",
        role=role
    )

    results = []

    for book in data.get("docs", [])[:MAX_API_RESULTS]:

        authors = book.get("author_name", [])

        authors = [
            clean_text(author)
            for author in authors[:3]
        ]

        key = book.get("key", "")

        book_url = (
            f"https://openlibrary.org{key}"
            if key else ""
        )

        record = (

            f"Title: {clean_text(book.get('title'))} | "

            f"Authors: {', '.join(authors)} | "

            f"First Published: {book.get('first_publish_year', '')} | "

            f"URL: {book_url}"

        )

        results.append(record)

    return combine_values(results)


openlibrary_map = {}

for index, row in unique_roles.iterrows():

    role = row["career_role"]

    print(
        f"Open Library [{index + 1}/{len(unique_roles)}]: {role}"
    )

    openlibrary_map[row["role_key"]] = openlibrary_search(role)

    time.sleep(API_DELAY)


fused_df["technical_books"] = fused_df["role_key"].map(
    openlibrary_map
).fillna("")


# ============================================================
# 19. OPENALEX API - RESEARCH PAPERS
# ============================================================

print("\n========== 9. FETCHING OPENALEX DATA ==========")


def openalex_search(role):

    url = "https://api.openalex.org/works"

    params = {
        "search": role,
        "per-page": MAX_API_RESULTS
    }

    data = safe_get(
        url,
        params=params,
        headers=USER_AGENT,
        service="openalex",
        role=role
    )

    results = []

    for work in data.get("results", [])[:MAX_API_RESULTS]:

        record = (

            f"Research Title: {clean_text(work.get('title'))} | "

            f"Publication Year: {work.get('publication_year', '')} | "

            f"DOI: {clean_text(work.get('doi'))} | "

            f"URL: {clean_text(work.get('id'))}"

        )

        results.append(record)

    return combine_values(results)


openalex_map = {}

for index, row in unique_roles.iterrows():

    role = row["career_role"]

    print(
        f"OpenAlex [{index + 1}/{len(unique_roles)}]: {role}"
    )

    openalex_map[row["role_key"]] = openalex_search(role)

    time.sleep(API_DELAY)


fused_df["research_papers"] = fused_df["role_key"].map(
    openalex_map
).fillna("")


# ============================================================
# 20. REMOVE INTERNAL ROLE KEY
# ============================================================

print("\n========== 10. FINAL CLEANING ==========")

fused_df = fused_df.drop(
    columns=["role_key"]
)


# ============================================================
# 21. FINAL COLUMN ORDER
# ============================================================

desired_columns = [

    "Job Title",
    "Job Description",
    "Skills",
    "Certifications",
    "career_role",
    "resume_samples",
    "remotive_jobs",
    "youtube_resources",
    "github_projects",
    "technical_books",
    "research_papers"

]

fused_df = fused_df[desired_columns]


# ============================================================
# 22. CLEAN FINAL DATASET
# ============================================================

for column in fused_df.columns:

    fused_df[column] = fused_df[column].apply(clean_text)


# ============================================================
# 23. SAVE CSV
# ============================================================

print("\n========== 11. SAVING CSV ==========")

fused_df.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig"
)

print("CSV saved:", OUTPUT_CSV)


# ============================================================
# 24. SAVE EXCEL
# ============================================================

print("\n========== 12. SAVING EXCEL ==========")

fused_df.to_excel(
    OUTPUT_EXCEL,
    index=False,
    engine="openpyxl"
)

print("Excel saved:", OUTPUT_EXCEL)


# ============================================================
# 25. FINAL REPORT
# ============================================================

print("\n==============================================")
print("             DATA FUSION COMPLETED")
print("==============================================")

print("Original Job Records:", len(job_df))
print("Resume Records:", len(resume_df))
print("Unique Career Roles:", len(unique_roles))
print("Final Fused Records:", len(fused_df))
print("Final Number of Columns:", len(fused_df.columns))


# ============================================================
# 26. API DATA COVERAGE
# ============================================================

print("\n========== API DATA COVERAGE ==========")

api_columns = [

    "resume_samples",
    "remotive_jobs",
    "youtube_resources",
    "github_projects",
    "technical_books",
    "research_papers"

]

for column in api_columns:

    non_empty = (
        fused_df[column]
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    print(
        f"{column}: {non_empty}/{len(fused_df)} records contain data"
    )


# ============================================================
# 27. FINAL COLUMN NAMES
# ============================================================

print("\n========== FINAL COLUMNS ==========")

for number, column in enumerate(
    fused_df.columns,
    start=1
):

    print(f"{number}. {column}")


# ============================================================
# 28. SAMPLE FUSED DATA
# ============================================================

print("\n========== SAMPLE FUSED DATA ==========")

sample_columns = [

    "Job Title",
    "Skills",
    "career_role",
    "resume_samples",
    "remotive_jobs",
    "youtube_resources",
    "github_projects",
    "technical_books",
    "research_papers"

]

print(
    fused_df[sample_columns]
    .head(3)
    .to_string(index=False)
)


# ============================================================
# 29. CREATED FILES
# ============================================================

print("\n========== CREATED FILES ==========")

print("CSV:", OUTPUT_CSV)
print("Excel:", OUTPUT_EXCEL)
print("API Cache:", CACHE_DIR)

print("\n==============================================")
print("       IT CAREER DATA FUSION SUCCESSFUL")
print("==============================================")

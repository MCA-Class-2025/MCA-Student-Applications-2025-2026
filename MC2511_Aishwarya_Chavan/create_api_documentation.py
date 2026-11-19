
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
import os

# =====================================================
# MOVIEVERSE AI - API DOCUMENTATION
# =====================================================

OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "API_DOCUMENTATION.pdf"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

doc = SimpleDocTemplate(
    OUTPUT_FILE,
    pagesize=A4,
    rightMargin=50,
    leftMargin=50,
    topMargin=55,
    bottomMargin=50
)

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="MainTitle",
    parent=styles["Title"],
    fontSize=25,
    leading=32,
    alignment=TA_CENTER,
    textColor=HexColor("#17365D"),
    spaceAfter=18
))

styles.add(ParagraphStyle(
    name="SectionHeading",
    parent=styles["Heading2"],
    fontSize=16,
    leading=21,
    textColor=HexColor("#1F4E79"),
    spaceBefore=15,
    spaceAfter=8
))

styles.add(ParagraphStyle(
    name="CustomBody",
    parent=styles["BodyText"],
    fontSize=9.5,
    leading=15,
    spaceAfter=7
))

styles.add(ParagraphStyle(
    name="SmallNote",
    parent=styles["BodyText"],
    fontSize=8,
    leading=12,
    textColor=colors.grey
))

story = []

def heading(text):
    story.append(Paragraph(text, styles["SectionHeading"]))

def paragraph(text):
    story.append(Paragraph(text, styles["CustomBody"]))

def bullet(text):
    paragraph("&#8226; " + text)

# =====================================================
# COVER PAGE
# =====================================================

story.append(Spacer(1, 1.1 * inch))

story.append(Paragraph(
    "MOVIEVERSE AI",
    styles["MainTitle"]
))

story.append(Paragraph(
    "API DOCUMENTATION",
    ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=17,
        textColor=HexColor("#4472C4")
    )
))

story.append(Spacer(1, 25))

paragraph(
    "<b>Project:</b> LLM and RAG Based Movie Recommendation System"
)

paragraph(
    "<b>Technology:</b> Python, Streamlit, LangChain, FAISS and Gemini"
)

paragraph(
    "<b>Documentation scope:</b> Five external movie information APIs"
)

story.append(Spacer(1, 25))

heading("Purpose of this Document")

paragraph(
    "This document explains the external APIs integrated into "
    "MovieVerse AI. It describes their purpose, authentication "
    "requirements, endpoints, request parameters, response data, "
    "and error handling based on the project's service modules."
)

story.append(PageBreak())

# =====================================================
# API OVERVIEW
# =====================================================

heading("1. API Overview")

api_data = [
    ["API", "Purpose", "Authentication"],
    ["TMDB", "Movie search and discovery", "API Key / Bearer Token"],
    ["OMDb", "Movie ratings and details", "API Key"],
    ["Watchmode", "Streaming availability", "API Key"],
    ["News API", "Movie-related news", "API Key"],
    ["Wikipedia", "Movie summaries and information", "No API key in implementation"]
]

table = Table(api_data, colWidths=[90, 190, 170], repeatRows=1)

table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#17365D")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
     [colors.white, HexColor("#EAF0F8")]),
    ("PADDING", (0, 0), (-1, -1), 7),
]))

story.append(table)

# =====================================================
# TMDB
# =====================================================

heading("2. TMDB API")

paragraph(
    "<b>Service file:</b> services/tmdb_service.py"
)

paragraph(
    "<b>Purpose:</b> TMDB provides movie search and discovery "
    "information, including titles, descriptions, release dates, "
    "posters, ratings and popularity."
)

paragraph(
    "<b>Base URL:</b> https://api.themoviedb.org/3"
)

paragraph(
    "<b>Authentication:</b> TMDB API key or Bearer access token. "
    "Credentials are loaded from environment variables."
)

paragraph("<b>Function 1: search_movie(movie_title)</b>")

bullet("Endpoint: GET /search/movie")
bullet("Parameter: query = movie title")
bullet("Additional parameters: language=en-US, include_adult=false")
bullet("Timeout: (5, 20) seconds")

paragraph("<b>Returned information:</b>")

bullet("TMDB ID, title and original title")
bullet("Overview and release date")
bullet("Poster and backdrop paths")
bullet("Rating, vote count and popularity")
bullet("Original language and search results")

paragraph("<b>Function 2: discover_movies(region='IN', page=1)</b>")

bullet("Endpoint: GET /discover/movie")
bullet("Parameters include region, page and sort_by")
bullet("Sort order: popularity.desc")
bullet("Returns movies, page number and result counts")

paragraph("<b>Error handling:</b> Authentication errors, rate limits, "
          "HTTP errors, connection errors and timeouts are handled.")

# =====================================================
# OMDB
# =====================================================

heading("3. OMDb API")

paragraph(
    "<b>Service file:</b> services/omdb_service.py"
)

paragraph(
    "<b>Purpose:</b> OMDb provides additional movie information "
    "and IMDb-related details."
)

paragraph(
    "<b>Base URL:</b> https://www.omdbapi.com/"
)

paragraph(
    "<b>Authentication:</b> API key loaded through OMDB_API_KEY."
)

paragraph("<b>Function: search_movie(title)</b>")

bullet("HTTP method: GET")
bullet("Parameter: t = movie title")
bullet("Parameter: type = movie")
bullet("Timeout: 15 seconds")

paragraph("<b>Returned information:</b>")

bullet("Title and year")
bullet("IMDb rating and IMDb ID")
bullet("Director and actors")
bullet("Awards, plot and genre")
bullet("Runtime")

paragraph(
    "<b>Error handling:</b> Checks API key availability and the "
    "API Response field. Handles unsuccessful responses and exceptions."
)

# =====================================================
# WATCHMODE
# =====================================================

heading("4. Watchmode API")

paragraph(
    "<b>Service file:</b> services/watchmode_service.py"
)

paragraph(
    "<b>Purpose:</b> Watchmode helps find streaming availability "
    "and viewing sources for movies."
)

paragraph(
    "<b>Base URL:</b> https://api.watchmode.com/v1"
)

paragraph(
    "<b>Authentication:</b> API key loaded through WATCHMODE_API_KEY."
)

paragraph("<b>Function 1: search_title(title)</b>")

bullet("Endpoint: GET /search/")
bullet("Parameters: apiKey, search_value and search_field=name")
bullet("Returns matching title results.")

paragraph("<b>Function 2: get_sources(title_id)</b>")

bullet("Endpoint: GET /title/{title_id}/sources/")
bullet("Parameter: apiKey")
bullet("Returns available source information for the title.")

paragraph(
    "<b>Error handling:</b> Checks API key availability and handles "
    "request exceptions."
)

# =====================================================
# NEWS API
# =====================================================

heading("5. News API")

paragraph(
    "<b>Service file:</b> services/news_service.py"
)

paragraph(
    "<b>Purpose:</b> Retrieves recent news articles related to a "
    "movie or movie title."
)

paragraph(
    "<b>Endpoint:</b> https://newsapi.org/v2/everything"
)

paragraph(
    "<b>Authentication:</b> API key loaded through NEWS_API_KEY."
)

paragraph("<b>Function: get_movie_news(title)</b>")

bullet("HTTP method: GET")
bullet("Search query: q = movie title")
bullet("Language: English")
bullet("Sort order: publishedAt")
bullet("Page size: 5 articles")
bullet("Timeout: 15 seconds")

paragraph("<b>Returned article information:</b>")

bullet("Article title and description")
bullet("Article URL")
bullet("Publication date")
bullet("News source name")

paragraph(
    "<b>Error handling:</b> Checks API key availability and handles "
    "request exceptions."
)

# =====================================================
# WIKIPEDIA
# =====================================================

heading("6. Wikipedia REST API")

paragraph(
    "<b>Service file:</b> services/wikipedia_service.py"
)

paragraph(
    "<b>Purpose:</b> Retrieves encyclopedic movie information "
    "and summaries."
)

paragraph(
    "<b>Endpoint:</b> https://en.wikipedia.org/api/rest_v1/page/summary/"
)

paragraph(
    "<b>Authentication:</b> No API key is used in the current implementation."
)

paragraph("<b>Function: search_wikipedia(movie_title)</b>")

bullet("Validates the movie title.")
bullet("Removes extra spaces and encodes the title for the URL.")
bullet("Sends an HTTP GET request.")
bullet("Timeout: 15 seconds.")
bullet("Uses a MovieVerseAI User-Agent header.")

paragraph("<b>Returned information:</b>")

bullet("Wikipedia page title")
bullet("Description and summary")
bullet("Wikipedia page URL")
bullet("Thumbnail image URL, when available")

paragraph(
    "<b>Error handling:</b> Handles page-not-found responses, "
    "other HTTP errors, timeouts and request exceptions."
)

# =====================================================
# SECURITY
# =====================================================

heading("7. API Security and Credential Management")

paragraph(
    "API credentials are loaded from environment variables using "
    "python-dotenv. The project should keep credentials in a local "
    ".env file and must not upload that file to a public repository."
)

bullet("Never hardcode API keys in source code.")
bullet("Do not commit .env or secrets.toml files.")
bullet("Use environment variables for API authentication.")
bullet("Keep API keys private.")
bullet("Follow each provider's terms, rate limits and usage policies.")

# =====================================================
# LIMITATIONS
# =====================================================

heading("8. Limitations and Notes")

paragraph(
    "API availability depends on network connectivity, provider "
    "authentication, service status and account-level usage limits. "
    "Actual response fields may vary depending on the provider and "
    "the requested movie."
)

paragraph(
    "This document describes the current service-module implementation. "
    "It does not guarantee API quotas, subscription benefits or "
    "streaming availability in every country."
)

# =====================================================
# CONCLUSION
# =====================================================

heading("9. Conclusion")

paragraph(
    "MovieVerse AI integrates TMDB, OMDb, Watchmode, News API and "
    "Wikipedia to collect complementary movie information. These "
    "services support movie discovery, detailed information, streaming "
    "source lookup, news retrieval and movie summaries."
)

story.append(Spacer(1, 20))

paragraph(
    "<b>Project:</b> MovieVerse AI"
)

paragraph(
    "<b>Document:</b> API Documentation"
)

paragraph(
    "<b>Generated using:</b> Python ReportLab"
)

# =====================================================
# PAGE NUMBER
# =====================================================

def add_page_number(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(
        A4[0] / 2,
        25,
        f"MovieVerse AI | API Documentation | Page {document.page}"
    )
    canvas.restoreState()

# =====================================================
# GENERATE PDF
# =====================================================

doc.build(
    story,
    onFirstPage=add_page_number,
    onLaterPages=add_page_number
)

print("=" * 55)
print("SUCCESS: API DOCUMENTATION PDF CREATED")
print("File:", os.path.abspath(OUTPUT_FILE))
print("=" * 55)

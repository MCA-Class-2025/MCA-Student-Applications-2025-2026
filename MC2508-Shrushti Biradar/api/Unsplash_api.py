import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# UNSPLASH CONFIGURATION
# ============================================================

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


# ============================================================
# SEARCH UNSPLASH PHOTOS
# ============================================================

def search_unsplash_photos(
    query,
    per_page=10,
    page=1
):
    """
    Search Unsplash for photos.
    """

    if not UNSPLASH_ACCESS_KEY:
        st.error("❌ UNSPLASH_ACCESS_KEY is not configured.")
        return []

    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    params = {
        "query": query,
        "page": page,
        "per_page": per_page,
        "orientation": "landscape"
    }

    try:

        response = requests.get(
            UNSPLASH_SEARCH_URL,
            headers=headers,
            params=params,
            timeout=15
        )

        # Check API response
        if response.status_code != 200:

            st.error(
                f"❌ Unsplash API Error: {response.status_code}"
            )

            st.error(
                f"Details from Unsplash: {response.text}"
            )

            return []

        # Convert response to JSON
        data = response.json()

        photos = []

        for photo in data.get("results", []):

            photo_data = {
                "id": photo.get("id"),

                "image_url": photo.get(
                    "urls", {}
                ).get("regular"),

                "full_image_url": photo.get(
                    "urls", {}
                ).get("full"),

                "photographer": photo.get(
                    "user", {}
                ).get(
                    "name",
                    "Unknown Photographer"
                ),

                "photographer_url": photo.get(
                    "user", {}
                ).get(
                    "links", {}
                ).get(
                    "html",
                    "https://unsplash.com/"
                ),

                "photo_url": photo.get(
                    "links", {}
                ).get(
                    "html",
                    "https://unsplash.com/"
                ),

                "download_location": photo.get(
                    "links", {}
                ).get(
                    "download_location"
                ),

                "description": photo.get(
                    "alt_description"
                ),

                "width": photo.get("width"),

                "height": photo.get("height")
            }

            photos.append(photo_data)

        return photos

    except requests.exceptions.RequestException as e:

        st.error(
            f"❌ Could not connect to Unsplash: {e}"
        )

        return []

    except Exception as e:

        st.error(
            f"❌ Unexpected Unsplash error: {e}"
        )

        return []


# ============================================================
# EVENT SEARCH CATEGORIES
# ============================================================

EVENT_CATEGORIES = {

    "Birthday": [
        "birthday decoration",
        "birthday stage decoration",
        "birthday balloons decoration",
        "birthday table decoration",
        "birthday cake decoration",
        "birthday entrance decoration",
        "birthday party setup",
        "birthday backdrop"
    ],

    "Wedding": [
        "wedding decoration",
        "wedding stage decoration",
        "wedding mandap decoration",
        "wedding flower decoration",
        "wedding lighting decoration",
        "wedding entrance decoration",
        "wedding table decoration",
        "wedding reception decoration",
        "wedding backdrop"
    ],

    "Engagement": [
        "engagement decoration",
        "engagement stage decoration",
        "engagement ring ceremony decoration",
        "engagement flower decoration",
        "engagement backdrop",
        "engagement entrance decoration",
        "engagement table decoration"
    ],

    "Anniversary": [
        "anniversary decoration",
        "romantic anniversary decoration",
        "anniversary stage decoration",
        "anniversary flower decoration",
        "anniversary balloon decoration",
        "anniversary table decoration",
        "anniversary candle decoration"
    ],

    "Party": [
        "party decoration",
        "party stage decoration",
        "party balloons decoration",
        "party lighting",
        "party table decoration",
        "party entrance decoration",
        "party backdrop",
        "party venue decoration"
    ],

    "Baby Shower": [
        "baby shower decoration",
        "baby shower stage decoration",
        "baby shower balloons",
        "baby shower backdrop",
        "baby shower table decoration",
        "baby shower entrance decoration",
        "baby shower flowers"
    ],

    "Bridal Shower": [
        "bridal shower decoration",
        "bridal shower balloons",
        "bridal shower backdrop",
        "bridal shower table decoration",
        "bridal shower flowers",
        "bridal shower party setup"
    ],

    "Corporate Event": [
        "corporate event decoration",
        "corporate event stage",
        "corporate conference decoration",
        "corporate event lighting",
        "corporate event seating",
        "corporate event backdrop",
        "corporate event entrance"
    ],

    "College Event": [
        "college event decoration",
        "college fest decoration",
        "college stage decoration",
        "college event lighting",
        "college event backdrop",
        "college event entrance",
        "college auditorium decoration"
    ],

    "Reception": [
        "wedding reception decoration",
        "reception stage decoration",
        "reception flower decoration",
        "reception lighting",
        "reception entrance decoration",
        "reception table decoration",
        "reception backdrop"
    ],

    "Festival": [
        "festival decoration",
        "festival stage decoration",
        "festival lighting",
        "festival entrance decoration",
        "festival flower decoration",
        "festival event setup"
    ]
}


# ============================================================
# GET EVENT CATEGORIES
# ============================================================

def get_event_categories(event_type):

    if event_type in EVENT_CATEGORIES:

        return EVENT_CATEGORIES[event_type]

    # Generic event

    return [
        f"{event_type} decoration",
        f"{event_type} stage decoration",
        f"{event_type} flower decoration",
        f"{event_type} lighting",
        f"{event_type} entrance decoration",
        f"{event_type} table decoration",
        f"{event_type} event setup"
    ]


# ============================================================
# PERSONALIZED EVENT IMAGE SEARCH
# ============================================================

def get_event_images(
    event_type,
    preferences="",
    color="",
    theme="",
    images_per_category=6,
    max_categories=8
):
    """
    Generate personalized image searches
    based on customer's requirements.
    """

    categories = get_event_categories(
        event_type
    )

    # Limit categories

    categories = categories[
        :max_categories
    ]

    all_photos = []

    # --------------------------------------------------------
    # Build customer-specific keywords
    # --------------------------------------------------------

    customization = []

    if theme.strip():

        customization.append(
            theme.strip()
        )

    if color.strip():

        customization.append(
            f"{color.strip()} color"
        )

    if preferences.strip():

        customization.append(
            preferences.strip()
        )

    # --------------------------------------------------------
    # Search every category
    # --------------------------------------------------------

    for category in categories:

        if customization:

           query = f"{event_type} event decoration {category}"

        else:

            query = category

        photos = search_unsplash_photos(
            query=query,
            per_page=images_per_category,
            page=1
        )

        # Add category information

        for photo in photos:

            photo["category"] = category

            photo["search_query"] = query

            all_photos.append(photo)

    # --------------------------------------------------------
    # Remove duplicate photos
    # --------------------------------------------------------

    unique_photos = {}

    for photo in all_photos:

        photo_id = photo.get("id")

        if photo_id:

            unique_photos[
                photo_id
            ] = photo

    return list(
        unique_photos.values()
    )


# ============================================================
# SEARCH CUSTOM QUERY
# ============================================================

def search_custom_event_images(
    event_type,
    custom_requirement,
    images=20
):
    """
    Search based directly on customer's requirement.
    """

    query = (
        f"{event_type} "
        f"{custom_requirement} "
        f"event decoration"
    )

    return search_unsplash_photos(
        query=query,
        per_page=images
    )
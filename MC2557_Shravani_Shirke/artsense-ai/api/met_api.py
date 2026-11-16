import requests
import pandas as pd


# ==================================================
# THE MET MUSEUM API
# ==================================================

BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"


# ==================================================
# SEARCH ARTWORKS
# ==================================================

def search_met_artworks(query, limit=20):

    print(f"\nSearching The Met API for: {query}")

    search_url = f"{BASE_URL}/search"

    params = {
        "q": query,
        "hasImages": "true"
    }

    try:

        response = requests.get(
            search_url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        object_ids = data.get("objectIDs", [])

        if not object_ids:

            print("No artworks found.")

            return []

        # Limit number of artworks
        object_ids = object_ids[:limit]

        print(
            f"Found {len(object_ids)} artwork IDs."
        )

        artworks = []

        for object_id in object_ids:

            artwork = get_met_artwork(object_id)

            if artwork is not None:

                artworks.append(artwork)

        return artworks

    except Exception as e:

        print(f"Met API error: {e}")

        return []


# ==================================================
# GET SINGLE ARTWORK
# ==================================================

def get_met_artwork(object_id):

    object_url = (
        f"{BASE_URL}/objects/{object_id}"
    )

    try:

        response = requests.get(
            object_url,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        artwork = {

            "source": "Met Museum",

            "api_id": data.get("objectID"),

            "title": data.get(
                "title",
                "Unknown"
            ),

            "artist": data.get(
                "artistDisplayName",
                "Unknown"
            ),

            "yearCreation": data.get(
                "objectDate",
                "Unknown"
            ),

            "period": data.get(
                "period",
                "Unknown"
            ),

            "movement": data.get(
                "culture",
                "Unknown"
            ),

            "medium": data.get(
                "medium",
                "Unknown"
            ),

            "department": data.get(
                "department",
                "Unknown"
            ),

            "country": data.get(
                "country",
                "Unknown"
            ),

            "image_url": data.get(
                "primaryImageSmall",
                ""
            ),

            "description": data.get(
                "creditLine",
                "Unknown"
            )
        }

        return artwork

    except Exception as e:

        print(
            f"Error getting artwork "
            f"{object_id}: {e}"
        )

        return None


# ==================================================
# CONVERT RESULTS TO DATAFRAME
# ==================================================

def met_results_to_dataframe(artworks):

    if not artworks:

        return pd.DataFrame()

    df = pd.DataFrame(artworks)

    return df


# ==================================================
# TEST API
# ==================================================

if __name__ == "__main__":

    print("=" * 60)

    print("TESTING THE MET MUSEUM API")

    print("=" * 60)

    artworks = search_met_artworks(
        query="painting",
        limit=10
    )

    df = met_results_to_dataframe(
        artworks
    )

    print("\nDATA RECEIVED:")

    print(df.head())

    print("\nDataset shape:")

    print(df.shape)
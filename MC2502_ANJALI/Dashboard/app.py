from pathlib import Path
import csv
import sys
import tempfile
import math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import traceback
# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shrimp_resnet_predict import ShrimpDiseaseClassifier


from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)


# ============================================================
# PROJECT PATHS
# ============================================================

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
FUSION_DIR = DATA_DIR / "fusion_analytics"

MODELS_DIR = PROJECT_ROOT / "models"
SRC_DIR = PROJECT_ROOT / "src"


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static"),
)


# ============================================================
# IMPORT MAIN AI
# ============================================================

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ============================================================
# SHRIMP DISEASE MODEL
# ============================================================

# ============================================================
# SHRIMP DISEASE MODEL
# ============================================================

SHRIMP_DISEASE_AVAILABLE = False
shrimp_classifier = None

try:

    shrimp_classifier = ShrimpDiseaseClassifier()

    SHRIMP_DISEASE_AVAILABLE = True

    print(
        "Shrimp disease model available."
    )

except Exception as error:

    SHRIMP_DISEASE_AVAILABLE = False

    shrimp_classifier = None

    print(
        "Shrimp disease classifier unavailable:",
        type(error).__name__ + ":",
        error
    )

NOAA_OCEAN_AVAILABLE = False
NOAA_OCEAN_ERROR = None

try:
    from noaa_utils import get_ocean_environment_for_occurrences
    NOAA_OCEAN_AVAILABLE = True
except Exception as exc:
    NOAA_OCEAN_ERROR = f"{type(exc).__name__}: {exc}"


MAIN_AI_AVAILABLE = True
MAIN_AI_ERROR = None

CONTEXT_REASONING_AVAILABLE = True
CONTEXT_REASONING_ERROR = None

try:

    from predict import FishClassifier

    from vit_predict import ViTClassifier

    from llm_chain import (
        generate_fish_info,
        ask_followup
    )

except Exception as exc:

    MAIN_AI_AVAILABLE = False

    MAIN_AI_ERROR = (
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================
# ViT / I-JEPA MODEL STATE
# ============================================================

VIT_AVAILABLE = True
VIT_ERROR = None
vit_classifier = None

IJEPA_AVAILABLE = True
IJEPA_ERROR = None
ijepa_classifier = None


def get_vit_classifier():

    global VIT_AVAILABLE
    global VIT_ERROR
    global vit_classifier

    if vit_classifier is not None:
        return vit_classifier

    if not MAIN_AI_AVAILABLE:
        VIT_AVAILABLE = False
        VIT_ERROR = MAIN_AI_ERROR
        return None

    try:

        vit_classifier = ViTClassifier()

        VIT_AVAILABLE = True

        print(
            "ViT classifier loaded successfully."
        )

        return vit_classifier

    except Exception as exc:

        VIT_AVAILABLE = False

        VIT_ERROR = (
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "ViT classifier unavailable:",
            VIT_ERROR
        )

        return None


def get_ijepa_classifier():

    global IJEPA_AVAILABLE
    global IJEPA_ERROR
    global ijepa_classifier

    if ijepa_classifier is not None:
        return ijepa_classifier

    try:

        from ijepa_predict import IJEPAClassifier

        print(
            "Loading I-JEPA classifier..."
        )

        ijepa_classifier = (
            IJEPAClassifier()
        )

        IJEPA_AVAILABLE = True

        print(
            "I-JEPA classifier loaded successfully."
        )

        return ijepa_classifier

    except Exception as exc:

        IJEPA_AVAILABLE = False

        IJEPA_ERROR = (
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "I-JEPA classifier unavailable:",
            IJEPA_ERROR
        )

        return None


try:

    from context_reasoning import (
        generate_context_reasoning
    )

except Exception as exc:

    CONTEXT_REASONING_AVAILABLE = False

    CONTEXT_REASONING_ERROR = (
        f"{type(exc).__name__}: {exc}"
    )
# ============================================================
# OPTIONAL ORIGINAL EXPLORE-MORE MODULES
# ============================================================

GBIF_MODULE_AVAILABLE = False
NUTRITION_MODULE_AVAILABLE = False
WEATHER_MODULE_AVAILABLE = False
MARKET_MODULE_AVAILABLE = False

try:
    from species_mapping import get_species_info
except Exception:
    get_species_info = None

try:
    from gbif_utils import (
        verify_species,
        get_distribution,
        get_available_countries,
    )
    GBIF_MODULE_AVAILABLE = True
except Exception:
    verify_species = None
    get_distribution = None
    get_available_countries = None

try:
    from nutrition_utils import get_nutrition_facts
    NUTRITION_MODULE_AVAILABLE = True
except Exception:
    get_nutrition_facts = None

try:
    from weather_utils import (
        get_weather,
        get_weather_by_coords,
        get_forecast_by_coords,
        is_favorable,
        find_next_favorable_window,
        fishing_condition_note,
    )
    WEATHER_MODULE_AVAILABLE = True
except Exception:
    get_weather = None
    get_weather_by_coords = None
    get_forecast_by_coords = None
    is_favorable = None
    find_next_favorable_window = None
    fishing_condition_note = None

try:
    from market_finder import (
        find_nearby_seafood_places,
        reverse_geocode,
    )
    MARKET_MODULE_AVAILABLE = True
except Exception:
    find_nearby_seafood_places = None
    reverse_geocode = None


# ============================================================
# MODEL
# ============================================================

MODEL_PATH = (
    MODELS_DIR / "fish_classifier.h5"
)

CLASS_INDICES_PATH = (
    MODELS_DIR / "class_indices.json"
)

classifier = None

if MAIN_AI_AVAILABLE:

    try:

        classifier = FishClassifier(
            str(MODEL_PATH),
            str(CLASS_INDICES_PATH),
        )

    except Exception as exc:

        MAIN_AI_AVAILABLE = False

        MAIN_AI_ERROR = (
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# DATA FILES
# ============================================================

API_METADATA_FILE = (
    FUSION_DIR / "api_fusion_metadata.csv"
)

FINAL_FUSION_FILE = (
    FUSION_DIR / "final_fusion_dataset.csv"
)

GBIF_DISTRIBUTION_FILE = (
    FUSION_DIR / "gbif_distribution.csv"
)

FUSION_RESULTS_FILE = (
    FUSION_DIR / "fusion_results.csv"
)

IMAGE_METADATA_FILE = (
    DATA_DIR / "fusion_metadata.csv"
)

AI_LOG_FILE = (
    FUSION_DIR / "ai_interactions.csv"
)


# ============================================================
# FISH FEATURE GROUPS
# ============================================================

GBIF_FEATURES = [

    "gbif_taxon_key",
    "gbif_canonical_name",
    "gbif_confidence",
    "gbif_occurrence_count",
    "gbif_country_count",
    "gbif_coordinate_count",
    "gbif_top_country",
    "gbif_top_country_records",
    "gbif_status",

]

USDA_FEATURES = [

    "usda_fdc_id",
    "usda_description",
    "usda_calories",
    "usda_protein",
    "usda_fat",
    "usda_carbohydrate",
    "usda_status",

]

WEATHER_FEATURES = [

    "weather_temperature",
    "weather_humidity",
    "weather_pressure",
    "weather_wind_speed",
    "weather_clouds",
    "weather_description",
    "weather_location",
    "weather_status",

]

ALL_FISH_FEATURES = (
    GBIF_FEATURES
    + USDA_FEATURES
    + WEATHER_FEATURES
)


# ============================================================
# KNOWN SCIENTIFIC NAMES
# ============================================================

SCIENTIFIC_NAMES = {

    "Type 1 Pomfret":
        "Pampus argenteus",

    "Type 3 Black Snapper":
        "Apsilus dentatus",

    "Type 4 Indian Carp":
        "Labeo rohita",

    "Type 5 Prawn":
        "Penaeus indicus",

    "Type 6 Pink Perch":
        "Zalembius rosaceus",

    "Type 8 Black Pomfret":
        "Parastromateus niger",

}


# ============================================================
# DATA CACHE
# ============================================================

api_df = pd.DataFrame()
fusion_df = pd.DataFrame()
gbif_df = pd.DataFrame()
results_df = pd.DataFrame()
image_df = pd.DataFrame()


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    global api_df
    global fusion_df
    global gbif_df
    global results_df
    global image_df

    print()
    print("=" * 70)
    print("LOADING FISH AI MULTIMODAL ANALYTICS DATA")
    print("=" * 70)

    if API_METADATA_FILE.exists():

        api_df = pd.read_csv(
            API_METADATA_FILE
        )

    else:

        api_df = pd.DataFrame()

    if FINAL_FUSION_FILE.exists():

        fusion_df = pd.read_csv(
            FINAL_FUSION_FILE
        )

    else:

        fusion_df = pd.DataFrame()

    if GBIF_DISTRIBUTION_FILE.exists():

        gbif_df = pd.read_csv(
            GBIF_DISTRIBUTION_FILE
        )

    else:

        gbif_df = pd.DataFrame()

    if FUSION_RESULTS_FILE.exists():

        results_df = pd.read_csv(
            FUSION_RESULTS_FILE
        )

    else:

        results_df = pd.DataFrame()

    if IMAGE_METADATA_FILE.exists():

        image_df = pd.read_csv(
            IMAGE_METADATA_FILE
        )

    else:

        image_df = pd.DataFrame()

    print(
        "API metadata:",
        api_df.shape
    )

    print(
        "Final fusion dataset:",
        fusion_df.shape
    )

    print(
        "GBIF distribution:",
        gbif_df.shape
    )

    print(
        "Fusion results:",
        results_df.shape
    )

    print(
        "Image metadata:",
        image_df.shape
    )

    print("=" * 70)


load_data()


# ============================================================
# SAFE JSON
# ============================================================

def clean_value(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    if isinstance(
        value,
        np.integer
    ):

        return int(value)

    if isinstance(
        value,
        np.floating
    ):

        if not np.isfinite(value):
            return None

        return float(value)

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return float(value)

    return value


def dataframe_records(df):

    if df is None or df.empty:
        return []

    records = []

    for row in df.to_dict(
        orient="records"
    ):

        records.append({
            key: clean_value(value)
            for key, value in row.items()
        })

    return records


# ============================================================
# MAP COORDINATES
# ============================================================
# Keep the existing OpenStreetMap/Leaflet frontend intact.
# This helper makes GBIF coordinate field names consistent so
# the map continues to work even when the CSV/API uses:
# latitude/longitude, lat/lon, decimalLatitude/decimalLongitude,
# decimal_latitude/decimal_longitude, or lng.
# ============================================================

def normalize_map_coordinates(row):
    """
    Return validated latitude/longitude for the OpenStreetMap map.

    Supports the coordinate field names commonly found in the
    GBIF export and the existing dashboard dataset.
    """

    latitude_keys = [
        "latitude",
        "lat",
        "decimalLatitude",
        "decimal_latitude",
    ]

    longitude_keys = [
        "longitude",
        "lon",
        "lng",
        "decimalLongitude",
        "decimal_longitude",
    ]

    latitude = None
    longitude = None

    for key in latitude_keys:
        if key in row:
            value = clean_value(row.get(key))

            if value is not None:
                try:
                    latitude = float(value)
                    break
                except (TypeError, ValueError):
                    pass

    for key in longitude_keys:
        if key in row:
            value = clean_value(row.get(key))

            if value is not None:
                try:
                    longitude = float(value)
                    break
                except (TypeError, ValueError):
                    pass

    if latitude is None or longitude is None:
        return None

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
    ):
        return None

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        return None

    return {
        "latitude": latitude,
        "longitude": longitude,
        # Keep these aliases because the existing Leaflet
        # frontend may use either naming convention.
        "lat": latitude,
        "lon": longitude,
    }


def gbif_map_records(df):
    """
    Convert GBIF records into clean map-ready records while
    preserving all original fields.

    OpenStreetMap itself does not require an API key. The map
    needs valid latitude/longitude values from this endpoint.
    """

    if df is None or df.empty:
        return []

    records = []

    for row in df.to_dict(orient="records"):

        cleaned = {
            key: clean_value(value)
            for key, value in row.items()
        }

        coordinates = normalize_map_coordinates(cleaned)

        if coordinates is None:
            continue

        # Preserve the original record and add normalized fields.
        cleaned.update(coordinates)

        records.append(cleaned)

    return records


# ============================================================
# SPECIES
# ============================================================

def get_species_list():

    if (
        fusion_df.empty
        or "species" not in fusion_df.columns
    ):
        return []

    return sorted(
        fusion_df["species"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )


# ============================================================
# AI LOG
# ============================================================

def get_prediction_log():

    if not AI_LOG_FILE.exists():
        return pd.DataFrame()

    try:

        return pd.read_csv(
            AI_LOG_FILE
        )

    except Exception:

        return pd.DataFrame()


def log_ai_event(
    event_type,
    species="",
    confidence=None,
    question="",
    answer="",
    language="en",
):

    FUSION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    row = {

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "event_type":
            event_type,

        "species":
            species,

        "confidence":
            confidence,

        "question":
            question,

        "answer":
            answer,

        "language":
            language,

        "question_length":
            len(question or ""),

        "answer_length":
            len(answer or ""),

    }

    exists = AI_LOG_FILE.exists()

    with open(
        AI_LOG_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=row.keys(),
        )

        if not exists:
            writer.writeheader()

        writer.writerow(row)


# ============================================================
# FIND FUSED SPECIES RECORD
# ============================================================

def get_fish_fusion_record(
    species
):

    if (
        fusion_df.empty
        or "species" not in fusion_df.columns
    ):

        return pd.DataFrame()

    species = str(
        species
    ).strip()

    df = fusion_df[
        fusion_df["species"]
        .astype(str)
        .str.strip()
        .str.lower()
        == species.lower()
    ].copy()

    return df


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return render_template(
        "dashboard.html",
        dataset_rows=len(fusion_df),
        species_count=len(
            get_species_list()
        ),
        api_available=not api_df.empty,
        main_ai_available=MAIN_AI_AVAILABLE,
    )


# ============================================================
# SUMMARY
# ============================================================

@app.route("/api/summary")
def summary():

    log_df = get_prediction_log()

    prediction_count = 0
    qa_count = 0

    if not log_df.empty:

        if "event_type" in log_df.columns:

            prediction_count = int(
                (
                    log_df["event_type"]
                    == "prediction"
                ).sum()
            )

            qa_count = int(
                (
                    log_df["event_type"]
                    == "qa"
                ).sum()
            )

    return jsonify({

        "success": True,

        "dataset_images":
            int(len(fusion_df)),

        "species":
            len(get_species_list()),

        "feature_count":
            int(
                len(fusion_df.columns)
            )
            if not fusion_df.empty
            else 0,

        "api_feature_count":
            len([
                x
                for x in ALL_FISH_FEATURES
                if x in fusion_df.columns
            ]),

        "prediction_count":
            prediction_count,

        "qa_count":
            qa_count,

        "main_ai_available":
            MAIN_AI_AVAILABLE,

        "api_sources": [

            "GBIF",
            "USDA FoodData Central",
            "Weather API",
            "OpenStreetMap",
            "FAISS + Google Embeddings",
            "Google Gemini",

        ],

    })


# ============================================================
# SPECIES DISTRIBUTION
# ============================================================

@app.route(
    "/api/species-distribution"
)
def species_distribution():

    if (
        fusion_df.empty
        or "species" not in fusion_df.columns
    ):

        return jsonify([])

    result = (
        fusion_df["species"]
        .astype(str)
        .value_counts()
        .rename_axis("species")
        .reset_index(
            name="images"
        )
    )

    return jsonify(
        dataframe_records(result)
    )


# ============================================================
# FUSED DATASET
# ============================================================

@app.route("/api/fused-data")
def fused_data():

    if fusion_df.empty:

        return jsonify({

            "rows": [],
            "total": 0,
            "columns": [],

        })

    try:

        page = max(
            int(
                request.args.get(
                    "page",
                    1
                )
            ),
            1,
        )

        page_size = min(
            max(
                int(
                    request.args.get(
                        "page_size",
                        25
                    )
                ),
                1,
            ),
            100,
        )

    except ValueError:

        page = 1
        page_size = 25

    species = request.args.get(
        "species",
        "All"
    )

    split = request.args.get(
        "split",
        "All"
    )

    search = request.args.get(
        "search",
        ""
    ).strip().lower()

    df = fusion_df.copy()

    if (
        species != "All"
        and "species" in df.columns
    ):

        df = df[
            df["species"]
            .astype(str)
            .str.strip()
            == species
        ]

    if (
        split != "All"
        and "split" in df.columns
    ):

        df = df[
            df["split"]
            .astype(str)
            == split
        ]

    if search:

        mask = pd.Series(
            False,
            index=df.index
        )

        for column in df.columns:

            try:

                mask |= (
                    df[column]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        search,
                        na=False
                    )
                )

            except Exception:
                pass

        df = df[mask]

    total = len(df)

    start = (
        page - 1
    ) * page_size

    end = start + page_size

    page_df = df.iloc[
        start:end
    ]

    return jsonify({

        "rows":
            dataframe_records(
                page_df
            ),

        "total":
            int(total),

        "page":
            page,

        "page_size":
            page_size,

        "columns":
            list(fusion_df.columns),

    })


# ============================================================
# REAL-TIME DATASET EDA
# ============================================================

@app.route("/api/eda")
def eda():

    species = request.args.get(
        "species",
        "All"
    )

    df = fusion_df.copy()

    if (
        species != "All"
        and "species" in df.columns
    ):

        df = df[
            df["species"]
            .astype(str)
            .str.strip()
            == species
        ]

    result = {

        "rows":
            int(len(df)),

        "species": [],

        "split": [],

        "numeric": [],

    }

    if "species" in df.columns:

        result["species"] = dataframe_records(

            df["species"]
            .value_counts()
            .rename_axis("species")
            .reset_index(
                name="count"
            )

        )

    if "split" in df.columns:

        result["split"] = dataframe_records(

            df["split"]
            .value_counts()
            .rename_axis("split")
            .reset_index(
                name="count"
            )

        )

    numeric_columns = list(
        df.select_dtypes(
            include=np.number
        ).columns
    )

    for column in numeric_columns:

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if values.empty:
            continue

        result["numeric"].append({

            "feature":
                column,

            "mean":
                float(values.mean()),

            "median":
                float(values.median()),

            "min":
                float(values.min()),

            "max":
                float(values.max()),

        })

    return jsonify(result)


# ============================================================
# ============================================================
# FISH-SPECIFIC FEATURE EDA
# THIS IS THE IMPORTANT NEW ENDPOINT
# ============================================================
# ============================================================

@app.route(
    "/api/fish-feature-eda"
)
def fish_feature_eda():

    species = request.args.get(
        "species",
        ""
    ).strip()

    if not species:

        return jsonify({

            "success": False,

            "error":
                "Species is required."

        }), 400

    if fusion_df.empty:

        return jsonify({

            "success": False,

            "error":
                "Final fusion dataset is empty."

        }), 500

    fish_df = get_fish_fusion_record(
        species
    )

    if fish_df.empty:

        return jsonify({

            "success": False,

            "error":
                f"No fused evidence found for {species}."

        }), 404

@app.route(
    "/api/shrimp-disease/predict",
    methods=["POST"]
)
def shrimp_disease_predict():

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    if not SHRIMP_DISEASE_AVAILABLE:

        return jsonify({
            "success": False,
            "error": "Shrimp disease model is unavailable."
        }), 503

    # --------------------------------------------------------
    # Check uploaded image
    # --------------------------------------------------------

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "error": "No image was uploaded."
        }), 400

    file = request.files["image"]

    if file.filename == "":

        return jsonify({
            "success": False,
            "error": "No image was selected."
        }), 400

    # --------------------------------------------------------
    # Save temporary image
    # --------------------------------------------------------

    temporary_path = None

    try:

        import tempfile

        suffix = Path(
            file.filename
        ).suffix.lower()

        if suffix not in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]:

            return jsonify({
                "success": False,
                "error": (
                    "Invalid image format. "
                    "Use JPG, JPEG, PNG or WEBP."
                )
            }), 400

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temporary_file:

            file.save(
                temporary_file.name
            )

            temporary_path = Path(
                temporary_file.name
            )

        # ----------------------------------------------------
        # Run ResNet18
        # ----------------------------------------------------

        result = shrimp_classifier.predict(
            temporary_path
        )

        # ----------------------------------------------------
        # Return prediction
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "prediction":
                result["prediction"],

            "confidence":
                result["confidence"],

            "healthy_probability":
                result["healthy_probability"],

            "diseased_probability":
                result["diseased_probability"]

        })

    except Exception as error:

        print(
            "Shrimp disease prediction error:",
            type(error).__name__,
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Shrimp disease prediction failed: "
                + str(error)

        }), 500

    finally:

        # ----------------------------------------------------
        # Delete temporary image
        # ----------------------------------------------------

        if (
            temporary_path is not None
            and temporary_path.exists()
        ):

            try:

                temporary_path.unlink()

            except Exception:

                pass

    # --------------------------------------------------------
    # IMPORTANT:
    # We do NOT use image pixels.
    # We use species-associated multimodal features.
    # --------------------------------------------------------

    # One species-level record is enough because the API
    # features are species-associated.
    row = fish_df.iloc[0]

    # --------------------------------------------------------
    # GROUPED FEATURES
    # --------------------------------------------------------

    def build_group(
        feature_names
    ):

        output = []

        for feature in feature_names:

            if feature not in row.index:
                continue

            value = clean_value(
                row[feature]
            )

            output.append({

                "feature":
                    feature,

                "label":
                    feature.replace(
                        "_",
                        " "
                    ).title(),

                "value":
                    value,

            })

        return output

    gbif = build_group(
        GBIF_FEATURES
    )

    usda = build_group(
        USDA_FEATURES
    )

    weather = build_group(
        WEATHER_FEATURES
    )

    # --------------------------------------------------------
    # NUMERIC FEATURE STATISTICS
    # --------------------------------------------------------

    numeric_features = []

    for feature in ALL_FISH_FEATURES:

        if feature not in row.index:
            continue

        value = row[feature]

        try:

            number = float(value)

        except (
            TypeError,
            ValueError
        ):

            continue

        if not math.isfinite(number):
            continue

        numeric_features.append({

            "feature":
                feature,

            "label":
                feature.replace(
                    "_",
                    " "
                ).title(),

            "value":
                number,

            "mean":
                float(
                    pd.to_numeric(
                        fish_df[feature],
                        errors="coerce"
                    ).mean()
                ),

            "minimum":
                float(
                    pd.to_numeric(
                        fish_df[feature],
                        errors="coerce"
                    ).min()
                ),

            "maximum":
                float(
                    pd.to_numeric(
                        fish_df[feature],
                        errors="coerce"
                    ).max()
                ),

        })

    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    availability = []

    for feature in ALL_FISH_FEATURES:

        if feature not in row.index:

            availability.append({

                "feature":
                    feature,

                "available":
                    False,

            })

            continue

        value = row[feature]

        try:

            available = (
                not pd.isna(value)
            )

        except Exception:

            available = (
                value is not None
            )

        availability.append({

            "feature":
                feature,

            "available":
                bool(available),

        })

    # --------------------------------------------------------
    # GBIF LOCATION DATA
    # --------------------------------------------------------

    locations = []

    if not gbif_df.empty:

        temp = gbif_df.copy()

        if "species" in temp.columns:

            temp = temp[
                temp["species"]
                .astype(str)
                .str.strip()
                .str.lower()
                == species.lower()
            ]

        for _, location in temp.iterrows():

            # Normalize GBIF coordinates using the same logic
            # as the OpenStreetMap distribution endpoint.
            coordinates = normalize_map_coordinates(
                {
                    key: clean_value(value)
                    for key, value in location.items()
                }
            )

            if coordinates is None:
                continue

            latitude = coordinates["latitude"]
            longitude = coordinates["longitude"]

            locations.append({

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "country":
                    clean_value(
                        location.get(
                            "country"
                        )
                    ),

                "country_code":
                    clean_value(
                        location.get(
                            "country_code"
                        )
                    ),

            })

    # --------------------------------------------------------
    # COUNTRY COUNTS
    # --------------------------------------------------------

    country_counts = {}

    for location in locations:

        country = (
            location.get(
                "country"
            )
            or "Unknown"
        )

        country_counts[country] = (
            country_counts.get(
                country,
                0
            ) + 1
        )

    countries = [

        {
            "country":
                country,

            "records":
                count,

        }

        for country, count
        in sorted(
            country_counts.items(),
            key=lambda item:
                item[1],
            reverse=True,
        )

    ]

    # --------------------------------------------------------
    # SCIENTIFIC NAME
    # --------------------------------------------------------

    scientific_name = (
        SCIENTIFIC_NAMES.get(
            species,
            "Not available"
        )
    )

    if get_species_info:

        try:

            info = get_species_info(
                species
            )

            if info:

                scientific_name = (
                    info.get(
                        "scientific_name"
                    )
                    or scientific_name
                )

        except Exception:
            pass

    # --------------------------------------------------------
    # INTERPRETATION
    # --------------------------------------------------------

    interpretation = []

    def numeric_value(
        feature
    ):

        for item in numeric_features:

            if (
                item["feature"]
                == feature
            ):

                return item["value"]

        return None

    occurrence = numeric_value(
        "gbif_occurrence_count"
    )

    country_count = numeric_value(
        "gbif_country_count"
    )

    coordinates = numeric_value(
        "gbif_coordinate_count"
    )

    calories = numeric_value(
        "usda_calories"
    )

    protein = numeric_value(
        "usda_protein"
    )

    fat = numeric_value(
        "usda_fat"
    )

    carbohydrate = numeric_value(
        "usda_carbohydrate"
    )

    temperature = numeric_value(
        "weather_temperature"
    )

    humidity = numeric_value(
        "weather_humidity"
    )

    if occurrence is not None:

        interpretation.append(
            f"GBIF evidence contains "
            f"{occurrence:,.0f} occurrence records "
            f"associated with this species."
        )

    if country_count is not None:

        interpretation.append(
            f"The retrieved GBIF evidence covers "
            f"approximately {country_count:,.0f} countries."
        )

    if coordinates is not None:

        interpretation.append(
            f"{coordinates:,.0f} coordinate records "
            f"are represented in the available biodiversity evidence."
        )

    if calories is not None:

        interpretation.append(
            f"The USDA-linked nutritional record reports "
            f"{calories:.2f} kcal per 100 g."
        )

    if protein is not None:

        interpretation.append(
            f"The USDA-linked nutritional record reports "
            f"{protein:.2f} g protein per 100 g."
        )

    if fat is not None:

        interpretation.append(
            f"The reported fat value is "
            f"{fat:.2f} g per 100 g."
        )

    if carbohydrate is not None:

        interpretation.append(
            f"The reported carbohydrate value is "
            f"{carbohydrate:.2f} g per 100 g."
        )

    if temperature is not None:

        interpretation.append(
            f"The associated weather record reports "
            f"a temperature of {temperature:.2f}."
        )

    if humidity is not None:

        interpretation.append(
            f"The associated weather record reports "
            f"humidity of {humidity:.2f}%."
        )

    return jsonify({

        "success":
            True,

        "species":
            species,

        "scientific_name":
            scientific_name,

        "records":
            int(len(fish_df)),

        "gbif":
            gbif,

        "usda":
            usda,

        "weather":
            weather,

        "numeric_features":
            numeric_features,

        "availability":
            availability,

        "locations":
            locations,

        "countries":
            countries,

        "interpretation":
            interpretation,

    })


# ============================================================
# FISH FACT-CHECK / EVIDENCE
# ============================================================

@app.route(
    "/api/fish-evidence"
)
def fish_evidence():

    species = request.args.get(
        "species",
        ""
    ).strip()

    if not species:

        return jsonify({

            "success": False,

            "error":
                "Species is required."

        }), 400

    fish_df = get_fish_fusion_record(
        species
    )

    if fish_df.empty:

        return jsonify({

            "success": False,

            "error":
                f"No evidence found for {species}."

        }), 404

    row = fish_df.iloc[0]

    groups = {

        "GBIF":
            {},

        "USDA":
            {},

        "Weather":
            {},

    }

    for feature in GBIF_FEATURES:

        if feature in row.index:

            groups["GBIF"][feature] = (
                clean_value(
                    row[feature]
                )
            )

    for feature in USDA_FEATURES:

        if feature in row.index:

            groups["USDA"][feature] = (
                clean_value(
                    row[feature]
                )
            )

    for feature in WEATHER_FEATURES:

        if feature in row.index:

            groups["Weather"][feature] = (
                clean_value(
                    row[feature]
                )
            )

    all_features = {}

    for group in groups.values():

        all_features.update(
            group
        )

    return jsonify({

        "success":
            True,

        "species":
            species,

        "groups":
            groups,

        "all_features":
            all_features,

    })


# ============================================================
# CONTEXT-AWARE REASONING
# ============================================================

@app.route(
    "/api/context-reasoning"
)
def context_reasoning_api():

    species = request.args.get(
        "species",
        ""
    ).strip()

    confidence = request.args.get(
        "confidence",
        "0"
    )

    if not species:

        return jsonify({
            "success": False,
            "error":
                "Species is required."
        }), 400

    try:

        try:

            confidence_value = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence_value = 0.0

        # --------------------------------------------------------
        # OPTIONAL CURRENT WEATHER CONDITIONS
        # --------------------------------------------------------

        current_conditions = {}

        request_mapping = {

            "temperature":
                "temperature",

            "humidity":
                "humidity",

            "pressure":
                "pressure",

            "wind_speed":
                "wind_speed",

            "clouds":
                "clouds",

        }

        for (
            request_key,
            condition_key
        ) in request_mapping.items():

            value = request.args.get(
                request_key
            )

            if value is None:
                continue

            try:

                current_conditions[
                    condition_key
                ] = float(value)

            except (
                TypeError,
                ValueError
            ):

                continue

        # --------------------------------------------------------
        # RUN EXISTING CONTEXT REASONING
        # --------------------------------------------------------

        result = generate_context_reasoning(

            species=
                species,

            confidence=
                confidence_value,

            fusion_df=
                fusion_df,

            current_conditions=
                current_conditions,

        )

        if not isinstance(result, dict):
            result = {
                "success": False,
                "species": species,
                "cnn_confidence": confidence_value,
                "overall_status": "insufficient_context",
                "overall_label": "Insufficient environmental evidence",
                "reasoning": [],
                "reasoning_text": "Context reasoning returned no structured result.",
                "error": "Context reasoning returned None or an invalid result."
            }

        # --------------------------------------------------------
        # NOAA OCEAN ENVIRONMENT
        # --------------------------------------------------------

        ocean_environment = {

            "source":
                "NOAA World Ocean Atlas 2023",

            "checked_locations":
                0,

            "usable_locations":
                0,

            "temperature":
                None,

            "salinity":
                None,

            "temperature_range":
                None,

            "salinity_range":
                None,

            "temperature_values":
                [],

            "salinity_values":
                [],

            "temperature_available":
                False,

            "salinity_available":
                False,

            "temperature_locations":
                [],

            "salinity_locations":
                [],

        }

        if NOAA_OCEAN_AVAILABLE:

            try:

                # ------------------------------------------------
                # GET GBIF OCCURRENCES FOR THIS SPECIES
                # ------------------------------------------------

                gbif_occurrences = []

                if (
                    not gbif_df.empty
                    and
                    "species"
                    in gbif_df.columns
                ):

                    species_gbif = (
                        gbif_df[
                            gbif_df["species"]
                            .astype(str)
                            .str.strip()
                            .str.lower()
                            ==
                            species.lower()
                        ]
                        .copy()
                    )

                    gbif_occurrences = (
                        dataframe_records(
                            species_gbif
                        )
                    )

                # ------------------------------------------------
                # QUERY NOAA
                # ------------------------------------------------

                if gbif_occurrences:

                    noaa_result = get_ocean_environment_for_occurrences(
                        gbif_occurrences,
                        max_locations=25
                    )

                    if isinstance(noaa_result, dict):
                        ocean_environment = noaa_result
                    else:
                        ocean_environment["error"] = (
                            "NOAA returned no structured environment result."
                        )

            except Exception as ocean_error:

                print(
                    "NOAA ocean environment error:",
                    ocean_error
                )

        # --------------------------------------------------------
        # ADD NOAA INFORMATION TO RESULT
        # --------------------------------------------------------

        if isinstance(result, dict):
            result["ocean_environment"] = ocean_environment

            reasoning_points = result.get("reasoning")
            if not isinstance(reasoning_points, list):
                reasoning_points = []

            checked = ocean_environment.get("checked_locations", 0)
            temp = ocean_environment.get("temperature")
            salinity = ocean_environment.get("salinity")
            temp_range = ocean_environment.get("temperature_range")
            salinity_range = ocean_environment.get("salinity_range")

            if checked:
                reasoning_points.append(
                    f"GBIF/NOAA evidence: NOAA World Ocean Atlas 2023 was checked at {checked} sampled GBIF occurrence locations."
                )

            if temp is not None:
                if isinstance(temp_range, dict):
                    tmin = temp_range.get("min", temp)
                    tmax = temp_range.get("max", temp)
                    reasoning_points.append(
                        f"Water temperature: NOAA mean {float(temp):.2f} °C; observed range {float(tmin):.2f}–{float(tmax):.2f} °C."
                    )
                else:
                    reasoning_points.append(
                        f"Water temperature: NOAA value {float(temp):.2f} °C."
                    )
            else:
                reasoning_points.append(
                    "Water temperature: no usable NOAA value was returned for the sampled occurrence locations."
                )

            if salinity is not None:
                if isinstance(salinity_range, dict):
                    smin = salinity_range.get("min", salinity)
                    smax = salinity_range.get("max", salinity)
                    reasoning_points.append(
                        f"Salinity: NOAA mean {float(salinity):.2f} PSU; observed range {float(smin):.2f}–{float(smax):.2f} PSU."
                    )
                else:
                    reasoning_points.append(
                        f"Salinity: NOAA value {float(salinity):.2f} PSU."
                    )
            else:
                reasoning_points.append(
                    "Salinity: no usable NOAA value was returned for the sampled occurrence locations."
                )

            # Expose NOAA values through the evidence structure already
            # consumed by the existing dashboard renderer.
            api_evidence = result.get("api_evidence")
            if not isinstance(api_evidence, dict):
                api_evidence = {}

            if temp is not None:
                api_evidence["water_temperature"] = f"{float(temp):.2f} °C"
            else:
                api_evidence["water_temperature"] = "No usable NOAA value returned"

            if isinstance(temp_range, dict):
                api_evidence["water_temperature_range"] = (
                    f"{temp_range.get('min')}–{temp_range.get('max')} °C"
                )

            if salinity is not None:
                api_evidence["salinity"] = f"{float(salinity):.2f} PSU"
            else:
                api_evidence["salinity"] = "No usable NOAA value returned"

            if isinstance(salinity_range, dict):
                api_evidence["salinity_range"] = (
                    f"{salinity_range.get('min')}–{salinity_range.get('max')} PSU"
                )

            api_evidence["noaa_source"] = ocean_environment.get(
                "source", "NOAA World Ocean Atlas 2023"
            )
            api_evidence["noaa_locations_checked"] = checked
            result["api_evidence"] = api_evidence

            result["reasoning_points"] = reasoning_points
            result["reasoning"] = "\n".join(
                "• " + str(point)
                for point in reasoning_points
            )
            result["reasoning_text"] = result["reasoning"]

        return jsonify(
            result
        )

    except Exception as exc:

        print(
            "Context reasoning error:",
            type(exc).__name__,
            exc
        )

        return jsonify({

            "success":
                False,

            "error":
                f"{type(exc).__name__}: {exc}",

        }), 500
# ============================================================
# MAIN AI — PREDICT
# ============================================================

@app.route(
    "/api/main-ai/predict",
    methods=["POST"]
)
def main_ai_predict():

    if (
        not MAIN_AI_AVAILABLE
        or classifier is None
    ):

        return jsonify({

            "success":
                False,

            "error":
                "Main AI model is unavailable.",

            "details":
                MAIN_AI_ERROR,

        }), 500

    if "image" not in request.files:

        return jsonify({

            "success":
                False,

            "error":
                "No image uploaded.",

        }), 400

    uploaded = request.files[
        "image"
    ]

    if not uploaded.filename:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid image.",

        }), 400

    language = request.form.get(
        "language",
        "en"
    )

    suffix = Path(
        uploaded.filename
    ).suffix.lower()

    if suffix not in [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    ]:

        suffix = ".jpg"

    temp_path = None

    try:

        # ----------------------------------------------------
        # SAVE TEMP IMAGE
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as tmp:

            uploaded.save(
                tmp.name
            )

            temp_path = tmp.name

        # ----------------------------------------------------
        # CNN
        # ----------------------------------------------------

        label, confidence, top3 = (
            classifier.predict(
                temp_path
            )
        )

        # ============================================================
        # ViT PREDICTION
        # ============================================================

        vit_label = None
        vit_confidence = None
        vit_top3 = []
        vit_error = None

        vit_model = get_vit_classifier()

        if vit_model is not None:

            try:

                (
                    vit_label,
                    vit_confidence,
                    vit_top3
                ) = vit_model.predict(
                    temp_path
                )

            except Exception as exc:

                vit_error = (
                    f"{type(exc).__name__}: {exc}"
                )

                print(
                    "ViT prediction error:",
                    vit_error
                )

        else:

            vit_error = VIT_ERROR


        # ============================================================
        # I-JEPA PREDICTION
        # ============================================================

        ijepa_label = None
        ijepa_confidence = None
        ijepa_top3 = []
        ijepa_error = None

        ijepa_model = get_ijepa_classifier()

        if ijepa_model is not None:

            try:

                (
                    ijepa_label,
                    ijepa_confidence,
                    ijepa_top3
                ) = ijepa_model.predict(
                    temp_path
                )

            except Exception as exc:

                ijepa_error = (
                    f"{type(exc).__name__}: {exc}"
                )

                print(
                    "I-JEPA prediction error:",
                    ijepa_error
                )

        else:

            ijepa_error = IJEPA_ERROR


        # ----------------------------------------------------
        # GEMINI / RAG
        # ----------------------------------------------------

        fact_sheet = None
        fact_sheet_error = None

        try:

            fact_sheet = (
                generate_fish_info(
                    label,
                    confidence,
                    language=language,
                )
            )

        except Exception as exc:

            fact_sheet_error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

        # ----------------------------------------------------
        # FUSED EVIDENCE
        # ----------------------------------------------------

        evidence = {}

        fish_df = get_fish_fusion_record(
            label
        )

        if not fish_df.empty:

            evidence = (
                dataframe_records(
                    fish_df.iloc[
                        [0]
                    ]
                )[0]
            )

        elif (
            not api_df.empty
            and "species" in api_df.columns
        ):

            matched = api_df[
                api_df["species"]
                .astype(str)
                .str.strip()
                .str.lower()
                ==
                str(label)
                .strip()
                .lower()
            ]

            if not matched.empty:

                evidence = (
                    dataframe_records(
                        matched.iloc[
                            [0]
                        ]
                    )[0]
                )



                # ----------------------------------------------------
        # CONTEXT-AWARE REASONING
        # ----------------------------------------------------

        context_reasoning = None
        context_reasoning_error = None

        if CONTEXT_REASONING_AVAILABLE:

            try:

                context_reasoning = (
                    generate_context_reasoning(

                        species=
                            label,

                        confidence=
                            float(confidence),

                        fusion_df=
                            fusion_df,

                    )
                )

                if not isinstance(context_reasoning, dict):
                    context_reasoning = {
                        "success": False,
                        "error": "Context reasoning returned no structured result.",
                        "species": label,
                        "reasoning": [],
                        "reasoning_text": ""
                    }

            except Exception as exc:

                context_reasoning_error = (
                    f"{type(exc).__name__}: {exc}"
                )

        else:

            context_reasoning_error = (
                CONTEXT_REASONING_ERROR
            )
        # ----------------------------------------------------
        # FISH EDA
        # ----------------------------------------------------

        fish_eda_data = None

        if not fish_df.empty:

            # Reuse the exact endpoint logic by
            # constructing the data directly.

            numeric = []

            row = fish_df.iloc[0]

            for feature in ALL_FISH_FEATURES:

                if feature not in row.index:
                    continue

                try:

                    number = float(
                        row[feature]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if not math.isfinite(
                    number
                ):
                    continue

                numeric.append({

                    "feature":
                        feature,

                    "label":
                        feature.replace(
                            "_",
                            " "
                        ).title(),

                    "value":
                        number,

                })

            fish_eda_data = {

                "species":
                    label,

                "numeric_features":
                    numeric,

            }

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        log_ai_event(

            event_type="prediction",

            species=label,

            confidence=float(
                confidence
            ),

            language=language,

        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "species": label,
            "confidence": float(confidence),

            "top3": [
                {
                    "species": cls,
                    "confidence": float(conf)
                }
                for cls, conf in top3
            ],

            "fact_sheet": fact_sheet,
            "fact_sheet_error": fact_sheet_error,

            "fusion_evidence": evidence,

            "context_reasoning": context_reasoning,
            "context_reasoning_error": context_reasoning_error,

            "fish_eda": fish_eda_data,

            "vit_species": vit_label,
            "vit_confidence": (
                float(vit_confidence)
                if vit_confidence is not None
                else None
            ),
            "vit_top3": [
            {
                "species": cls,
                "confidence": float(conf)
            }
            for cls, conf in vit_top3
        ],
        "vit_error": vit_error,

        "ijepa_species": ijepa_label,

        "ijepa_confidence": (
            float(ijepa_confidence)
            if ijepa_confidence is not None
            else None
        ),

        "ijepa_top3": [
            {
                "species": cls,
                "confidence": float(conf)
            }
            for cls, conf in ijepa_top3
        ],

        "ijepa_error": ijepa_error,
    })

    except Exception as exc:

        return jsonify({

            "success":
                False,

            "error":
                f"{type(exc).__name__}: {exc}",

        }), 500

    finally:

        if temp_path:

            try:

                Path(
                    temp_path
                ).unlink(
                    missing_ok=True
                )

            except Exception:
                pass


# ============================================================
# MAIN AI — Q&A
# ============================================================

@app.route(
    "/api/main-ai/ask",
    methods=["POST"]
)
def main_ai_ask():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    question = str(
        data.get(
            "question",
            ""
        )
    ).strip()

    species = str(
        data.get(
            "species",
            ""
        )
    ).strip()

    language = str(
        data.get(
            "language",
            "en"
        )
    ).strip()

    session_id = str(
        data.get(
            "session_id",
            "dashboard-user"
        )
    ).strip()

    if not question:

        return jsonify({

            "success":
                False,

            "error":
                "Please enter a question.",

        }), 400

    contextual_question = question

    if species:

        contextual_question = (
            f"{question} "
            f"(The currently identified fish "
            f"is {species}.)"
        )

    try:

        answer = ask_followup(
            contextual_question,
            session_id=session_id,
            language=language,
        )

        log_ai_event(

            event_type="qa",

            species=species,

            question=question,

            answer=answer,

            language=language,

        )

        return jsonify({

            "success":
                True,

            "answer":
                answer,

        })

    except Exception as exc:

        return jsonify({

            "success":
                False,

            "error":
                f"{type(exc).__name__}: {exc}",

        }), 500


# ============================================================
# API EVIDENCE
# ============================================================

@app.route(
    "/api/api-evidence"
)
def api_evidence():

    return jsonify({

        "apis": [

            {

                "name":
                    "GBIF",

                "category":
                    "Biodiversity / Taxonomy",

                "description":
                    "Taxonomic identity, occurrence records, countries and coordinates.",

            },

            {

                "name":
                    "USDA FoodData Central",

                "category":
                    "Nutrition",

                "description":
                    "Calories, protein, fat and carbohydrate information.",

            },

            {

                "name":
                    "Weather API",

                "category":
                    "Environment",

                "description":
                    "Temperature, humidity, pressure, wind and weather conditions.",

            },

            {

                "name":
                    "OpenStreetMap",

                "category":
                    "Location",

                "description":
                    "Nearby seafood-market and geographic context.",

            },

            {

                "name":
                    "FAISS + Google Embeddings",

                "category":
                    "RAG",

                "description":
                    "Semantic retrieval used to ground Gemini.",

            },

            {

                "name":
                    "Google Gemini",

                "category":
                    "LLM",

                "description":
                    "Grounded fish fact sheets and Q&A.",

            },

        ]

    })


# ============================================================
# FUSION RESULTS
# ============================================================

@app.route(
    "/api/fusion-results"
)
def fusion_results():

    if results_df.empty:
        return jsonify([])

    required = [

        "Raw/Data-Level Fusion",

        "Feature-Level Fusion",

    ]

    if "experiment" in results_df.columns:

        result = results_df[
            results_df["experiment"]
            .isin(required)
        ].copy()

    else:

        result = results_df.copy()

    return jsonify(
        dataframe_records(
            result
        )
    )


# ============================================================
# GBIF DISTRIBUTION
# ============================================================

@app.route(
    "/api/gbif-distribution"
)
def gbif_distribution():

    if gbif_df.empty:
        return jsonify([])

    species = request.args.get(
        "species",
        "All"
    )

    df = gbif_df.copy()

    if (
        species != "All"
        and "species" in df.columns
    ):

        df = df[
            df["species"]
            .astype(str)
            .str.strip()
            == species
        ]

    # --------------------------------------------------------
    # IMPORTANT:
    # Keep the existing GBIF/OpenStreetMap functionality,
    # but return only records containing valid coordinates.
    # Also provide both latitude/longitude and lat/lon aliases
    # so the existing Leaflet frontend remains compatible.
    # --------------------------------------------------------

    return jsonify(
        gbif_map_records(df)
    )


# ============================================================
# GBIF COUNTRIES
# ============================================================

@app.route(
    "/api/gbif-countries"
)
def gbif_countries():

    if gbif_df.empty:
        return jsonify([])

    species = request.args.get(
        "species",
        "All"
    )

    df = gbif_df.copy()

    if (
        species != "All"
        and "species" in df.columns
    ):

        df = df[
            df["species"]
            .astype(str)
            .str.strip()
            == species
        ]

    if "country" not in df.columns:
        return jsonify([])

    result = (
        df["country"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("country")
        .reset_index(
            name="records"
        )
    )

    return jsonify(
        dataframe_records(
            result
        )
    )


# ============================================================
# EXPLORE MORE — TAXONOMY
# ============================================================

@app.route(
    "/api/explore/taxonomy"
)
def explore_taxonomy():

    species = request.args.get(
        "species",
        ""
    ).strip()

    if not species:

        return jsonify({

            "success":
                False,

            "error":
                "Species required."

        }), 400

    scientific_name = (
        SCIENTIFIC_NAMES.get(
            species,
            species
        )
    )

    if get_species_info:

        try:

            info = get_species_info(
                species
            )

            if info:

                scientific_name = (
                    info.get(
                        "scientific_name"
                    )
                    or scientific_name
                )

        except Exception:
            pass

    if not GBIF_MODULE_AVAILABLE:

        return jsonify({

            "success":
                False,

            "error":
                "GBIF module unavailable."

        })

    try:

        taxonomy = verify_species(
            scientific_name
        )

        return jsonify({

            "success":
                True,

            "scientific_name":
                scientific_name,

            "taxonomy":
                taxonomy,

        })

    except Exception as exc:

        return jsonify({

            "success":
                False,

            "error":
                str(exc),

        })


# ============================================================
# EXPLORE MORE — USDA
# ============================================================

@app.route(
    "/api/explore/nutrition"
)
def explore_nutrition():

    species = request.args.get(
        "species",
        ""
    ).strip()

    if not species:

        return jsonify({

            "success":
                False,

            "error":
                "Species required."

        }), 400

    if not NUTRITION_MODULE_AVAILABLE:

        return jsonify({

            "success":
                False,

            "error":
                "Nutrition module unavailable."

        })

    common_name = species

    if get_species_info:

        try:

            info = get_species_info(
                species
            )

            if info:

                common_name = (
                    info.get(
                        "common_name"
                    )
                    or common_name
                )

        except Exception:
            pass

    try:

        nutrition = get_nutrition_facts(
            common_name,
            common_name=common_name,
        )

        return jsonify({

            "success":
                True,

            "nutrition":
                nutrition,

        })

    except Exception as exc:

        return jsonify({

            "success":
                False,

            "error":
                str(exc),

        })


# ============================================================
# EXPLORE MORE — WEATHER
# ============================================================

@app.route(
    "/api/explore/weather"
)
def explore_weather():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({

            "success":
                False,

            "error":
                "City is required."

        }), 400

    if not WEATHER_MODULE_AVAILABLE:

        return jsonify({

            "success":
                False,

            "error":
                "Weather module unavailable."

        })

    try:

        weather = get_weather(
            city
        )

        return jsonify({

            "success":
                True,

            "weather":
                weather,

        })

    except Exception as exc:

        return jsonify({

            "success":
                False,

            "error":
                str(exc),

        })

SHRIMP_DISEASE_AVAILABLE = False
SHRIMP_DISEASE_ERROR = None
shrimp_disease_classifier = None

try:

    shrimp_disease_classifier = ShrimpDiseaseClassifier()

    SHRIMP_DISEASE_AVAILABLE = True

    print("Shrimp disease classifier loaded successfully.")

except Exception as exc:

    SHRIMP_DISEASE_AVAILABLE = False

    SHRIMP_DISEASE_ERROR = (
        f"{type(exc).__name__}: {exc}"
    )

    print(
        "Shrimp disease classifier unavailable:",
        SHRIMP_DISEASE_ERROR
    )

# ============================================================
# EXPLORE MORE — NEARBY MARKETS
# ============================================================

@app.route(
    "/api/explore/markets"
)
def explore_markets():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({

            "success":
                False,

            "error":
                "City is required."

        }), 400

    if not MARKET_MODULE_AVAILABLE:

        return jsonify({

            "success":
                False,

            "error":
                "Market module unavailable."

        })

    try:

        places = (
            find_nearby_seafood_places(
                city,
                radius_km=5
            )
        )

        return jsonify({

            "success":
                True,

            "places":
                places or [],

        })

    except Exception as exc:

        return jsonify({

            "success":
                False,

            "error":
                str(exc),

        })


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/api/health"
)
def health():

    return jsonify({

        "dashboard":
            True,

        "main_ai":
            MAIN_AI_AVAILABLE,

        "model":
            MODEL_PATH.exists(),

        "class_indices":
            CLASS_INDICES_PATH.exists(),

        "shrimp_disease":
        SHRIMP_DISEASE_AVAILABLE,

        "fusion_dataset":
            FINAL_FUSION_FILE.exists(),

        "api_metadata":
            API_METADATA_FILE.exists(),

        "gbif_distribution":
            GBIF_DISTRIBUTION_FILE.exists(),

        "gbif_map_records":
            int(
                len(
                    gbif_map_records(gbif_df)
                )
            ),

        "openstreetmap":
            True,

        "fusion_results":
            FUSION_RESULTS_FILE.exists(),

    })
# ============================================================
# SHRIMP DISEASE — PREDICT
# ============================================================

@app.route(
    "/api/shrimp-disease/predict",
    methods=["POST"]
)
def shrimp_disease_prediction():

    if not SHRIMP_DISEASE_AVAILABLE:

        return jsonify({
            "success": False,
            "error": "Shrimp disease model is unavailable.",
            "details": SHRIMP_DISEASE_ERROR
        }), 500

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "error": "No image uploaded."
        }), 400

    uploaded = request.files["image"]

    if not uploaded.filename:

        return jsonify({
            "success": False,
            "error": "Invalid image."
        }), 400

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    suffix = Path(
        uploaded.filename
    ).suffix.lower()

    if suffix not in allowed_extensions:

        return jsonify({
            "success": False,
            "error": (
                "Invalid image format. "
                "Use JPG, JPEG, PNG or WEBP."
            )
        }), 400

    temp_path = None

    try:

        # ----------------------------------------------------
        # SAVE UPLOADED IMAGE TEMPORARILY
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp:

            uploaded.save(
                tmp.name
            )

            temp_path = tmp.name

        # ----------------------------------------------------
        # PREDICT
        # ----------------------------------------------------

        result = shrimp_disease_predict(
            temp_path
        )

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "prediction": result["prediction"],

            "confidence": result["confidence"],

            "healthy_probability":
                result["healthy_probability"],

            "diseased_probability":
                result["diseased_probability"]

        })

    except Exception as exc:

        print(
            "Shrimp disease prediction error:"
        )

        traceback.print_exc()

        return jsonify({

            "success": False,

            "error":
                f"{type(exc).__name__}: {exc}"

        }), 500

    finally:

        # ----------------------------------------------------
        # DELETE TEMPORARY FILE
        # ----------------------------------------------------

        if (
            temp_path is not None
            and Path(temp_path).exists()
        ):

            try:

                Path(temp_path).unlink()

            except Exception:

                pass


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 70)

    print(
        "FISH AI MULTIMODAL ANALYTICS DASHBOARD"
    )

    print("=" * 70)

    print(
        "Project root:"
    )

    print(
        PROJECT_ROOT
    )

    print()

    print(
        "Main AI available:",
        MAIN_AI_AVAILABLE
    )

    if MAIN_AI_ERROR:

        print(
            "Main AI error:",
            MAIN_AI_ERROR
        )

    print()

    print(
        "Open:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print("=" * 70)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
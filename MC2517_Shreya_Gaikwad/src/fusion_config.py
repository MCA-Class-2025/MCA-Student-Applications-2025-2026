# PolicyPal Data Fusion Configuration
# 10 countries x 5 cities x 10 policy topics = up to 100 NewsData requests.
# NewsData free plan currently allows 200 credits/day; this pipeline caps the default run at 100 requests.
# Each successful NewsData request can return up to 10 articles on the free plan, so the resulting dataset
# can reach roughly 5,000 city-article observations after city contextualization.

COUNTRIES = {
    "IN": {
        "name": "India",
        "cities": ["Mumbai", "Delhi", "Bengaluru", "Pune", "Hyderabad"],
    },
    "US": {
        "name": "United States",
        "cities": ["New York", "San Francisco", "Chicago", "Seattle", "Austin"],
    },
    "GB": {
        "name": "United Kingdom",
        "cities": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow"],
    },
    "CA": {
        "name": "Canada",
        "cities": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
    },
    "AU": {
        "name": "Australia",
        "cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Canberra"],
    },
    "SG": {
        "name": "Singapore",
        "cities": ["Singapore", "Jurong East", "Woodlands", "Tampines", "Punggol"],
    },
    "AE": {
        "name": "United Arab Emirates",
        "cities": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Al Ain"],
    },
    "DE": {
        "name": "Germany",
        "cities": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"],
    },
    "FR": {
        "name": "France",
        "cities": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"],
    },
    "JP": {
        "name": "Japan",
        "cities": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya"],
    },
}

POLICY_TOPICS = [
    "remote work",
    "employee leave",
    "maternity leave",
    "workplace attendance",
    "employee benefits",
    "expense policy",
    "business travel",
    "working hours",
    "employee rights",
    "workplace regulation",
]

DATASET_COLUMNS = [
    "record_id",
    "observation_date",
    "country_code",
    "country_name",
    "alpha3_code",
    "capital",
    "region",
    "subregion",
    "timezone",
    "population",
    "area_km2",
    "currency_code",
    "currency_name",
    "currency_symbol",
    "usd_to_local_rate",
    "city",
    "latitude",
    "longitude",
    "temperature_c",
    "precipitation_mm",
    "wind_speed_kmh",
    "weather_code",
    "weather_condition",
    "is_severe_weather",
    "holiday_date",
    "holiday_name",
    "holiday_type",
    "is_public_holiday",
    "policy_topic",
    "news_title",
    "news_source",
    "news_url",
    "news_published_at",
    "news_country",
    "api_collection_status",
    "data_quality_flag",
]

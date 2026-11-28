"""Stateful Streamlit interface for the live healthcare-facility search."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from scripts.api_overpass_search import find_healthcare


US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
    "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]


@st.cache_data(ttl=900, show_spinner=False)
def _cached_search(city: str, state: str, radius_km: int) -> dict:
    """Reduce repeated traffic to the public Nominatim/Overpass services."""
    return find_healthcare(city=city, state=state, radius_km=radius_km)


def _safe_web_url(value: object) -> str | None:
    text = str(value or "").strip()
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    return text if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _prepare_facilities(records: list[dict]) -> pd.DataFrame:
    expected = [
        "name", "type", "distance_km", "address", "phone", "website",
        "osm_url", "latitude", "longitude",
    ]
    frame = pd.DataFrame(records)
    for column in expected:
        if column not in frame.columns:
            frame[column] = None

    frame["name"] = frame["name"].fillna("Unnamed facility")
    frame["type"] = frame["type"].fillna("Healthcare Facility")
    frame["address"] = frame["address"].fillna("").replace("", "Address not available")
    frame["phone"] = frame["phone"].fillna("").replace("", "Not available")
    frame["website"] = frame["website"].apply(
        lambda value: _safe_web_url(value) or "Not available"
    )
    frame["distance_km"] = pd.to_numeric(frame["distance_km"], errors="coerce")
    return frame.sort_values(
        ["distance_km", "name"], na_position="last"
    ).reset_index(drop=True)


def _render_results(search: dict) -> None:
    result = search["result"]
    city = search["city"]
    state = search["state"]

    if not result.get("success"):
        if result.get("error") == "location":
            st.error(
                f"Could not verify {city}, {state}. Check the spelling and search again."
            )
        else:
            st.error(
                "The OpenStreetMap healthcare service is temporarily unavailable. "
                "Your previous app data was not affected. Please try again later."
            )
        return

    facilities = _prepare_facilities(result.get("facilities", []))
    location = result.get("location") or {}
    verified_location = location.get("display_name", f"{city}, {state}")

    if facilities.empty:
        st.warning(
            f"No mapped healthcare facilities were found within "
            f"{search['radius_km']} km of {city}, {state}. Try a larger radius."
        )
        return

    st.success(
        f"Found {len(facilities):,} mapped facilities within "
        f"{search['radius_km']} km."
    )
    st.caption(
        f"Verified search location: {verified_location} · "
        f"Search performed {search['searched_at']} UTC"
    )

    st.markdown("### Find a facility")
    filter_col, name_col, sort_col = st.columns([1, 1.6, 1])
    with filter_col:
        available_types = ["All", *sorted(facilities["type"].dropna().unique())]
        selected_type = st.selectbox(
            "Facility type", available_types, key="healthcare_type_filter"
        )
    with name_col:
        search_name = st.text_input(
            "Facility name", placeholder="Hospital, clinic, pharmacy…",
            key="healthcare_name_search",
        )
    with sort_col:
        sort_order = st.selectbox(
            "Sort by", ["Nearest first", "Name A–Z"],
            key="healthcare_sort_order",
        )

    filtered = facilities.copy()
    if selected_type != "All":
        filtered = filtered.loc[filtered["type"].eq(selected_type)]
    if search_name.strip():
        filtered = filtered.loc[
            filtered["name"].str.contains(
                search_name.strip(), case=False, na=False, regex=False
            )
        ]
    if sort_order == "Name A–Z":
        filtered = filtered.sort_values("name", key=lambda s: s.str.lower())
    else:
        filtered = filtered.sort_values("distance_km", na_position="last")

    st.caption(f"Showing {len(filtered):,} of {len(facilities):,} facilities.")

    categories = [
        ("Hospitals", "Hospital"), ("Clinics", "Clinic"),
        ("Doctors", "Doctor"), ("OB-GYN", "Gynecologist / OB-GYN"),
        ("Pharmacies", "Pharmacy"),
    ]
    count_columns = st.columns(5)
    for column, (label, category) in zip(count_columns, categories):
        column.metric(label, int(facilities["type"].eq(category).sum()))

    if filtered.empty:
        st.info("No facilities match the current filters.")
        return

    st.markdown("### Facility directory")
    directory = filtered[
        ["name", "type", "distance_km", "address", "phone", "website"]
    ].copy()
    directory.columns = [
        "Facility", "Type", "Distance (km)", "Address", "Phone", "Website"
    ]
    st.dataframe(
        directory,
        width="stretch",
        hide_index=True,
        height=min(520, 38 + len(directory.head(12)) * 35),
        column_config={
            "Distance (km)": st.column_config.NumberColumn(format="%.2f km"),
            "Website": st.column_config.LinkColumn(display_text="Open website"),
        },
    )

    st.markdown("### Facility map")
    map_data = filtered.dropna(subset=["latitude", "longitude"])
    if map_data.empty:
        st.info("Coordinates are not available for the filtered facilities.")
    else:
        st.map(
            map_data, latitude="latitude", longitude="longitude", size=38,
            width="stretch",
        )

    st.markdown("### Facility details")
    details_limit = 30
    for _, facility in filtered.head(details_limit).iterrows():
        distance = (
            f"{facility['distance_km']:.2f} km"
            if pd.notna(facility["distance_km"])
            else "Distance unavailable"
        )
        with st.expander(f"{facility['name']} · {facility['type']} · {distance}"):
            detail_col, action_col = st.columns([3, 1])
            with detail_col:
                st.markdown(f"**Address:** {facility['address']}")
                st.markdown(f"**Phone:** {facility['phone']}")
                if facility["website"] != "Not available":
                    st.link_button("Open facility website", facility["website"])
                if _safe_web_url(facility.get("osm_url")):
                    st.link_button("View OpenStreetMap record", facility["osm_url"])
            with action_col:
                if pd.notna(facility["latitude"]) and pd.notna(facility["longitude"]):
                    maps_url = (
                        "https://www.google.com/maps/search/?api=1&query="
                        f"{facility['latitude']},{facility['longitude']}"
                    )
                    st.link_button("Open directions", maps_url, width="stretch")

    if len(filtered) > details_limit:
        st.caption(
            f"Showing details for the nearest {details_limit} matches. "
            "Use the filters to narrow the directory."
        )

    st.warning(
        "OpenStreetMap entries can be incomplete or outdated. Verify the facility, "
        "services, opening hours and contact details before travelling. This finder "
        "is not an emergency service."
    )


def render_healthcare_finder() -> None:
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🏥 FemCare Healthcare Finder</div>
            <p class="hero-subtitle">
                Search mapped hospitals, clinics, doctors, OB-GYN services and
                pharmacies across the United States.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "The search sends the entered city, state and radius to public "
        "OpenStreetMap services. FemCare does not store a precise home address."
    )

    state_col, city_col, radius_col = st.columns([1, 1.25, 1])
    with state_col:
        state = st.selectbox(
            "State", US_STATES, index=US_STATES.index("Massachusetts"),
            key="healthcare_state",
        )
    with city_col:
        city = st.text_input(
            "City or locality", value="Boston", placeholder="Example: Boston",
            key="healthcare_city",
        )
    with radius_col:
        radius = st.slider(
            "Search radius", min_value=5, max_value=50, value=15,
            step=5, format="%d km", key="healthcare_radius",
        )

    if st.button(
        "Find healthcare facilities", type="primary", width="stretch"
    ):
        if not city.strip():
            st.warning("Enter a city or locality before searching.")
        else:
            with st.spinner(f"Searching near {city.strip()}, {state}…"):
                result = _cached_search(city.strip(), state, radius)
            st.session_state["healthcare_search"] = {
                "city": city.strip(), "state": state, "radius_km": radius,
                "searched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "result": result,
            }

    saved_search = st.session_state.get("healthcare_search")
    if saved_search:
        _render_results(saved_search)
    else:
        st.caption(
            "Choose a location and radius, then start a search. Results will remain "
            "available while you change the directory filters."
        )

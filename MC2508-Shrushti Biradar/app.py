import streamlit as st
import joblib
import pandas as pd
import smtplib
import os

from email.message import EmailMessage
from chatbot import generate_response
from api.Googleplaces_api import search_places
from api.Openweather_api import get_weather
from api.Sendgrid_api import send_email
from api.Unsplash_api import get_event_images
from api.googleroute_api import get_route

from history import (
    create_history_table,
    save_event_plan,
    get_user_event_history,
    get_event_plan,
    delete_event_plan
)
# Load ML model
model = joblib.load("event_success_model.pkl")


# ==============================
# PAGE CONFIGURATION
# ==============================

st.set_page_config(
    page_title="AI Event Planner",
    page_icon="🎉",
    layout="wide"
)
# Create Event History table
create_history_table()


# ==============================
# TITLE
# ==============================

st.title("🎉 AI Event Planner")

st.write(
    "Create a personalized and practical event plan using Gemini AI."
)

st.divider()



# ==============================
# EVENT DETAILS
# ==============================

st.header("📝 Enter Your Event Details")


event_type = st.selectbox(
    "🎉 Event Type",
    [
        "Birthday",
        "Wedding",
        "Engagement",
        "Anniversary",
        "College Event",
        "Corporate Event",
        "Other"
    ]
)


event_date = st.date_input(
    "📅 Event Date"
)


location = st.text_input(
    "📍 Location",
    placeholder="Example: Mumbai"
)


guests = st.number_input(
    "👥 Number of Guests",
    min_value=1,
    max_value=10000,
    value=50,
    step=1
)


budget = st.number_input(
    "💰 Budget (₹)",
    min_value=1000,
    max_value=10000000,
    value=50000,
    step=1000
)


preferences = st.text_area(
    "✨ Special Preferences",
    placeholder=(
        "Example: vegetarian food, DJ, decoration, "
        "games, photography..."
    )
)
# --------------------------------
# DECORATION PREFERENCES
# --------------------------------

st.subheader("🎨 Decoration Preferences")

theme = st.text_input(
    "🎭 Decoration Theme",
    placeholder="Example: Royal, Romantic, Barbie, Floral"
)

color = st.text_input(
    "🎨 Decoration Color",
    placeholder="Example: Pink, Blue, Red, White and Gold"
)

decoration_preferences = st.text_area(
    "✨ Special Decoration Requirements",
    placeholder=(
        "Example: flowers, balloons, LED lights, "
        "stage decoration, elegant setup..."
    )
)

  # ==============================
# GENERATE EVENT PLAN
# ==============================

if st.button("✨ Generate Event Plan"):

    decoration_query = f"{event_type} event decoration ideas"

    # ==============================
    # BASIC VALIDATION
    # ==============================

    if not location.strip():

        st.warning("⚠️ Please enter a location before generating the plan.")

    else:
            
            

        # ==============================
        # FIND REAL PLACES + WEATHER
        # ==============================

        places = []

        with st.spinner("📍 Finding real places and weather..."):

            try:

                places = search_places(
                    location,
                    "event venues"
                )

                weather = get_weather(location)

            except Exception as e:

                places = []

                weather = {}

                st.warning(
                    "⚠️ Could not fetch places or weather data."
                )

        # ==========================================
        # GOOGLE ROUTES - DISTANCE & TRAVEL TIME
        # ==========================================

        route_information = []

        if places:

            for place in places[:5]:

                try:

                    venue_name = place.get(
                        "displayName",
                        {}
                    ).get(
                        "text",
                        "Unknown Venue"
                    )

                    venue_address = place.get(
                        "formattedAddress",
                        ""
                    )

                    route = get_route(
                        location,
                        venue_address
                    )

                    route_information.append({
                        "name": venue_name,
                        "address": venue_address,
                        "distance_km": route.get(
                            "distance_km",
                            "Unavailable"
                        ),
                        "travel_time": route.get(
                            "duration_text",
                            "Unavailable"
                        )
                    })

                except Exception:

                    route_information.append({
                        "name": venue_name,
                        "address": venue_address,
                        "distance_km": "Unavailable",
                        "travel_time": "Unavailable"
                    })

        else:

            st.warning("⚠️ No event venues found.")

        # ==========================================
        # DISPLAY ROUTE INFORMATION
        # ==========================================

        if route_information:

            st.subheader("🛣️ Distance & Travel Time")

            for route in route_information:

                st.markdown(
                    f"""
                    ### 📍 {route['name']}

                    **Address:** {route['address']}

                    🚗 **Distance:** {route['distance_km']} km

                    ⏱️ **Travel Time:** {route['travel_time']}
                    """
                )

                st.divider()
        
        # ==============================
        # PREPARE REAL PLACE INFORMATION
        # ==============================

        places_text = ""

        for place in places[:5]:

            name = place.get(
                "displayName", {}
            ).get(
                "text",
                "Unknown Place"
            )

            address = place.get(
                "formattedAddress",
                "Address unavailable"
            )

            rating = place.get(
                "rating",
                "Not available"
            )

            map_link = place.get(
                "googleMapsUri",
                ""
            )

            places_text += f"""
Name: {name}
Address: {address}
Rating: {rating}
Google Maps: {map_link}

-------------------------
"""

        if not places_text:

            places_text = "No real places were found."

        # ==============================
        # PREPARE WEATHER INFORMATION
        # ==============================

        if weather:

            weather_text = f"""
City: {weather.get("city", location)}
Temperature: {weather.get("temperature", "Not available")} °C
Feels Like: {weather.get("feels_like", "Not available")} °C
Humidity: {weather.get("humidity", "Not available")} %
Weather: {weather.get("description", "Not available")}
Wind Speed: {weather.get("wind_speed", "Not available")} m/s
"""

        else:

            weather_text = "Weather information is not available."

        # ==============================
        # SHOW REAL PLACES
        # ==============================

        if places:

            st.subheader("📍 Real Places Found in Your Location")

            for place in places[:5]:

                name = place.get(
                    "displayName", {}
                ).get(
                    "text",
                    "Unknown Place"
                )

                address = place.get(
                    "formattedAddress",
                    "Address unavailable"
                )

                rating = place.get(
                    "rating",
                    "Not available"
                )

                map_link = place.get(
                    "googleMapsUri",
                    ""
                )

                st.markdown(f"### 🏢 {name}")

                st.write(f"📍 **Address:** {address}")

                st.write(f"⭐ **Rating:** {rating}")

                if map_link:

                    st.link_button(
                        "🗺️ View on Google Maps",
                        map_link
                    )

                st.divider()

        # ==============================
        # SHOW WEATHER
        # ==============================

        if weather:

            st.subheader("🌦️ Current Weather")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "🌡️ Temperature",
                    f'{weather.get("temperature", "N/A")} °C'
                )

            with col2:
                st.metric(
                    "💧 Humidity",
                    f'{weather.get("humidity", "N/A")} %'
                )

            with col3:
                st.write(
                    f'🌧️ **Weather:** {weather.get("description", "N/A")}'
                )

        # ==============================
        # SHOW REAL PLACES
        # ==============================

        if places:

            st.subheader("📍 Real Places Found in Your Location")

            for place in places[:5]:

                name = place.get(
                    "displayName", {}
                ).get(
                    "text",
                    "Unknown Place"
                )

                address = place.get(
                    "formattedAddress",
                    "Address not available"
                )

                rating = place.get(
                    "rating",
                    "N/A"
                )

                map_url = place.get(
                    "googleMapsUri",
                    ""
                )

                st.markdown(f"### 🏢 {name}")

                st.write(f"📍 **Address:** {address}")

                st.write(f"⭐ **Rating:** {rating}")

                if map_url:

                    st.link_button(
                        "🗺️ View on Google Maps",
                        map_url
                    )

                st.divider()

        else:

            st.info(
                "ℹ️ No real places were found for this location."
            )

        # ==============================
        # PREPARE REAL PLACE INFORMATION
        # ==============================

        places_text = ""

        for place in places[:5]:

            name = place.get(
                "displayName", {}
            ).get(
                "text",
                "Unknown"
            )

            address = place.get(
                "formattedAddress",
                "Address unavailable"
            )

            rating = place.get(
                "rating",
                "Not available"
            )

            map_link = place.get(
                "googleMapsUri",
                ""
            )

            places_text += f"""
Name: {name}
Address: {address}
Rating: {rating}
Google Maps: {map_link}

-------------------------
"""

        if not places_text:

            places_text = "No real places were found."
        # --------------------------------
        # FORMAT USER DATA
        # --------------------------------

        formatted_date = event_date.strftime("%d %B %Y")

        location = location.strip()

        guests = int(guests)

        budget = int(budget)


        # --------------------------------
        # BUDGET PER GUEST
        # --------------------------------

        budget_per_guest = budget / guests


        # --------------------------------
        # GEMINI PROMPT
        # --------------------------------

        prompt = f"""
You are an expert professional AI Event Planner.

Your job is to create a realistic, practical and detailed event
plan that could actually be used by a person organizing this event.

Use ONLY the user's event information provided below.

==================================================
USER EVENT DETAILS
==================================================

Event Type: {event_type}

Event Date: {formatted_date}

Location: {location}

Number of Guests: {guests}

Total Budget: ₹{budget}

Approximate Budget Per Guest: ₹{budget_per_guest:.2f}

Special Preferences:
{preferences if preferences.strip() else "No special preferences provided."}


REAL PLACES FOUND BY GOOGLE PLACES API:

{places_text}


==================================================
VERY IMPORTANT RULES
==================================================

1. EVENT DATE

The event date provided by the user is FINAL.

Use exactly:

{formatted_date}

NEVER change the date.

NEVER invent another date.

NEVER move the event to another date.


2. LOCATION

The user's location is FINAL.

Use:

{location}

Do not replace the location with another city.

You may mention nearby areas only when suggesting practical
venue options, but the main event location must remain
{location}.


3. GUEST COUNT

The guest count is FINAL.

The event is for exactly:

{guests} guests.

All food, seating, venue capacity, transportation,
activities and crowd-management suggestions must consider
{guests} guests.


4. BUDGET

The maximum available budget is:

₹{budget}

The total estimated cost MUST NOT exceed ₹{budget}.

Calculate the budget carefully.

Do not create unrealistic prices just to make the total fit.


5. REAL-LIFE PRACTICALITY

The plan should be realistic for:

Location: {location}
Guests: {guests}
Budget: ₹{budget}
Date: {formatted_date}

Think about actual event-planning problems such as:

- venue capacity
- food quantity
- seating
- crowd management
- parking
- toilets
- electricity
- sound system
- decoration
- cake
- photography
- transportation
- weather
- rain
- emergency arrangements
- permissions
- cleanup
- timing
- vendor coordination


6. BUDGET CONSTRAINT

If ₹{budget} is too low for {guests} guests, DO NOT pretend
that expensive services are affordable.

Clearly explain that the budget is tight.

Then suggest practical ways to reduce costs.

Examples:

- community hall
- society clubhouse
- simple decoration
- limited menu
- buffet instead of expensive catering
- DIY decoration
- family/friend photographer
- local DJ
- digital invitations
- shared transportation


7. SPECIAL PREFERENCES

Respect the user's preferences:

{preferences if preferences.strip() else "No special preferences provided."}

Include them wherever realistically possible.

If a preference conflicts with the budget, explain the
cheaper alternative.
8. REAL PLACES:
   Use the real places provided by the Google Places API when recommending
   restaurants, cafes, or food venues.

   Do NOT invent Google Maps links.

   If real places are provided, mention their actual name, address,
   rating, and Google Maps link where useful.

   Do not claim that a place is a suitable event venue unless the
   available information supports that conclusion.

9. REALISTIC BUDGET:
   Calculate the estimated costs carefully.

   The final total MUST NOT exceed the user's budget.

   If the budget is too low for the number of guests, clearly explain
   the limitation and provide practical cost-saving alternatives.

10. COMPLETE PLAN:
    All 8 requested sections MUST contain useful information.

    Important Tips must contain at least 5 practical tips.

    Do not leave any section empty.

    REAL VENUE RULES:

Use the real places provided above when recommending venues.

Do NOT invent fake venue names when a suitable real place is available.

For each recommended real place, use the exact name and address provided.

Include the Google Maps link when available.

Choose venues that are practical for the event type, guest count,
location, and budget.

Consider the event type, guest count, location, and budget before recommending a place.

If none of the provided places are suitable for the event,
clearly say that and recommend a suitable venue type instead.

==================================================
REQUIRED EVENT PLAN
==================================================

Create EXACTLY these 8 sections:


### 1. 🎉 Event Overview

Include:

Event Type:
Event Date:
Location:
Guest Count:
Total Budget:
Budget Per Guest:

Then provide a short realistic description of the event.


### 2. 📍 Recommended Venue

Recommend a suitable TYPE of venue based on:

- number of guests
- budget
- location
- event type
- date

Explain:

- approximate capacity required
- seating arrangement
- parking
- toilets
- electricity
- rain/weather protection
- accessibility
- estimated venue cost

Do not invent a specific venue name unless you have reliable
information.


### 3. 🍽️ Food and Catering

Create a realistic food plan.

Include:

- welcome drink
- starters
- main course
- dessert
- cake if appropriate
- water
- vegetarian/non-vegetarian options based on preferences

Calculate food quantity for exactly {guests} guests.

Show an approximate cost calculation.

Example:

{guests} guests × ₹X per person = ₹Y

Make sure the food cost fits inside the total budget.


### 4. 🎨 Decoration

Create a practical decoration plan.

Include:

- entrance
- stage/backdrop
- balloons
- lights
- cake table
- seating decoration

Give an estimated cost.

Prefer budget-friendly options when the budget is limited.


### 5. 🎵 Entertainment and Activities

Suggest realistic entertainment based on:

- event type
- number of guests
- budget

Possible options:

- DJ
- music playlist
- live singer
- games
- dance
- birthday activities
- photography
- announcements

Do not recommend expensive entertainment if it cannot fit
within the budget.


### 6. ⏰ Event Schedule

Create a realistic timetable.

Use the EXACT date:

{formatted_date}

Include preparation/setup time and guest arrival.

Make sure the schedule works for {guests} guests.

Include:

- setup
- guest arrival
- welcome
- food
- activities
- main ceremony
- entertainment
- closing
- cleanup


### 7. 💰 Estimated Budget

Create a clear budget table.

Include:

| Item | Estimated Cost |
|------|----------------|
| Venue | ₹ |
| Food | ₹ |
| Cake | ₹ |
| Decoration | ₹ |
| Entertainment | ₹ |
| Photography | ₹ |
| Transportation | ₹ |
| Miscellaneous | ₹ |
| Emergency/Contingency | ₹ |
| TOTAL | ₹ |

IMPORTANT:

The final TOTAL MUST NOT exceed:

₹{budget}

Also calculate:

Budget per guest = ₹{budget_per_guest:.2f}


After the table, explain where money can be saved if necessary.


### 8. 💡 Important Tips

Provide AT LEAST 5 useful practical tips.

Include tips about:

1. Venue
2. Food
3. Crowd management
4. Budget
5. Weather/logistics

Also mention any important safety, permission or vendor
coordination issues relevant to the event.


==================================================
FINAL VALIDATION
==================================================

Before giving the final answer, check all of the following:

✓ Event date is exactly {formatted_date}

✓ Location is exactly {location}

✓ Guest count is exactly {guests}

✓ Budget is exactly ₹{budget}

✓ Total estimated cost is NOT greater than ₹{budget}

✓ All 8 sections contain useful information

✓ Section 8 contains at least 5 tips

✓ Food quantity is appropriate for {guests} guests

✓ Venue capacity is appropriate for {guests} guests

✓ Schedule uses the correct event date

✓ Recommendations are realistic

✓ Special preferences are respected

DO NOT change the user's date.

DO NOT change the user's location.

DO NOT change the user's guest count.

DO NOT exceed the user's budget.

DO NOT leave any section empty.
"""

# ==========================================
# GENERATE RESPONSE + UNSPLASH IMAGES
# ==========================================

# Create prompt for Gemini
prompt = f"""
Create a detailed, realistic and practical event plan.

EVENT DETAILS
-------------
Event Type: {event_type}
Location: {location}
Number of Guests: {guests}
Budget: ₹{budget}

DECORATION DETAILS
------------------
Decoration Theme: {theme}
Decoration Color: {color}
Special Decoration Requirements: {decoration_preferences}

Please create the event plan with the following sections:

1. 🎉 Event Overview
2. 🎨 Decoration Plan
3. 🏛️ Venue Setup
4. 🍽️ Food and Catering
5. 🎵 Entertainment
6. 💡 Lighting and Special Effects
7. 🛍️ Required Materials
8. 💰 Detailed Budget Breakdown
9. ⏰ Event Timeline
10. 💡 Special Recommendations

Make the plan suitable for the customer's exact requirements,
guest count, location and budget.
"""

# ==========================================
# GENERATE EVENT PLAN
# ==========================================

with st.spinner("🤖 Gemini is creating your realistic event plan..."):

    try:

        # Generate event plan using Gemini
        result = generate_response(prompt)

        

        # ==========================================
        # UNSPLASH DECORATION IMAGES
        # ==========================================

        st.divider()

        st.subheader("🖼️ Decoration & Inspiration Ideas")

        with st.spinner("🖼️ Finding decoration ideas..."):

            unsplash_photos = get_event_images(
                event_type=event_type,
                preferences=decoration_preferences,
                color=color,
                theme=theme,
                images_per_category=3,
                max_categories=6
            )

        # ==========================================
        # DISPLAY IMAGES
        # ==========================================

        if unsplash_photos:

            cols = st.columns(3)

            for index, photo in enumerate(unsplash_photos):

                with cols[index % 3]:

                    st.image(
                        photo["image_url"],
                        use_container_width=True
                    )

                    st.caption(
                        f"📸 {photo['photographer']}"
                    )

                    st.markdown(
                        f"[View photo on Unsplash]({photo['photo_url']})"
                    )

        else:

            st.warning(
                "⚠️ No decoration images found."
            )

    except Exception as e:

        st.error(
            "❌ Unable to generate the event plan."
        )

        st.write(str(e))


        # ==========================================
        # UNSPLASH DECORATION IMAGES
        # ==========================================

        st.divider()

        with st.spinner("🖼️ Finding decoration ideas..."):

            unsplash_photos = get_event_images(
    event_type=event_type,
    preferences=decoration_preferences,
    color=color,
    theme=theme,
    images_per_category=3,
    max_categories=6
)

        # ==========================================
        # DISPLAY UNSPLASH IMAGES
        # ==========================================

        if unsplash_photos:

            st.subheader("🖼️ Decoration & Inspiration Ideas")

            cols = st.columns(3)

            for index, photo in enumerate(unsplash_photos):

                with cols[index % 3]:

                    st.image(
                        photo["image_url"],
                        use_container_width=True
                    )

                    st.caption(
                        f"📸 {photo['photographer']}"
                    )

                    st.markdown(
                        f"[View photo on Unsplash]({photo['photo_url']})"
                    )

        else:

            st.warning(
                "⚠️ No decoration images found."
            )

    except Exception as e:

        st.error(
            "❌ Unable to generate the event plan."
        )

        st.write(str(e))

           

st.subheader("📧 Email Your Event Plan")

email = st.text_input(
    "Enter your email address",
    placeholder="example@gmail.com"
)

if st.button("📨 Send Event Plan"):

    if not email.strip():

        st.warning(
            "Please enter your email address."
        )

    else:

        with st.spinner("Sending email..."):

            success = send_email(
                email,
                f"Your {event_type} Event Plan 🎉",
                  st.session_state["event_plan"]
            )

            if success:

                st.success(
                    "✅ Event plan sent successfully!"
                )

            else:

                st.error(
                    "❌ Failed to send email."
                )
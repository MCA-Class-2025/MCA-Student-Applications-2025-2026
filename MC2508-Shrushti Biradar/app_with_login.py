import streamlit as st

from chatbot import generate_response
from api.Googleplaces_api import search_places
from api.Openweather_api import get_weather
from api.Sendgrid_api import send_email, get_last_error
from api.Unsplash_api import get_event_images
from api.googleroute_api import get_route
from auth import create_user_table, register_user, authenticate_user, valid_email

# ==============================
# PAGE CONFIGURATION
# ==============================

st.set_page_config(
    page_title="AI Event Planner",
    page_icon="🎉",
    layout="wide"
)

# ==============================
# USER LOGIN / REGISTRATION
# ==============================

create_user_table()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None

if not st.session_state["logged_in"]:

    st.title("🔐 AI Event Planner")
    st.write("Please login or create an account to continue.")
    st.divider()

    login_tab, register_tab = st.tabs(["🔑 Login", "📝 Registration"])

    with login_tab:

        st.subheader("Welcome Back!")

        login_email = st.text_input(
            "📧 Email",
            key="login_email",
            placeholder="example@gmail.com"
        )

        login_password = st.text_input(
            "🔒 Password",
            type="password",
            key="login_password"
        )

        if st.button("🔐 Login", use_container_width=True):

            if not login_email.strip() or not login_password:
                st.error("Please enter both email and password.")

            elif not valid_email(login_email):
                st.error("Please enter a valid email address.")

            else:
                user = authenticate_user(
                    login_email,
                    login_password
                )

                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.success(
                        f"Welcome {user['full_name']}! 🎉"
                    )
                    st.rerun()

                else:
                    st.error(
                        "❌ Invalid email or password."
                    )

    with register_tab:

        st.subheader("Create Your Account")

        reg_name = st.text_input(
            "👤 Full Name",
            key="reg_name",
            placeholder="Enter your full name"
        )

        reg_email = st.text_input(
            "📧 Email",
            key="reg_email",
            placeholder="example@gmail.com"
        )

        reg_password = st.text_input(
            "🔒 Password",
            type="password",
            key="reg_password",
            help=(
                "Minimum 8 characters with uppercase, lowercase, "
                "number and special character."
            )
        )

        reg_confirm_password = st.text_input(
            "🔒 Confirm Password",
            type="password",
            key="reg_confirm_password"
        )

        st.caption(
            "Password: 8+ characters, uppercase, lowercase, "
            "number and special character."
        )

        if st.button(
            "📝 Create Account",
            use_container_width=True
        ):

            success, message = register_user(
                reg_name,
                reg_email,
                reg_password,
                reg_confirm_password
            )

            if success:
                st.success(f"✅ {message}")
                st.info(
                    "Now open the Login tab and sign in."
                )

            else:
                st.error(f"❌ {message}")

    st.stop()


# ==============================
# LOGGED-IN USER HEADER
# ==============================

current_user = st.session_state.get("user")

header_col1, header_col2 = st.columns([5, 1])

with header_col1:
    if current_user:
        st.success(
            f"👋 Welcome, {current_user['full_name']}!"
        )

with header_col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user"] = None
        st.session_state.pop("event_plan", None)
        st.session_state.pop("results", None)
        st.rerun()

st.divider()

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

    if not location.strip():

        st.warning("⚠️ Please enter a location before generating the plan.")

    else:

        location = location.strip()
        guests = int(guests)
        budget = int(budget)
        budget_per_guest = budget / guests
        formatted_date = event_date.strftime("%d %B %Y")

        # ---------- 1. PLACES + WEATHER ----------
        places = []
        weather = {}

        with st.spinner("📍 Finding real places and weather..."):

            try:
                places = search_places(location, "event venues") or []
            except Exception:
                st.warning("⚠️ Could not fetch places.")

            try:
                weather = get_weather(location) or {}
            except Exception:
                st.warning("⚠️ Could not fetch weather.")

        # ---------- 2. ROUTES ----------
        route_information = []

        for place in places[:5]:

            venue_name = place.get("displayName", {}).get("text", "Unknown Venue")
            venue_address = place.get("formattedAddress", "")

            try:
                route = get_route(location, venue_address)
                distance = route.get("distance_km", "Unavailable")
                travel_time = route.get("duration_text", "Unavailable")
            except Exception:
                distance = "Unavailable"
                travel_time = "Unavailable"

            route_information.append({
                "name": venue_name,
                "address": venue_address,
                "distance_km": distance,
                "travel_time": travel_time
            })

               # ---------- 3. TEXT FOR GEMINI ----------
        places_text = ""

        for place in places[:5]:
            p_name = place.get("displayName", {}).get("text", "Unknown")
            p_address = place.get("formattedAddress", "Address unavailable")
            p_rating = place.get("rating", "Not available")
            p_link = place.get("googleMapsUri", "")
            places_text += (
                f"Name: {p_name}\n"
                f"Address: {p_address}\n"
                f"Rating: {p_rating}\n"
                f"Google Maps: {p_link}\n"
                "-------------------------\n"
            )

        if not places_text:
            places_text = "No real places were found."

        if weather:
            weather_text = (
                f"City: {weather.get('city', location)}\n"
                f"Temperature: {weather.get('temperature', 'Not available')} °C\n"
                f"Humidity: {weather.get('humidity', 'Not available')} %\n"
                f"Weather: {weather.get('description', 'Not available')}\n"
                f"Wind Speed: {weather.get('wind_speed', 'Not available')} m/s\n"
            )
        else:
            weather_text = "Weather information is not available."

        preferences_text = preferences.strip() if preferences.strip() else "No special preferences provided."
        theme_text = theme.strip() if theme.strip() else "Not specified"
        color_text = color.strip() if color.strip() else "Not specified"
        decor_text = decoration_preferences.strip() if decoration_preferences.strip() else "Not specified"

        # ---------- 4. THE PROMPT ----------
        prompt = f"""
You are an expert professional AI Event Planner.
Create a realistic, practical and detailed event plan.

EVENT DETAILS (these are FINAL, never change them)
Event Type: {event_type}
Event Date: {formatted_date}
Location: {location}
Number of Guests: {guests}
Total Budget: ₹{budget}
Budget Per Guest: ₹{budget_per_guest:.2f}

Special Preferences:
{preferences_text}

Decoration Theme: {theme_text}
Decoration Color: {color_text}
Special Decoration Requirements: {decor_text}

REAL PLACES FROM GOOGLE PLACES:
{places_text}

CURRENT WEATHER IN {location}:
{weather_text}

RULES
1. Use the exact date, location, guest count and budget above.
2. The total estimated cost MUST NOT exceed ₹{budget}.
3. If the budget is too low for {guests} guests, say so clearly
   and suggest cheaper options.
4. Use the real places above when you recommend venues. Use their
   exact names and addresses. Never invent Google Maps links.
5. Think about weather, rain, parking, toilets, electricity,
   seating, food quantity and safety.
6. Respect the special preferences and the decoration choices.

CREATE EXACTLY THESE 8 SECTIONS
### 1. 🎉 Event Overview
### 2. 📍 Recommended Venue
### 3. 🍽️ Food and Catering (show cost: guests x price per person)
### 4. 🎨 Decoration (use the theme and color)
### 5. 🎵 Entertainment and Activities
### 6. ⏰ Event Schedule (use the date {formatted_date})
### 7. 💰 Estimated Budget (a table, with TOTAL not above ₹{budget})
### 8. 💡 Important Tips (at least 5 tips)

Do not leave any section empty.
"""
        # ---------- 5. ASK GEMINI ----------
        result = None

        with st.spinner("🤖 Gemini is creating your realistic event plan..."):
            try:
                result = generate_response(prompt)
            except Exception as e:
                st.error("❌ Unable to generate the event plan.")
                st.write(str(e))

        # ---------- 6. UNSPLASH IMAGES ----------
        unsplash_photos = []

        if result:
            with st.spinner("🖼️ Finding decoration ideas..."):
                try:
                    unsplash_photos = get_event_images(
                        event_type=event_type,
                        preferences=decoration_preferences,
                        color=color,
                        theme=theme,
                        images_per_category=3,
                        max_categories=6
                    ) or []
                except Exception:
                    st.warning("⚠️ Could not fetch decoration images.")

        # ---------- 7. SAVE EVERYTHING ----------
        if result:
            st.session_state["event_plan"] = result
            st.session_state["results"] = {
                "plan": result,
                "places": places[:5],
                "routes": route_information,
                "weather": weather,
                "photos": unsplash_photos,
            }


# ==============================
# SHOW RESULTS (from saved memory)
# ==============================

results = st.session_state.get("results")

if results:

    st.success("🎉 Your Event Plan is Ready!")

    # ----- Weather -----
    weather = results["weather"]

    if weather:
        st.subheader("🌦️ Current Weather")
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡️ Temperature", f'{weather.get("temperature", "N/A")} °C')
        c2.metric("💧 Humidity", f'{weather.get("humidity", "N/A")} %')
        c3.write(f'🌧️ **Weather:** {weather.get("description", "N/A")}')

    # ----- Places -----
    if results["places"]:
        st.subheader("📍 Real Places Found in Your Location")

        for place in results["places"]:
            st.markdown(f"### 🏢 {place.get('displayName', {}).get('text', 'Unknown Place')}")
            st.write(f"📍 **Address:** {place.get('formattedAddress', 'Address unavailable')}")
            st.write(f"⭐ **Rating:** {place.get('rating', 'N/A')}")

            map_url = place.get("googleMapsUri", "")
            if map_url:
                st.link_button("🗺️ View on Google Maps", map_url, key=f"map_{map_url}")

            st.divider()
    else:
        st.info("ℹ️ No real places were found for this location.")

    # ----- Routes -----
    if results["routes"]:
        st.subheader("🛣️ Distance & Travel Time")

        for r in results["routes"]:
            st.markdown(f"### 📍 {r['name']}")
            st.write(f"**Address:** {r['address']}")
            st.write(f"🚗 **Distance:** {r['distance_km']} km")
            st.write(f"⏱️ **Travel Time:** {r['travel_time']}")
            st.divider()

    # ----- The plan -----
    st.subheader("📋 Your Event Plan")
    st.markdown(results["plan"])

    # ----- Pictures -----
    st.divider()
    st.subheader("🖼️ Decoration & Inspiration Ideas")

    if results["photos"]:
        cols = st.columns(3)

        for index, photo in enumerate(results["photos"]):
            with cols[index % 3]:
                st.image(photo["image_url"], use_container_width=True)
                st.caption(f"📸 {photo['photographer']}")
                st.markdown(f"[View photo on Unsplash]({photo['photo_url']})")
    else:
        st.warning("⚠️ No decoration images found.")


# ==============================
# EMAIL THE PLAN
# ==============================

if "event_plan" in st.session_state:

    st.divider()
    st.subheader("📧 Email Your Event Plan")

    email = st.text_input(
        "Enter your email address",
        placeholder="example@gmail.com"
    )

    if st.button("📨 Send Event Plan"):

        if not email.strip():
            st.warning("Please enter your email address.")

        else:
            with st.spinner("Sending email..."):
                success = send_email(
                    email,
                    f"Your {event_type} Event Plan 🎉",
                    st.session_state["event_plan"]
                )

            if success:
                st.success("✅ Event plan sent successfully!")
            else:
                st.error("❌ Failed to send email.")
                st.error(get_last_error())
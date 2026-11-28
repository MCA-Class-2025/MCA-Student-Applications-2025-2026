
import os
import html
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Rasoi AI | Intelligent Food Recommendation",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

ORIGINAL_FILE = os.path.join(
    PROJECT_DIR, "data", "original", "Food_Dataset.xlsx"
)

POSSIBLE_FUSED_FILES = [
    os.path.join(
        PROJECT_DIR, "FINAL_FUSED_FOOD_DATASET.csv"
    ),
    os.path.join(
        PROJECT_DIR, "data", "fused", "fused_food_dataset.csv"
    ),
    os.path.join(
        PROJECT_DIR, "data", "fused",
        "Final_Fused_Food_Dataset.csv"
    )
]

WEATHER_FILE = os.path.join(
    PROJECT_DIR, "data", "fused", "fused_weather_data.csv"
)

if not os.path.exists(WEATHER_FILE):
    WEATHER_FILE = os.path.join(
        PROJECT_DIR, "data", "api_data", "weather_data.csv"
    )

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #F7F7F2;
    color: #20251F;
}

[data-testid="stSidebar"] {
    background: #17251E;
}

[data-testid="stSidebar"] * {
    color: #F5F5EA !important;
}

[data-testid="stSidebar"] .stRadio label {
    padding: 10px 12px;
    border-radius: 9px;
}

.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 42px;
    font-weight: 700;
    color: #20372B;
    margin-bottom: 4px;
}

.subtitle {
    color: #788078;
    font-size: 15px;
    margin-bottom: 25px;
}

.hero {
    background: linear-gradient(115deg, #203B2D, #365D43);
    border-radius: 22px;
    padding: 34px;
    color: #FFFFFF;
    margin: 10px 0 25px 0;
}

.hero h1 {
    color: #FFFFFF;
    font-family: 'Playfair Display', serif;
    font-size: 36px;
    margin-bottom: 8px;
}

.hero p {
    color: #E4EDE4;
    font-size: 15px;
    max-width: 650px;
}

.section-heading {
    font-family: 'Playfair Display', serif;
    color: #20372B;
    font-size: 25px;
    font-weight: 700;
    margin: 15px 0;
}

.metric-card {
    background: #FFFFFF;
    border: 1px solid #E8EAE3;
    border-radius: 16px;
    padding: 19px;
    min-height: 112px;
}

.metric-label {
    color: #7A8379;
    font-size: 13px;
    font-weight: 600;
}

.metric-value {
    color: #20372B;
    font-size: 29px;
    font-weight: 800;
    margin-top: 7px;
}

.info-card {
    background: #FFFFFF;
    border: 1px solid #E8EAE3;
    border-radius: 15px;
    padding: 19px;
    min-height: 130px;
}

.info-card h3 {
    color: #294B35;
    font-size: 17px;
    margin-bottom: 8px;
}

.info-card p {
    color: #747D74;
    font-size: 13px;
}

.recipe-card {
    background: #FFFFFF;
    border: 1px solid #E7EAE2;
    border-radius: 14px;
    padding: 17px;
    margin-bottom: 12px;
}

.stButton > button {
    background: #2F6040;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
}

.stButton > button:hover {
    background: #244B32;
    color: white;
    border: none;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E8EAE3;
    padding: 14px;
    border-radius: 13px;
}

hr {
    border-color: #E5E9E1;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_original_data():
    if os.path.exists(ORIGINAL_FILE):
        return pd.read_excel(ORIGINAL_FILE)
    return pd.DataFrame()


@st.cache_data
def load_fused_data():
    for path in POSSIBLE_FUSED_FILES:
        if os.path.exists(path):
            if path.lower().endswith(".xlsx"):
                return pd.read_excel(path), path
            return pd.read_csv(path), path

    original = load_original_data()
    return original.copy(), ORIGINAL_FILE


@st.cache_data
def load_weather_data():
    if os.path.exists(WEATHER_FILE):
        return pd.read_csv(WEATHER_FILE)
    return pd.DataFrame()


original_df = load_original_data()
food_df, fused_file_path = load_fused_data()
weather_df = load_weather_data()


# ============================================================
# DATA PREPARATION
# ============================================================

def get_column(df, possible_names):
    """Find a column without depending on capitalization."""
    lookup = {str(col).lower(): col for col in df.columns}

    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


def numeric_column(df, possible_names):
    column = get_column(df, possible_names)

    if column is None:
        return pd.Series(dtype="float64")

    return pd.to_numeric(df[column], errors="coerce")


def get_food_name_column(df):
    return get_column(df, ["food_name", "name", "dish_name"])


def get_unique_foods(df):
    name_col = get_food_name_column(df)

    if name_col is None:
        return pd.DataFrame()

    return df.drop_duplicates(
        subset=[name_col]
    ).copy()


food_name_col = get_food_name_column(food_df)

cuisine_col = get_column(food_df, ["cuisine"])
diet_col = get_column(food_df, ["diet"])
meal_col = get_column(food_df, ["meal_type"])
calorie_col = get_column(food_df, ["calories"])
protein_col = get_column(food_df, ["protein_g", "protein"])
carbs_col = get_column(food_df, ["carbs_g", "carbs"])
fat_col = get_column(food_df, ["fat_g", "fat"])
fiber_col = get_column(food_df, ["fiber_g", "fiber"])
time_col = get_column(food_df, ["cooking_time_min", "ready_in_minutes"])
difficulty_col = get_column(food_df, ["difficulty"])
weather_suitable_col = get_column(food_df, ["weather_suitable"])


# ============================================================
# COMMON UI FUNCTIONS
# ============================================================

def page_header(title, description):
    st.markdown(
        f'<div class="main-title">{title}</div>'
        f'<div class="subtitle">{description}</div>',
        unsafe_allow_html=True
    )


def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section_title(title):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True
    )


def clean_display(value):
    if pd.isna(value):
        return "Not available"
    return str(value)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="padding:15px 5px 25px 5px;">
            <div style="font-size:34px;">🍲</div>
            <div style="font-size:25px;font-weight:800;">
                Rasoi AI
            </div>
            <div style="font-size:11px;color:#C4D5C5;">
                INTELLIGENT FOOD DISCOVERY
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    selected_page = st.radio(
        "NAVIGATION",
        [
            "Home Dashboard",
            "Food Analytics",
            "AI Food Assistant",
            "Recipe Explorer",
            "Data Fusion & APIs"
        ],
        label_visibility="visible"
    )

    st.markdown("---")

    st.caption("MCA Major Project")
    st.caption("AI Food Recommendation System")
    st.caption("Powered by RAG and Generative AI")


# ============================================================
# PAGE 1: HOME DASHBOARD
# ============================================================

if selected_page == "Home Dashboard":

    page_header(
        "Discover food intelligently.",
        "Your smart companion for recipes, nutrition and food discovery."
    )

    st.markdown("""
    <div class="hero">
        <h1>Welcome to Rasoi AI 🍲</h1>
        <p>
        Explore food information, understand nutrition, discover recipes
        and ask questions using an AI-powered food knowledge assistant.
        </p>
    </div>
    """, unsafe_allow_html=True)

    unique_food_df = get_unique_foods(food_df)

    total_records = len(food_df)
    unique_food_count = len(unique_food_df)

    avg_calories = numeric_column(
        food_df, ["calories"]
    ).mean()

    avg_protein = numeric_column(
        food_df, ["protein_g", "protein"]
    ).mean()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Dataset Records", f"{total_records:,}")

    with c2:
        metric_card("Unique Foods", f"{unique_food_count:,}")

    with c3:
        metric_card(
            "Average Calories",
            f"{avg_calories:.0f} kcal" if pd.notna(avg_calories) else "N/A"
        )

    with c4:
        metric_card(
            "Average Protein",
            f"{avg_protein:.1f} g" if pd.notna(avg_protein) else "N/A"
        )

    section_title("Explore Rasoi AI")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>📊 Food Analytics</h3>
            <p>Understand food categories, nutritional values and cooking patterns.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3>✨ AI Assistant</h3>
            <p>Ask food-related questions using the recipe knowledge base and RAG.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card">
            <h3>🍛 Recipe Explorer</h3>
            <p>Search dishes and explore their ingredients and nutritional details.</p>
        </div>
        """, unsafe_allow_html=True)

    section_title("Popular foods in the knowledge base")

    if food_name_col:
        popular = (
            food_df[food_name_col]
            .dropna()
            .value_counts()
            .head(6)
        )

        cols = st.columns(3)

        for i, (food, count) in enumerate(popular.items()):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div class="recipe-card">
                        <div style="font-size:25px;">🍽️</div>
                        <b>{html.escape(str(food))}</b>
                        <div style="color:#788078;font-size:12px;">
                            {count} dataset record(s)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.caption("Statistics are calculated from the currently loaded dataset.")


# ============================================================
# PAGE 2: FOOD ANALYTICS
# ============================================================

elif selected_page == "Food Analytics":

    page_header(
        "Food Analytics",
        "Explore patterns and nutritional information from the food dataset."
    )

    if food_df.empty:
        st.warning("Food dataset could not be loaded.")
        st.stop()

    # Cuisine distribution
    section_title("Cuisine distribution")

    if cuisine_col:
        cuisine_counts = (
            food_df[cuisine_col]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        cuisine_counts.columns = ["Cuisine", "Records"]

        col1, col2 = st.columns([1.2, 1])

        with col1:
            fig = px.pie(
                cuisine_counts,
                names="Cuisine",
                values="Records",
                hole=0.55,
                title="Food records by cuisine"
            )
            fig.update_layout(
                template="plotly_white",
                height=380,
                legend_title="Cuisine"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(
                cuisine_counts,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Cuisine information is not available.")

    # Nutrition charts
    section_title("Nutritional analysis")

    nutrition_columns = {
        "Calories": ["calories"],
        "Protein": ["protein_g", "protein"],
        "Carbohydrates": ["carbs_g", "carbs"],
        "Fat": ["fat_g", "fat"],
        "Fiber": ["fiber_g", "fiber"]
    }

    nutrition_summary = []

    for label, candidates in nutrition_columns.items():
        values = numeric_column(food_df, candidates)

        if not values.empty and values.notna().any():
            nutrition_summary.append({
                "Nutrient": label,
                "Average": values.mean()
            })

    if nutrition_summary:
        nutrition_df = pd.DataFrame(nutrition_summary)

        fig = px.bar(
            nutrition_df,
            x="Nutrient",
            y="Average",
            color="Nutrient",
            text_auto=".1f",
            title="Average nutritional composition"
        )

        fig.update_layout(
            template="plotly_white",
            height=380,
            showlegend=False,
            yaxis_title="Average value"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Diet distribution
    col1, col2 = st.columns(2)

    with col1:
        section_title("Dietary preferences")

        if diet_col:
            diet_counts = (
                food_df[diet_col]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )

            diet_counts.columns = ["Diet", "Count"]

            fig = px.bar(
                diet_counts,
                x="Diet",
                y="Count",
                color="Diet",
                text="Count",
                title="Distribution by diet type"
            )

            fig.update_layout(
                template="plotly_white",
                height=350,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Diet information is unavailable.")

    with col2:
        section_title("Meal type analysis")

        if meal_col:
            meal_counts = (
                food_df[meal_col]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )

            meal_counts.columns = ["Meal Type", "Count"]

            fig = px.pie(
                meal_counts,
                names="Meal Type",
                values="Count",
                hole=0.45,
                title="Meal type distribution"
            )

            fig.update_layout(
                template="plotly_white",
                height=350
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Meal type information is unavailable.")

    # Cooking time and calories
    section_title("Cooking time and calorie relationship")

    calories = numeric_column(food_df, ["calories"])
    cooking_time = numeric_column(
        food_df, ["cooking_time_min"]
    )

    if not calories.empty and not cooking_time.empty:
        scatter_df = pd.DataFrame({
            "Calories": calories,
            "Cooking Time (minutes)": cooking_time
        }).dropna()

        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x="Cooking Time (minutes)",
                y="Calories",
                trendline="ols" if len(scatter_df) >= 3 else None,
                title="Cooking time versus calories",
                opacity=0.7
            )

            fig.update_layout(
                template="plotly_white",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Cooking time or calorie data is unavailable.")

    st.caption(
        "All charts use available dataset values. "
        "Missing values are excluded from numerical calculations."
    )


# ============================================================
# PAGE 3: AI FOOD ASSISTANT
# ============================================================

elif selected_page == "AI Food Assistant":

    page_header(
        "Your AI Food Assistant",
        "Ask questions about recipes, ingredients, nutrition and cooking."
    )

    st.markdown("""
    <div class="hero">
        <h1>What would you like to cook today? 🍲</h1>
        <p>
        Ask about Indian recipes, cooking instructions, ingredients,
        nutrition or food-related questions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Try asking:**")

    suggestions = [
        "How do I prepare Rajma Masala?",
        "Suggest a high-protein vegetarian meal.",
        "Tell me about Paneer Tikka.",
        "What are some easy Indian dinner recipes?"
    ]

    suggestion_cols = st.columns(2)

    if "food_question" not in st.session_state:
        st.session_state.food_question = ""

    for i, suggestion in enumerate(suggestions):
        with suggestion_cols[i % 2]:
            if st.button(suggestion, key=f"suggestion_{i}"):
                st.session_state.food_question = suggestion

    question = st.text_area(
        "Enter your food-related question",
        key="food_question",
        height=110,
        placeholder="Example: Give me a healthy Indian breakfast recipe..."
    )

    if st.button("✨ Generate Answer", type="primary"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            try:
                with st.spinner("Searching your food knowledge base..."):
                    from rag.qa_chain import ask_food_question

                    answer = ask_food_question(question.strip())

                st.markdown("### 🍽️ Rasoi AI Response")
                st.markdown(answer)

            except ImportError as error:
                st.error(
                    "Could not import the existing RAG question-answering "
                    f"module. Check rag/qa_chain.py. Details: {error}"
                )

            except Exception as error:
                st.error(f"Unable to generate an answer: {error}")

    st.caption(
        "Answers are generated using your existing RAG system. "
        "Verify nutritional and medical advice with reliable sources."
    )


# ============================================================
# PAGE 4: RECIPE EXPLORER
# ============================================================

elif selected_page == "Recipe Explorer":

    page_header(
        "Recipe Explorer",
        "Explore foods from your fused dataset."
    )

    if food_df.empty or food_name_col is None:
        st.warning("Food dataset or food names are unavailable.")
        st.stop()

    unique_df = get_unique_foods(food_df)

    search = st.text_input(
        "🔍 Search for a food",
        placeholder="Search Rajma, Paneer, Biryani..."
    )

    filtered_df = unique_df.copy()

    if search.strip():
        filtered_df = filtered_df[
            filtered_df[food_name_col]
            .astype(str)
            .str.contains(search, case=False, na=False)
        ]

    filter_cols = st.columns(3)

    if cuisine_col:
        cuisines = sorted(
            food_df[cuisine_col].dropna().astype(str).unique()
        )

        with filter_cols[0]:
            selected_cuisine = st.selectbox(
                "Cuisine",
                ["All"] + cuisines
            )

        if selected_cuisine != "All":
            filtered_df = filtered_df[
                filtered_df[cuisine_col].astype(str) == selected_cuisine
            ]

    if diet_col:
        diets = sorted(
            food_df[diet_col].dropna().astype(str).unique()
        )

        with filter_cols[1]:
            selected_diet = st.selectbox(
                "Diet type",
                ["All"] + diets
            )

        if selected_diet != "All":
            filtered_df = filtered_df[
                filtered_df[diet_col].astype(str) == selected_diet
            ]

    if meal_col:
        meal_types = sorted(
            food_df[meal_col].dropna().astype(str).unique()
        )

        with filter_cols[2]:
            selected_meal = st.selectbox(
                "Meal type",
                ["All"] + meal_types
            )

        if selected_meal != "All":
            filtered_df = filtered_df[
                filtered_df[meal_col].astype(str) == selected_meal
            ]

    st.write(f"**{len(filtered_df)} food results found**")

    for start in range(0, len(filtered_df), 3):
        cols = st.columns(3)

        for offset, (_, row) in enumerate(
            filtered_df.iloc[start:start + 3].iterrows()
        ):
            with cols[offset]:
                food_name = clean_display(row[food_name_col])

                st.markdown(
                    f"""
                    <div class="recipe-card">
                        <div style="font-size:27px;">🍛</div>
                        <h3 style="color:#294B35;">
                            {html.escape(food_name)}
                        </h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if cuisine_col:
                    st.caption(
                        "Cuisine: " + clean_display(row[cuisine_col])
                    )

                if calorie_col:
                    st.caption(
                        "Calories: " + clean_display(row[calorie_col])
                    )

                if protein_col:
                    st.caption(
                        "Protein: " + clean_display(row[protein_col]) + " g"
                    )

                if time_col:
                    st.caption(
                        "Cooking time: " + clean_display(row[time_col])
                        + " minutes"
                    )

                with st.expander("View food details"):
                    for column in [
                        "ingredients",
                        "difficulty",
                        "health_category",
                        "weather_suitable"
                    ]:
                        actual_col = get_column(food_df, [column])

                        if actual_col:
                            st.write(
                                f"**{column.replace('_', ' ').title()}:** "
                                f"{clean_display(row[actual_col])}"
                            )

    if filtered_df.empty:
        st.info("No matching foods found. Try another search.")


# ============================================================
# PAGE 5: DATA FUSION & API INSIGHTS
# ============================================================

elif selected_page == "Data Fusion & APIs":

    page_header(
        "Data Fusion & API Insights",
        "Understand how multiple data sources enrich the food knowledge base."
    )

    original_count = len(original_df)
    fused_count = len(food_df)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card("Original Records", f"{original_count:,}")

    with c2:
        metric_card("Fused Records", f"{fused_count:,}")

    with c3:
        metric_card("Weather Locations", f"{len(weather_df):,}")

    section_title("Integrated data sources")

    api_sources = [
        ("USDA FoodData Central", "Nutrition information"),
        ("Spoonacular", "Recipe and ingredient information"),
        ("TheMealDB", "Meal and preparation information"),
        ("OpenWeatherMap", "Current weather information"),
        ("Groq", "AI answer generation")
    ]

    api_cols = st.columns(2)

    for i, (name, description) in enumerate(api_sources):
        with api_cols[i % 2]:
            st.markdown(
                f"""
                <div class="info-card">
                    <h3>🔗 {name}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    section_title("API matching coverage")

    coverage = []

    for prefix, label in [
        ("usda_", "USDA"),
        ("spoonacular_", "Spoonacular"),
        ("themealdb_", "TheMealDB")
    ]:
        columns = [
            col for col in food_df.columns
            if col.lower().startswith(prefix)
        ]

        if columns:
            matched = (
                food_df[columns]
                .notna()
                .any(axis=1)
                .sum()
            )
        else:
            matched = 0

        coverage.append({
            "API Source": label,
            "Matched Records": int(matched),
            "Unmatched Records": int(max(0, len(food_df) - matched))
        })

    coverage_df = pd.DataFrame(coverage)

    fig = px.bar(
        coverage_df,
        x="API Source",
        y="Matched Records",
        color="API Source",
        text="Matched Records",
        title="Food records enriched by each API"
    )

    fig.update_layout(
        template="plotly_white",
        height=380,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        coverage_df,
        use_container_width=True,
        hide_index=True
    )

    section_title("Weather information")

    if not weather_df.empty:
        st.dataframe(
            weather_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "Weather data is not available. "
            "Run the weather API collection process first."
        )

    section_title("Final fused dataset preview")

    st.write(
        f"Loaded file: `{os.path.basename(fused_file_path)}`"
    )

    st.dataframe(
        food_df.head(20),
        use_container_width=True,
        hide_index=True
    )

    csv_data = food_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "⬇️ Download fused dataset CSV",
        data=csv_data,
        file_name="FINAL_FUSED_FOOD_DATASET.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center;color:#879087;padding:15px;">
        <b>Rasoi AI</b> · AI Food Recommendation System<br>
    </div>
    """,
    unsafe_allow_html=True
)

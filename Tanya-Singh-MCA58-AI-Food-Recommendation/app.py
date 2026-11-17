import streamlit as st
import os
import sys
from pathlib import Path


st.set_page_config(
    page_title="AI Food Recommendation Assistant",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

# Make sure project directory is available
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# IMPORT RAG FUSION
# ============================================================

try:
    from rag_fusion import ask_food_question
    RAG_AVAILABLE = True

except Exception as e:
    RAG_AVAILABLE = False
    RAG_IMPORT_ERROR = str(e)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */
    .main {
        padding-top: 1rem;
    }

    /* Title */
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        color: #666;
        margin-bottom: 25px;
    }

    /* Recommendation box */
    .recommendation-box {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        background-color: #fafafa;
        margin-top: 15px;
    }

    /* API status */
    .api-status {
        padding: 6px 10px;
        border-radius: 6px;
        margin-bottom: 5px;
        font-size: 14px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        width: 310px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🍲 AI Food Recommendation")

    st.caption("RAG + Data Fusion + Multi-API System")

    st.divider()

    # --------------------------------------------------------
    # PROJECT COMPONENTS
    # --------------------------------------------------------

    st.markdown("### 🤖 AI System")

    st.markdown(
        """
        - **Gemini LLM**
        - **RAG**
        - **FAISS Vector Search**
        - **Automatic Local Fallback**
        """
    )

    st.divider()

    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    st.markdown("### 📚 Knowledge Base")

    st.markdown(
        """
        - **Food Dataset**
          - 51 Indian food records
          - Nutrition information
          - Ingredients
          - Diet information
          - Health category

        - **Indian Recipe PDF**
          - Recipe knowledge
          - Ingredients
          - Cooking instructions
          - Indian dishes
        """
    )

    st.divider()

    # --------------------------------------------------------
    # EXTERNAL APIS
    # --------------------------------------------------------

    st.markdown("### 🌐 External APIs")

    st.markdown(
        """
        - 🥗 **USDA FoodData Central**
          - Nutrition information

        - 🌦️ **OpenWeatherMap**
          - Weather information
          - Weather-based recommendations

        - 🍝 **Spoonacular**
          - Recipe information
          - Ingredients
          - Cooking information

        - 🍽️ **TheMealDB**
          - Meal and recipe information

        - 🤖 **Google Gemini**
          - AI-generated response
          - Natural-language recommendation
        """
    )

    st.divider()

    # --------------------------------------------------------
    # DATA FUSION
    # --------------------------------------------------------

    st.markdown("### 🔗 Data Fusion")

    st.markdown(
        """
        - Local Dataset
        - Recipe PDF
        - RAG Retrieval
        - USDA Nutrition
        - Weather Data
        - External Recipes
        - Gemini AI
        """
    )

    st.divider()

    # --------------------------------------------------------
    # PROJECT FEATURES
    # --------------------------------------------------------

    st.markdown("### ✨ Features")

    st.markdown(
        """
        - 🍛 Recipe recommendations
        - 🥗 Nutrition information
        - 💪 Protein information
        - 🍚 Carbohydrates
        - 🧈 Fat and fiber
        - 📝 Ingredients
        - 👨‍🍳 Cooking instructions
        - 🌦️ Weather-aware recommendations
        - 🔎 Semantic search
        - 📚 PDF knowledge retrieval
        - 🔗 Multi-source data fusion
        - 🛡️ Local fallback
        """
    )

    st.divider()

    # --------------------------------------------------------
    # DATA SOURCES
    # --------------------------------------------------------

    st.markdown("### 📂 Local Sources")

    csv_path = BASE_DIR / "data" / "food_dataset.csv"
    pdf_path = BASE_DIR / "recipes" / "Indian_dishes.pdf"

    if csv_path.exists():
        st.success("✓ Food Dataset")

    else:
        st.error("✗ Food Dataset missing")

    if pdf_path.exists():
        st.success("✓ Indian Recipe PDF")

    else:
        st.warning("⚠ Indian Recipe PDF missing")

    st.divider()

    st.caption("AI Food Recommendation System")
    st.caption("RAG • FAISS • Gemini • Data Fusion")


# ============================================================
# MAIN PAGE
# ============================================================

st.markdown(
    '<div class="main-title">🍲 AI Food Recommendation Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Get intelligent food recommendations using RAG, FAISS, Gemini, '
    'local food data and external APIs.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SYSTEM STATUS
# ============================================================

if not RAG_AVAILABLE:

    st.error("⚠️ RAG system could not be loaded.")

    with st.expander("Technical error"):
        st.code(RAG_IMPORT_ERROR)

    st.info(
        "Make sure rag_fusion.py is working correctly by running "
        "`python rag_fusion.py` from the project folder."
    )

    st.stop()


# ============================================================
# ASK QUESTION
# ============================================================

st.markdown("### 💬 Ask Your Food Question")

question = st.text_area(
    "What would you like to know?",
    placeholder=(
        "Examples:\n"
        "• Give me an easy Rajma recipe\n"
        "• Give me a Paneer Tikka recipe\n"
        "• How do I make Chicken Biryani?\n"
        "• What are the ingredients for Dal Tadka?\n"
        "• Give me the nutrition information for Rajma\n"
        "• Which Indian food is high in protein?\n"
        "• Give me a healthy vegetarian dinner\n"
        "• Give me an easy recipe for a rainy day"
    ),
    height=140,
    label_visibility="visible"
)


# ============================================================
# RECOMMEND BUTTON
# ============================================================

recommend_button = st.button(
    "🍲 Recommend Food",
    type="primary",
    use_container_width=True
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if recommend_button:

    if not question.strip():

        st.warning("Please enter a food question first.")

    else:

        with st.spinner(
            "🔎 Searching knowledge base and external food sources..."
        ):

            try:

                # ------------------------------------------------
                # CALL RAG + DATA FUSION
                # ------------------------------------------------

                result = ask_food_question(question.strip())

                # Save result in session state
                st.session_state["food_result"] = result
                st.session_state["food_question"] = question.strip()

            except Exception as e:

                st.session_state["food_result"] = None
                st.session_state["food_error"] = str(e)


# ============================================================
# DISPLAY RESULT
# ============================================================

if "food_error" in st.session_state:

    st.error("❌ Unable to generate the recommendation.")

    with st.expander("Technical details"):
        st.code(st.session_state["food_error"])

    del st.session_state["food_error"]


elif "food_result" in st.session_state:

    result = st.session_state["food_result"]

    st.success("Recommendation ready!")

    st.markdown("### 🍽️ Recommendation")

    # ----------------------------------------------------------
    # RESULT IS A STRING
    # ----------------------------------------------------------

    if isinstance(result, str):

        st.markdown(
            '<div class="recommendation-box">',
            unsafe_allow_html=True
        )

        st.markdown(result)

        st.markdown("</div>", unsafe_allow_html=True)


    # ----------------------------------------------------------
    # RESULT IS A DICTIONARY
    # ----------------------------------------------------------

    elif isinstance(result, dict):

        # --------------------------------------------
        # AI ANSWER
        # --------------------------------------------

        answer = (
            result.get("answer")
            or result.get("response")
            or result.get("recommendation")
            or result.get("final_answer")
            or result.get("text")
        )

        if answer:

            st.markdown(
                '<div class="recommendation-box">',
                unsafe_allow_html=True
            )

            st.markdown(answer)

            st.markdown("</div>", unsafe_allow_html=True)



        food = (
            result.get("food")
            or result.get("food_info")
            or result.get("local_food")
        )

        if isinstance(food, dict):

            st.markdown("### 🥗 Food Information")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                calories = food.get("calories", "N/A")
                st.metric("Calories", str(calories))

            with col2:
                protein = food.get("protein", "N/A")
                st.metric("Protein", str(protein))

            with col3:
                carbs = food.get("carbs", "N/A")
                st.metric("Carbs", str(carbs))

            with col4:
                fat = food.get("fat", "N/A")
                st.metric("Fat", str(fat))

            # More nutrition information

            fiber = food.get("fiber")

            if fiber is not None:
                st.write(f"🌾 **Fiber:** {fiber} g")

            diet = food.get("diet")

            if diet:
                st.write(f"🥗 **Diet:** {diet}")

            health = food.get("health_category")

            if health:
                st.write(f"💚 **Health Category:** {health}")

            ingredients = food.get("ingredients")

            if ingredients:
                st.markdown("### 🧂 Ingredients")

                if isinstance(ingredients, str):

                    ingredient_list = ingredients.replace(
                        ";", "\n"
                    ).splitlines()

                    for item in ingredient_list:

                        if item.strip():
                            st.markdown(
                                f"- {item.strip()}"
                            )

                elif isinstance(ingredients, list):

                    for item in ingredients:
                        st.markdown(f"- {item}")


        recipe = result.get("recipe")

        if isinstance(recipe, dict):

            st.markdown("### 👨‍🍳 Recipe")

            recipe_name = recipe.get("name")

            if recipe_name:
                st.markdown(
                    f"#### 🍽️ {recipe_name}"
                )

            recipe_ingredients = recipe.get(
                "ingredients"
            )

            if recipe_ingredients:

                st.markdown("##### 🧂 Ingredients")

                if isinstance(recipe_ingredients, str):

                    for item in recipe_ingredients.splitlines():

                        if item.strip():
                            st.markdown(
                                f"- {item.strip()}"
                            )

                elif isinstance(recipe_ingredients, list):

                    for item in recipe_ingredients:
                        st.markdown(f"- {item}")


            instructions = recipe.get(
                "instructions"
            )

            if instructions:

                st.markdown(
                    "##### 👨‍🍳 Cooking Instructions"
                )

                if isinstance(instructions, str):

                    st.markdown(instructions)

                elif isinstance(instructions, list):

                    for i, step in enumerate(
                        instructions,
                        start=1
                    ):
                        st.markdown(
                            f"**Step {i}:** {step}"
                        )


      
        nutrition = result.get("nutrition")

        if isinstance(nutrition, dict):

            st.markdown("### 💪 Nutrition")

            nutrition_items = []

            for key, value in nutrition.items():

                if value is not None:

                    nutrition_items.append(
                        (key.replace("_", " ").title(), value)
                    )

            if nutrition_items:

                columns = st.columns(
                    min(4, len(nutrition_items))
                )

                for i, (name, value) in enumerate(
                    nutrition_items
                ):

                    with columns[i % len(columns)]:
                        st.metric(
                            name,
                            str(value)
                        )


        weather = result.get("weather")

        if isinstance(weather, dict):

            st.markdown("### 🌦️ Weather")

            weather_text = []

            for key, value in weather.items():

                if value is not None:

                    weather_text.append(
                        f"**{key.replace('_', ' ').title()}:** {value}"
                    )

            for item in weather_text:
                st.write(item)


        sources = result.get("sources")

        if sources:

            st.markdown("### 🔗 Data Sources")

            if isinstance(sources, list):

                for source in sources:

                    st.markdown(
                        f"- {source}"
                    )

            elif isinstance(sources, dict):

                for name, value in sources.items():

                    st.markdown(
                        f"- **{name}:** {value}"
                    )

            else:

                st.write(sources)


     
        if not answer and not food and not recipe:

            st.markdown(
                '<div class="recommendation-box">',
                unsafe_allow_html=True
            )

            st.write(result)

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

    else:

        st.write(result)

if (
    "food_result" not in st.session_state
    and "food_error" not in st.session_state
):

    st.info(
        "💡 Ask a question such as "
        "**'Give me an easy Rajma recipe'** "
        "to get a recipe, ingredients, cooking instructions "
        "and nutrition information."
    )
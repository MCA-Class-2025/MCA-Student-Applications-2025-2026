"""Streamlit presentation for recipes and validated USDA food data."""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

from utils.nutrition import (
    calculate_recipe_nutrition,
    filter_recipes,
    format_nutrient,
    format_recipe_ingredient,
    get_food_record,
    get_usda_food_names,
    load_recipes,
    load_usda_foods,
)
from utils.recipe_ai import RecipeAIError, RecipeRequest, generate_recipes


def _unique_values(recipes, field):
    return sorted({str(recipe[field]) for recipe in recipes if recipe.get(field)})


def _unique_list_values(recipes, field):
    return sorted({
        str(value)
        for recipe in recipes
        for value in recipe.get(field, [])
    })


def _render_recipe_card(recipe, usda_foods):
    total_time = int(recipe.get("prep_time", 0) + recipe.get("cook_time", 0))
    with st.container(border=True):
        st.markdown(f"### 🍽️ {recipe['name']}")
        st.caption(
            f"{recipe['meal_type']} · {recipe['diet']} · "
            f"{recipe['difficulty']} · {total_time} min · "
            f"{recipe.get('servings', 1)} servings"
        )
        st.markdown(
            "**Nutrition focus:** " + ", ".join(recipe.get("nutrition_focus", []))
        )
        st.markdown(
            "**Cycle-phase tags:** " + ", ".join(recipe.get("cycle_phases", []))
        )
        allergens = recipe.get("allergens", [])
        st.markdown(
            "**Declared allergens:** "
            + (", ".join(allergens) if allergens else "None in the recipe data")
        )

        with st.expander("Ingredients and instructions"):
            st.markdown("**Measured ingredients**")
            for ingredient in recipe.get(
                "ingredients_detailed", recipe.get("ingredients", [])
            ):
                st.markdown(f"- {format_recipe_ingredient(ingredient)}")
            st.markdown("**Instructions**")
            for number, step in enumerate(recipe.get("instructions", []), start=1):
                st.write(f"{number}. {step}")

        nutrition = calculate_recipe_nutrition(recipe, usda_foods)
        with st.expander("Nutrition calculation"):
            if not nutrition["complete"]:
                st.info(
                    f"Validated USDA ingredient coverage: "
                    f"{nutrition['coverage_percent']:.1f}%. Per-serving totals are hidden "
                    "until every measured ingredient has a mapped food record."
                )
            else:
                values = nutrition["values"]
                columns = st.columns(4)
                columns[0].metric(
                    "Energy / serving",
                    format_nutrient(values.get("energy_kcal_100g"), "kcal"),
                )
                columns[1].metric(
                    "Protein / serving",
                    format_nutrient(values.get("protein_g_100g"), "g"),
                )
                columns[2].metric(
                    "Iron / serving",
                    format_nutrient(values.get("iron_mg_100g"), "mg"),
                )
                columns[3].metric(
                    "Fiber / serving",
                    format_nutrient(values.get("fiber_g_100g"), "g"),
                )
                st.caption(
                    "Calculated from the measured ingredient weights and the locally "
                    "stored USDA values. These are estimates, not dietary prescriptions."
                )


def _scaled_value(food, column, portion_grams):
    value = food.get(column)
    if pd.isna(value):
        return None
    return float(value) * float(portion_grams) / 100


def _setting(name):
    """Read a server-side setting without exposing it in the interface."""

    value = os.getenv(name)
    if value:
        return value

    # Windows `setx` writes user variables to the registry, but processes that
    # were already open (including some IDE-launched Streamlit servers) do not
    # inherit the updated environment. Read the current user's setting as a
    # fallback so the app can still discover it without displaying the secret.
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
            if value:
                return str(value).strip()
        except (ImportError, FileNotFoundError, OSError):
            pass

    try:
        value = st.secrets.get(name)
    except (FileNotFoundError, KeyError):
        value = None
    return str(value).strip() if value else None


def _configured_recipe_providers():
    providers = {}
    openai_key = _setting("OPENAI_API_KEY")
    gemini_key = _setting("GEMINI_API_KEY")
    if openai_key:
        providers["OpenAI"] = {
            "key": openai_key,
            "model": _setting("OPENAI_RECIPE_MODEL"),
        }
    if gemini_key:
        providers["Gemini"] = {
            "key": gemini_key,
            "model": _setting("GEMINI_RECIPE_MODEL"),
        }
    return providers


def _recipe_result_markdown(result):
    lines = ["# FemCare AI Recipe Suggestions", ""]
    for recipe in result.get("recipes", []):
        lines.extend([
            f"## {recipe['name']}",
            recipe["why_it_matches"],
            "",
            (
                f"Servings: {recipe['servings']} | Prep: "
                f"{recipe['prep_time_minutes']} min | Cook: "
                f"{recipe['cook_time_minutes']} min | Total: "
                f"{recipe['total_time_minutes']} min | Difficulty: "
                f"{recipe['difficulty']}"
            ),
            "",
            "### Ingredients",
        ])
        for ingredient in recipe.get("ingredients", []):
            optional = " (optional)" if ingredient.get("optional") else ""
            lines.append(
                f"- {ingredient['quantity']} {ingredient['name']}{optional}"
            )
        lines.extend(["", "### Method"])
        for number, step in enumerate(recipe.get("steps", []), start=1):
            lines.append(f"{number}. {step}")
        if recipe.get("substitutions"):
            lines.extend(["", "### Substitutions"])
            lines.extend(f"- {item}" for item in recipe["substitutions"])
        lines.extend([
            "",
            "### Allergens and storage",
            "- Allergens: " + (", ".join(recipe.get("allergens", [])) or "None identified"),
            f"- Storage: {recipe['storage']}",
        ])
        if recipe.get("safety_notes"):
            lines.extend(f"- Safety: {item}" for item in recipe["safety_notes"])
        lines.append("")
    return "\n".join(lines)


def _render_generated_recipes(result, provider, model):
    st.success(f"Created {len(result['recipes'])} recipe suggestion(s).")
    st.caption(f"Generated by {provider} · {model} · Times are estimates")
    for recipe in result["recipes"]:
        with st.container(border=True):
            st.markdown(f"### ✨ {recipe['name']}")
            st.write(recipe["why_it_matches"])
            metrics = st.columns(5)
            metrics[0].metric("Servings", recipe["servings"])
            metrics[1].metric("Prep", f"{recipe['prep_time_minutes']} min")
            metrics[2].metric("Cook", f"{recipe['cook_time_minutes']} min")
            metrics[3].metric("Total", f"{recipe['total_time_minutes']} min")
            metrics[4].metric("Difficulty", recipe["difficulty"])

            ingredient_col, method_col = st.columns([1, 1.4])
            with ingredient_col:
                st.markdown("**Ingredients**")
                for ingredient in recipe.get("ingredients", []):
                    optional = " _(optional)_" if ingredient.get("optional") else ""
                    st.markdown(
                        f"- **{ingredient['quantity']}** {ingredient['name']}{optional}"
                    )
            with method_col:
                st.markdown("**Method**")
                for number, step in enumerate(recipe.get("steps", []), start=1):
                    st.write(f"{number}. {step}")

            with st.expander("Substitutions, allergens, storage and safety"):
                st.markdown("**Substitutions**")
                substitutions = recipe.get("substitutions", [])
                if substitutions:
                    for item in substitutions:
                        st.markdown(f"- {item}")
                else:
                    st.write("No substitutions suggested.")
                st.markdown(
                    "**Possible allergens:** "
                    + (", ".join(recipe.get("allergens", [])) or "None identified")
                )
                st.markdown(f"**Storage:** {recipe['storage']}")
                if recipe.get("safety_notes"):
                    st.markdown("**Food-safety notes**")
                    for item in recipe["safety_notes"]:
                        st.markdown(f"- {item}")

    if result.get("general_notes"):
        with st.expander("General notes"):
            for note in result["general_notes"]:
                st.markdown(f"- {note}")
    st.download_button(
        "📥 Download these recipes",
        data=_recipe_result_markdown(result),
        file_name="femcare_ai_recipes.md",
        mime="text/markdown",
        use_container_width=True,
        key="download_ai_recipes",
    )


def _render_ai_recipe_assistant():
    st.divider()
    st.subheader("✨ AI Recipe Assistant")
    st.write(
        "Describe what you want to make and the ingredients you have. The assistant "
        "creates up to five suitable recipes with quantities, timings, steps, "
        "substitutions, allergens, storage guidance and food-safety notes."
    )
    st.caption(
        "This feature uses the selected cloud LLM, not the USDA dataset. Only the "
        "recipe request below is sent to that provider; FemCare health records are not sent."
    )

    providers = _configured_recipe_providers()
    if not providers:
        st.info(
            "Recipe AI is ready but no cloud key is configured. Add OPENAI_API_KEY or "
            "GEMINI_API_KEY to your environment or Streamlit secrets, then restart the app."
        )

    with st.form("recipe_ai_form"):
        request = st.text_area(
            "What would you like to cook?",
            placeholder=(
                "Example: Give me quick dinner ideas using these ingredients. "
                "I prefer something spicy and suitable for meal prep."
            ),
            height=90,
        )
        ingredients = st.text_area(
            "Available ingredients",
            placeholder="Example: chickpeas, tomatoes, spinach, rice, onion, garlic",
            height=90,
        )
        first_row = st.columns(3)
        with first_row[0]:
            dietary_preference = st.selectbox(
                "Dietary preference",
                [
                    "No preference",
                    "Vegetarian",
                    "Vegan",
                    "Pescatarian",
                    "Gluten-free",
                    "Dairy-free",
                ],
            )
        with first_row[1]:
            cuisine = st.text_input(
                "Cuisine preference", placeholder="Any, Indian, Italian…"
            )
        with first_row[2]:
            allergens = st.text_input(
                "Exclude allergens", placeholder="Example: peanuts, dairy"
            )

        second_row = st.columns(4)
        with second_row[0]:
            servings = st.number_input(
                "Servings", min_value=1, max_value=12, value=2, step=1
            )
        with second_row[1]:
            max_time = st.slider(
                "Maximum total time", 5, 240, 45, 5, format="%d min"
            )
        with second_row[2]:
            recipe_count = st.slider("Number of ideas", 1, 5, 3)
        with second_row[3]:
            provider = st.selectbox(
                "Recipe AI provider",
                list(providers) if providers else ["Not configured"],
            )

        submitted = st.form_submit_button(
            "✨ Generate recipes",
            type="primary",
            use_container_width=True,
            disabled=not providers,
        )

    if submitted:
        if not request.strip() or not ingredients.strip():
            st.warning("Enter both a cooking request and the ingredients you have.")
        else:
            try:
                recipe_request = RecipeRequest(
                    request=request,
                    available_ingredients=ingredients,
                    dietary_preference=dietary_preference,
                    excluded_allergens=allergens or "None specified",
                    cuisine_preference=cuisine or "Any cuisine",
                    servings=int(servings),
                    maximum_total_time_minutes=int(max_time),
                    recipe_count=int(recipe_count),
                )
                config = providers[provider]
                with st.spinner(f"{provider} is creating recipe ideas…"):
                    response, model = generate_recipes(
                        provider,
                        recipe_request,
                        api_key=config["key"],
                        model=config["model"],
                    )
                st.session_state.recipe_ai_result = response.model_dump()
                st.session_state.recipe_ai_provider = provider
                st.session_state.recipe_ai_model = model
            except (RecipeAIError, ValueError) as exc:
                st.error(str(exc))

    result = st.session_state.get("recipe_ai_result")
    if result:
        clear_col, _ = st.columns([1, 4])
        with clear_col:
            if st.button("Clear AI recipes", key="clear_ai_recipes"):
                for key in (
                    "recipe_ai_result",
                    "recipe_ai_provider",
                    "recipe_ai_model",
                ):
                    st.session_state.pop(key, None)
                st.rerun()
        _render_generated_recipes(
            result,
            st.session_state.get("recipe_ai_provider", "Recipe AI"),
            st.session_state.get("recipe_ai_model", "configured model"),
        )


def _render_food_explorer(usda_foods):
    st.divider()
    st.subheader("🔬 USDA Food Explorer")
    st.write(
        "Inspect the locally collected USDA FoodData Central records. Choose a portion "
        "to scale the stored values from their 100 g reference."
    )

    if usda_foods.empty:
        st.warning("USDA nutrition data is not available.")
        return

    validated = int(usda_foods["record_status"].eq("Validated").sum())
    summary_columns = st.columns(3)
    summary_columns[0].metric("Food records", len(usda_foods))
    summary_columns[1].metric("Validated core records", validated)
    summary_columns[2].metric("Records needing review", len(usda_foods) - validated)

    food_names = get_usda_food_names(usda_foods)
    if not food_names:
        st.warning("No food names are available in the USDA dataset.")
        return

    food_col, portion_col = st.columns([2, 1])
    with food_col:
        selected_food = st.selectbox(
            "Food", food_names, key="usda_food_selector"
        )
    with portion_col:
        portion = st.number_input(
            "Portion size (g)", min_value=1, max_value=1000,
            value=100, step=10, key="usda_portion_grams",
        )

    food = get_food_record(usda_foods, selected_food)
    if food is None:
        return

    st.markdown(f"### {food['food_name']}")
    source_text = (
        f"USDA FoodData Central · {food['data_type']} · "
        f"FDC ID {int(food['fdc_id'])}"
    )
    if pd.notna(food.get("collected_at_utc")):
        source_text += f" · Collected {food['collected_at_utc']}"
    st.caption(source_text)

    status = str(food.get("record_status", "Review"))
    if status == "Validated":
        st.success("Core energy and macronutrient checks passed for this record.")
    else:
        st.warning(
            "This record needs review: "
            + str(food.get("validation_notes") or "validation details unavailable")
        )

    quality_note = str(food.get("energy_quality_note") or "").strip()
    if quality_note and quality_note.lower() != "nan":
        st.warning(f"Energy data quality note: {quality_note}")

    st.markdown(f"**Nutrition values for {portion:g} g**")
    nutrient_rows = [
        ("Energy", "energy_kcal_100g", "kcal"),
        ("Protein", "protein_g_100g", "g"),
        ("Carbohydrates", "carbohydrates_g_100g", "g"),
        ("Fat", "fat_g_100g", "g"),
        ("Iron", "iron_mg_100g", "mg"),
        ("Magnesium", "magnesium_mg_100g", "mg"),
        ("Calcium", "calcium_mg_100g", "mg"),
        ("Fiber", "fiber_g_100g", "g"),
        ("Vitamin B6", "vitamin_b6_mg_100g", "mg"),
        ("Vitamin B12", "vitamin_b12_ug_100g", "µg"),
    ]
    for start in range(0, len(nutrient_rows), 4):
        columns = st.columns(4)
        for column, (label, key, unit) in zip(columns, nutrient_rows[start:start + 4]):
            column.metric(
                label,
                format_nutrient(_scaled_value(food, key, portion), unit),
            )

    st.caption(
        "Missing USDA values remain 'Not available'; they are never treated as zero. "
        "Portion scaling is arithmetic and does not account for cooking-related changes."
    )


def render_nutrition_guide():
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🍎 FemCare Nutrition Guide</div>
            <p class="hero-subtitle">
                Explore measured recipes and inspect validated USDA food records.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Nutrition information is for general education. Allergy declarations depend "
        "on the listed ingredients and do not address cross-contamination."
    )

    recipes = load_recipes()
    usda_foods = load_usda_foods()
    st.subheader("🥗 Recipe Finder")

    if not recipes:
        st.warning("Recipe data is not available.")
        _render_food_explorer(usda_foods)
        return

    max_time_available = max(
        int(recipe.get("prep_time", 0) + recipe.get("cook_time", 0))
        for recipe in recipes
    )
    with st.container(border=True):
        first_row = st.columns(4)
        with first_row[0]:
            nutrition_focus = st.selectbox(
                "Nutrition focus", ["All", *_unique_list_values(recipes, "nutrition_focus")]
            )
        with first_row[1]:
            diet = st.selectbox("Diet", ["All", *_unique_values(recipes, "diet")])
        with first_row[2]:
            meal_type = st.selectbox(
                "Meal type", ["All", *_unique_values(recipes, "meal_type")]
            )
        with first_row[3]:
            cycle_phase = st.selectbox(
                "Cycle-phase tag", ["All", *_unique_list_values(recipes, "cycle_phases")]
            )

        second_row = st.columns([1.4, 1.2, 1])
        with second_row[0]:
            search_text = st.text_input(
                "Search recipes or ingredients", placeholder="Spinach, lentils, breakfast…"
            )
        with second_row[1]:
            excluded_allergens = st.multiselect(
                "Exclude declared allergens", _unique_list_values(recipes, "allergens")
            )
        with second_row[2]:
            max_total_time = st.slider(
                "Maximum total time", min_value=5, max_value=max_time_available,
                value=max_time_available, step=5, format="%d min",
            )

    filtered = filter_recipes(
        recipes,
        nutrition_focus=nutrition_focus,
        diet=diet,
        meal_type=meal_type,
        cycle_phase=cycle_phase,
        max_prep_time=max_total_time,
        excluded_allergens=excluded_allergens,
        search_text=search_text,
    )
    st.caption(f"Showing {len(filtered)} of {len(recipes)} recipes.")

    if not filtered:
        st.warning("No recipes match the selected filters.")
    else:
        for start in range(0, len(filtered), 3):
            columns = st.columns(3)
            for column, recipe in zip(columns, filtered[start:start + 3]):
                with column:
                    _render_recipe_card(recipe, usda_foods)

    _render_ai_recipe_assistant()
    _render_food_explorer(usda_foods)


import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from services.pexels_service import search_destination_image

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ AI Travel Planner")
st.write("Plan personalized trips using Artificial Intelligence.")

st.divider()

st.subheader("🤖 Test the AI Travel Assistant")

user_question = st.text_area(
    "Ask your travel question",
    placeholder="Example: Plan a 5-day trip to Dubai."
)

destination = st.text_input(
    "Enter destination for travel images",
    placeholder="Example: Dubai"
)

if st.button("Ask AI"):

    if not user_question:
        st.warning("Please enter a travel question.")

    else:
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI Travel Planner. "
                            "Create a complete day-by-day itinerary. "
                            "Include morning, afternoon and evening activities. "
                            "Consider destination and budget. "
                            "Include estimated costs. "
                            "Use clear headings and tables where useful. "
                            "Do not generate image URLs, HTML image tags, "
                            "or Unsplash/Pexels image links."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_question
                    }
                ],
                temperature=0.5,
                max_completion_tokens=4096
            )

            answer = response.choices[0].message.content

            st.subheader("🤖 AI Response")
            st.markdown(answer)

            if destination.strip():
                st.divider()
                st.subheader("📸 Destination Image")

                image_data = search_destination_image(
                    destination.strip()
                )

                if image_data:
                    st.image(
                        image_data["image_url"],
                        caption=f'Photo by {image_data["photographer"]}'
                    )
                    st.markdown(
                        f"[View original image on Pexels]({image_data['pexels_url']})"
                    )
                else:
                    st.warning("No destination image found.")

        except Exception as e:
            st.error(f"Error: {e}")

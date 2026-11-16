import unittest
from unittest.mock import patch

import app


class WeatherLocationTests(unittest.TestCase):
    def test_country_question_requests_a_city_without_looking_up_weather(self):
        request = app.WeatherQuestion(
            question="What is the temperature in India?"
        )

        with patch.object(app, "get_current_weather") as get_current_weather:
            response = app.ask_weather(request)

        self.assertEqual(response["ai_status"], "clarification")
        self.assertIsNone(response["city"])
        self.assertIn("Which city", response["answer"])
        get_current_weather.assert_not_called()

    def test_country_name_in_followup_context_is_not_parsed_as_a_city(self):
        self.assertIsNone(app.extract_city(
            "India is a country, so I need a city to look up local weather. "
            "Which city would you like?"
        ))

    def test_historical_search_filters_by_city_and_alias(self):
        with patch.object(
            app.vectorstore,
            "similarity_search",
            return_value=[]
        ) as similarity_search:
            app.get_historical_weather(
                "Historical weather in Bengaluru",
                city="Bengaluru"
            )

        similarity_search.assert_called_once_with(
            "Historical weather in Bengaluru",
            k=5,
            filter={"city": "Bangalore"}
        )


if __name__ == "__main__":
    unittest.main()

from services.travel_data_service import get_destination_context
from services.llm_service import generate_response


def create_travel_plan(
    destination,
    days=3,
    budget=80000
):

    context = get_destination_context(destination)

    if context is None:
        return (
            f"Sorry, no travel data was found "
            f"for {destination}."
        )

    places_text = "\n".join(
        f"- {place}"
        for place in context["places"]
    )

    prompt = f"""
You are an AI Travel Planner.

Create a practical, natural-sounding {days}-day travel
plan for {context['destination']}.

The user's total budget is ₹{budget}.

==================================================
PROJECT DATA RULES
==================================================

Use the supplied project data as the primary source.

NEVER invent factual information.

The AVAILABLE PLACES section contains only names
obtained from Geoapify. The names do not provide
descriptions, history, opening hours, prices,
activities, addresses, or other facts.

Therefore:

- Use a place name exactly as provided.
- Do not describe a place unless the project data
  explicitly provides that description.
- Do not invent opening hours.
- Do not invent ticket prices.
- Do not invent travel times or distances.
- Do not invent restaurants, hotels, activities,
  events, or transportation schedules.
- Do not claim an attraction is famous or popular.
- Do not treat every Geoapify result as a tourist
  attraction.

==================================================
PLACE QUALITY
==================================================

Review the available place names before creating
the itinerary.

Prefer names that clearly suggest:

- landmarks
- museums
- galleries
- monuments
- parks
- gardens
- viewpoints
- cultural attractions
- sightseeing locations

Avoid obvious noise such as:

- generic objects
- products
- equipment
- counters
- signs
- random objects
- vague names
- unrelated organizations
- ordinary businesses

If a place is questionable, leave it out.

Never invent a replacement attraction.

==================================================
ITINERARY
==================================================

Create exactly {days} days.

Use this format:

## Day 1

**Morning**
Activity or selected project-data place.

**Afternoon**
Activity or selected project-data place.

**Evening**
Activity or general suggestion.

Continue for all {days} days.

IMPORTANT:

Do not force a project-data place into the itinerary
just to fill space.

If there are not enough suitable places, use:

**General suggestion:** Explore the destination at
your own pace.

Do not repeatedly write "GENERAL TRAVEL SUGGESTION".

Make the wording natural and traveler-friendly.

For example:

GOOD:
**Morning:** Visit **The Empty Quarter Gallery**.

GOOD:
**Afternoon:** Take some free time to explore the
surrounding area.

BAD:
**Morning:** The Empty Quarter Gallery – a famous
Dubai art gallery with exhibitions.

The BAD example invents information.

==================================================
PROJECT DATA
==================================================

DESTINATION:
{context['destination']}


WEATHER
--------------------------------------------------

Temperature:
{context['weather']['temperature_c']} °C

Feels Like:
{context['weather']['feels_like_c']} °C

Humidity:
{context['weather']['humidity']} %

Condition:
{context['weather']['condition']}

Wind Speed:
{context['weather']['wind_speed']} m/s


CURRENCY
--------------------------------------------------

From:
{context['currency']['from']}

To:
{context['currency']['to']}

Project Exchange Rate:
{context['currency']['exchange_rate']}

Project Reference Conversion:

₹{context['currency']['amount_inr']} =
{context['currency']['converted_amount']}
{context['currency']['to']}


AVAILABLE PLACES
--------------------------------------------------

{places_text}


FLIGHT INFORMATION
--------------------------------------------------

Date:
{context['flight']['date']}

Status:
{context['flight']['status']}

Airline:
{context['flight']['airline']}

Flight Number:
{context['flight']['flight_number']}


ACCOMMODATION
--------------------------------------------------

Type:
{context['accommodation']['type']}

Reference Cost:
{context['accommodation']['cost']}


TRANSPORTATION
--------------------------------------------------

Type:
{context['transportation']['type']}

Reference Cost:
{context['transportation']['cost']}


==================================================
OUTPUT
==================================================

1. Short Destination Overview

Write a short, natural 2–3 sentence overview.

Do not introduce unsupported factual claims.

2. Day-by-Day Itinerary

Create exactly {days} days.

Use the Morning / Afternoon / Evening format above.

3. Weather Information

Show:

- Temperature
- Feels Like
- Humidity
- Condition
- Wind Speed

Use only the supplied weather data.

4. Currency Information

Show:

- From currency
- To currency
- Project exchange rate
- Project reference conversion

Call it a "Project Reference Rate".

5. Transportation Information

Show the transportation type and reference cost.

If flight details are available, show them.

If unavailable, write:

"Flight details are not available for this trip."

6. Accommodation Information

Show the accommodation type and reference cost.

Write:

"Reference cost — actual prices may vary."

7. Budget Considerations

Compare the user's budget with the supplied
reference costs.

Clearly explain that the supplied accommodation
and transportation values are reference data and
may not represent current prices.

8. Important Travel Tips

Give concise, practical general travel advice.

Do not present general advice as information
obtained from the project dataset.

==================================================
WRITING STYLE
==================================================

The final answer should sound like a helpful travel
planner, not a technical report.

Avoid repetitive phrases.

Do not repeatedly say:

"project data"
"GENERAL TRAVEL SUGGESTION"
"information not available"

unless genuinely necessary.

Keep the response concise, clear, and
beginner-friendly.

NEVER hallucinate.
"""

    return generate_response(prompt)
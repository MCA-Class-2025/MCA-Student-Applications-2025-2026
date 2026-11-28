# AI Travel Planner

## Project Overview

AI Travel Planner is an intelligent travel planning application developed as an MCA Major Project. It helps users plan trips by providing useful travel information, destination details, weather updates, flight information, currency conversion, and nearby places to visit.

The application uses Artificial Intelligence and multiple external APIs to make travel planning easier and more convenient.

## Objectives

- To simplify the travel planning process.
- To generate personalized travel itineraries using AI.
- To provide real-time weather information.
- To retrieve flight information.
- To provide currency exchange rates and conversion.
- To find nearby tourist attractions and places.
- To display relevant destination images.

## Key Features

- **AI-Based Itinerary Generation:** Generates travel plans based on user preferences and requirements.
- **Weather Information:** Provides weather details for selected destinations.
- **Flight Information:** Retrieves flight-related information.
- **Currency Conversion:** Provides exchange rates and converted currency values.
- **Nearby Places:** Finds tourist attractions and places using location-based services.
- **Destination Images:** Displays relevant images of travel destinations.
- **Interactive Interface:** Allows users to interact with the application and enter their travel requirements.

## Technologies Used

| Category | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Integration | Groq API |
| Weather API | OpenWeather API |
| Flight API | Aviationstack API |
| Currency API | Exchange Rate API |
| Location API | Geoapify API |
| Image API | Pexels API |
| Data Analysis | Pandas, NumPy |
| Data Visualization | Matplotlib, Seaborn |
| Version Control | GitHub |

## System Architecture

The project follows an API-integrated architecture:

1. The user enters travel requirements through the application.
2. The AI component processes the user's requirements.
3. External APIs retrieve relevant travel information.
4. The collected information is processed using Python.
5. The application combines the information and generates useful travel recommendations.
6. The results are displayed through the user interface.

## Project Structure

```text
MC2548_Isha_Pillai_AI-Travel-Planner/
│
├── data/
│   ├── Travel details dataset.csv
│   ├── final_fusion.csv
│   ├── flights.csv
│   ├── weather.csv
│   ├── exchange_rates.csv
│   ├── places.csv
│   ├── images.csv
│   └── eda_outputs/
│
├── Figures/
│   ├── E1_Temperature_Distribution.png
│   ├── E2_Place_Count_Distribution.png
│   ├── E3_Temperature_Humidity.png
│   ├── E4_API_Correlation_Heatmap.png
│   ├── EDA_1_Destination_Analysis.png
│   ├── EDA_2_Trip_Duration.png
│   └── EDA_3_Traveler_Age.png
│
├── services/
│   ├── travel_planner.py
│   └── exchange_service.py
│
├── frontend/
│   └── src/
│
├── app.py
├── main.py
├── requirements.txt
└── README.md
```

*Note: Update the structure if your actual GitHub folders or filenames differ.*

## Dataset Description

The project uses a travel dataset containing information such as:

- Destination
- Trip start and end dates
- Trip duration
- Traveler details
- Accommodation type and cost
- Transportation type and cost

The original dataset contained 139 records. After data cleaning, 137 records were retained.

Additional datasets were collected through external APIs, including flight details, weather information, currency exchange rates, nearby places, and destination images.

## Data Integration

Multiple datasets were combined to create a unified dataset.

The final fused dataset contains:

- 137 records
- 44 attributes
- Information collected from different sources and APIs

This integrated dataset helps in analyzing travel-related information in one place.

## Data Analysis and Visualization

Exploratory Data Analysis (EDA) was performed to understand the collected travel data.

The following visualizations were created:

1. **Temperature Distribution:** Shows the distribution of temperatures across destinations.
2. **Place Count Distribution:** Shows the distribution of the number of places found.
3. **Temperature vs Humidity:** Shows the relationship between temperature and humidity.
4. **API Correlation Heatmap:** Displays correlations between selected numerical attributes.
5. **Destination Analysis:** Helps understand destination-wise travel data.
6. **Traveler Age Analysis:** Shows the distribution of traveler ages.
7. **Trip Duration Analysis:** Shows the distribution of trip durations.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/MCA-Class-2025/MCA-Student-Applications-2025-2026.git
```

### 2. Open the Project Folder

Navigate to:

```text
MC2548_Isha_Pillai_AI-Travel-Planner
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure API Keys

Create a `.env` file in the project folder and add the required API keys:

```env
GROQ_API_KEY=your_groq_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key
PEXELS_API_KEY=your_pexels_api_key
```

Replace the placeholder values with your actual API keys. Never upload your `.env` file or expose API keys publicly.

## Running the Application

### Run the Streamlit Application

```bash
streamlit run app.py
```

### Run the FastAPI Backend

Open another terminal, activate the virtual environment, and execute:

```bash
uvicorn main:app --reload
```

The FastAPI documentation can be accessed at:

```text
http://127.0.0.1:8000/docs
```

## Future Scope

- Integration of more travel and booking APIs.
- Hotel and accommodation recommendations.
- Improved personalization based on user preferences.
- Map-based route planning.
- Travel budget estimation.
- Multi-language support.
- Mobile application development.

## Conclusion

The AI Travel Planner demonstrates how Artificial Intelligence, Python, and external APIs can be integrated to simplify travel planning. It combines travel-related information from multiple sources and presents useful details through an interactive application.

The project also demonstrates data collection, data cleaning, data integration, exploratory data analysis, and data visualization.

## Developed By

**Name:** Isha Pillai  
**Project:** AI Travel Planner  
**Course:** Master of Computer Applications (MCA)  
**Academic Year:** 2025–2026

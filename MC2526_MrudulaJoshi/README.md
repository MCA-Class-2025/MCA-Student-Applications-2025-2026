# FinSight AI — An Intelligent Corporate Travel Expense Analysis System

**MCA Project | Travel Intelligence Platform**

## Project Information

| Field | Details |
|---|---|
| Student | Mrudula Joshi |
| Programme | Master of Computer Applications (MCA) |
| University | SNDT Women's University |
| Project Title | FinSight AI — An Intelligent Corporate Travel Expense Analysis System |

> Add your official college roll number and academic year here before submitting, if required by your department.

## About the Project

FinSight AI is a corporate travel analytics application developed using Python and Streamlit. It brings travel-related information into one place and helps users explore corporate travel activity, expenses, employees, destinations, travel agencies and weather-related patterns.

The project includes data preparation and fusion workflows, data-quality checks, exploratory data analysis and an interactive dashboard. The dashboard is designed to make travel information easier to explore through summary views, filters and visual analytics.

## Dashboard Screenshot
## Dashboard Screenshots

The following screenshots show the different pages and interactive visualizations of the FinSight AI application.

### 1. Dashboard Overview
![Dashboard Overview](screenshots/Screenshot%202026-11-16%20225458.png)

### 2. Analytics Dashboard
![Analytics Dashboard](screenshots/Screenshot%202026-11-16%20225521.png)

### 3. Travel Analytics
![Travel Analytics](screenshots/Screenshot%202026-11-16%20225540.png)

### 4. Expense Analysis
![Expense Analysis](screenshots/Screenshot%202026-11-16%20225557.png)

### 5. Company Analysis
![Company Analysis](screenshots/Screenshot%202026-11-16%20225611.png)

### 6. Travel Trends
![Travel Trends](screenshots/Screenshot%202026-11-16%20225641.png)

### 7. Data Exploration
![Data Exploration](screenshots/Screenshot%202026-11-16%20225700.png)

### 8. API and Data Fusion
![API and Data Fusion](screenshots/Screenshot%202026-11-16%20225713.png)

### 9. Data Quality Analysis
![Data Quality Analysis](screenshots/Screenshot%202026-11-16%20225728.png)

### 10. Expense Visualizations
![Expense Visualizations](screenshots/Screenshot%202026-11-16%20225742.png)

### 11. Interactive Analytics
![Interactive Analytics](screenshots/Screenshot%202026-11-16%20225756.png)

### 12. Ask FinSight AI
![Ask FinSight AI](screenshots/Screenshot%202026-11-16%20225816.png)

## Main Application Sections

- **Overview** — summary view of corporate travel information.
- **Analytics Studio** — interactive analysis and visualizations for travel and expenses.
- **Explore Data** — explore the underlying travel datasets.
- **API & Fusion** — review API-related data and fused datasets.
- **Data Quality** — inspect data-quality and validation information.
- **Ask FinSight** — ask questions about employees, trips, spending, cities and weather.

## Dataset and Data Fusion

The project works with flight, hotel and employee data. The data preparation workflow combines related travel records with employee information and destination climate data to support analysis.

The packaged project includes original datasets, prepared API/climate data, fused flight and hotel datasets, and generated quality/EDA outputs. Refer to the accompanying project documentation for the detailed assignment workflow and API description.

## Technology Stack

| Area | Technology |
|---|---|
| Programming language | Python |
| Web application | Streamlit |
| Data processing | Pandas, NumPy |
| Data visualization | Plotly |
| API requests | Requests |
| API framework described in the assignment documentation | FastAPI |
| Climate data source | Open-Meteo |
| Data formats | CSV, JSON, Excel |

## Installation and Setup

Run the commands from the `FinSightAI/app` directory.

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the environment on Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## Project Structure

```text
FinSightAI/
├── app/
│   ├── app.py
│   └── requirements.txt
├── data/
│   ├── original/
│   ├── api/
│   └── fused/
├── notebooks/
├── report/
├── scripts/
├── docs/
└── screenshots/
    └── dashboard-home.png
```

## API and Implementation Note

The accompanying API/data-fusion assignment documentation describes the API workflow and endpoints. The Streamlit dashboard and the API/data-preparation scripts included in the submitted source should be treated as the implementation evidence. Do not assume that every endpoint described in the documentation is independently running unless its server module is included and started.

## Author

**Mrudula Joshi**  
**Programme:** MCA  
**University:** SNDT Women's University  
**Project:** FinSight AI — An Intelligent Corporate Travel Expense Analysis System

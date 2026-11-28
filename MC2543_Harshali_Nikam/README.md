# CityFusion — 5 API Data Fusion Project

## Objective

Demonstrate a complete Data Science pipeline using five APIs:

1. Open-Meteo Weather API
2. Open-Meteo Air Quality API
3. REST Countries API
4. World Bank Indicators API
5. ExchangeRate-API

The project demonstrates:

- Raw Data Fusion
- Data cleaning
- Missing-value handling
- Normalization
- Feature engineering
- Feature Fusion
- Descriptive statistics
- Correlation analysis
- Linear Regression
- Ridge Regression
- Support Vector Regression
- Model Fusion
- R², MSE and MAE
- GridSearchCV
- MongoDB data storage
- Streamlit visualization

## Project Architecture

5 APIs
→ Raw JSON
→ Raw Data Fusion
→ Pandas
→ Cleaning + Normalization
→ Feature Fusion
→ ML Models
→ Model Fusion
→ Prediction

## Setup in VS Code

### 1. Open the project folder

Open `CityFusion` in VS Code.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```cmd
venv\Scripts\activate
```

### 3. Install packages

```bash
pip install -r requirements.txt
```

### 4. Collect API data

```bash
python collect_data.py
```

This creates:

```text
data/raw/
data/processed/fused_dataset.csv
```

### 5. Run feature fusion

```bash
python fusion.py
```

### 6. Run model fusion

```bash
python model_fusion.py
```

### 7. Launch dashboard

```bash
streamlit run app.py
```

## MongoDB

MongoDB is optional for the demonstration.

If MongoDB is installed locally and running:

```bash
python mongo_store.py
```

The data is stored in:

```text
cityfusion
└── raw_fused_data
```

## Five API evidence

The raw JSON files saved in `data/raw/` are important for your submission. Show them to demonstrate that the system actually collected data from APIs.

## Fusion definitions for viva

### Raw Data Fusion
Integration of raw heterogeneous data from multiple sources before or during preprocessing.

### Feature Fusion
Combination of extracted/engineered features from multiple sources into a unified feature vector.

### Model Fusion
Combination of predictions from multiple trained models to obtain a final prediction.

## Suggested presentation

Show these four things tomorrow:

1. `data/raw/` — five API outputs
2. `fused_dataset.csv` — raw data fusion
3. `feature_fusion_matrix.csv` — feature fusion
4. Model metrics + fused prediction — model fusion

## Important

Internet access is required when running `collect_data.py`, because the five APIs are called live.

<img width="1917" height="872" alt="image" src="https://github.com/user-attachments/assets/a5fd6246-93f1-4f46-a602-a0a618ec4941" />


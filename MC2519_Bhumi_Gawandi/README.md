# AI Smart Expense Tracker

An AI-powered expense tracking and analytics application that helps users manage financial transactions, explore spending patterns, identify unusual transactions, and view predictive insights.

## Project Overview

The AI Smart Expense Tracker combines expense-management functionality with data analytics and machine-learning features. It supports transaction analysis, category-based insights, anomaly detection, forecasting, and a dashboard for visualizing financial data.

## Features

- **Expense Management:** Record and review expenses.
- **Analytics Dashboard:** View summaries and spending trends.
- **Data Fusion:** Analyze consolidated financial records from the data sources supported by the application.
- **Exploratory Data Analysis (EDA):** Explore distributions, categories and temporal patterns.
- **Expense Category Classification:** Compare Logistic Regression, Random Forest, Decision Tree, Naive Bayes and SVM models.
- **Anomaly Detection:** Identify transactions or patterns flagged as unusual by the ML pipeline.
- **Forecasting:** View forecasts produced by the forecasting components in the project.
- **AI Assistant:** Ask questions through the application's AI chat functionality, subject to the configured services.

> Features and integrations may depend on the current backend configuration and available data.

## Technology Stack

### Frontend
- React
- JavaScript
- CSS
- Lucide React icons

### Backend
- Python
- FastAPI

### Machine Learning and Data Analysis
- Pandas
- NumPy
- Scikit-learn
- Python pickle model files

### Data and Storage
- CSV datasets
- Application database and data sources configured in the backend

## Project Structure

```text
MC2519_Bhumi_Gawandi/
├── Sample Receipts/
├── backend/
├── eda/
│   └── results/
├── frontend/
├── ml/
├── Phase1_2 assignment.pdf
├── dataset_inspection.py
└── README.md
```

Folder contents may evolve as development continues.

## ML Classification

The initial classification experiment uses the personal-finance dataset and the following features:

- Amount
- Year
- Month
- Day
- DayOfWeek
- IsWeekend
- TypeEncoded

The target is `Category`.

Five models were evaluated using a train/test split of 80%/20% (1,200 training rows and 300 test rows from a 1,500-row dataset).

| Model | Accuracy |
|---|---:|
| Logistic Regression | 20.67% |
| Random Forest | 16.33% |
| Decision Tree | 15.67% |
| Naive Bayes | 21.33% |
| SVM | 18.67% |

These values represent the initial experiment and are not a guarantee of future performance. The experiment can be improved by incorporating transaction-description text features, tuning parameters and evaluating alternative feature strategies.

## Dataset

The classification experiment used:

`ml/dataset/personal_finance.csv`

The dataset includes transaction date, description, category, amount and transaction type. Preprocessing derives date-related features and encodes transaction type.

**Data notice:** Do not publish personal, financial, confidential or licensed data in this repository. Remove or anonymize such data before sharing.

## Setup and Run

The following is a general development setup. Adapt commands and environment variables to the actual files in your backend and frontend.

### 1. Clone the repository

```bash
git clone <repository-url>
cd MC2519_Bhumi_Gawandi
```

### 2. Start the backend

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a virtual environment (recommended):

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies, if a requirements file is present:

```bash
pip install -r requirements.txt
```

Start the FastAPI server using the entry point configured in the project. For example, if the application is exposed as `app.main`:

```bash
uvicorn app.main:app --reload
```

The API may then be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Start the frontend

Open a separate terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Use the local URL printed by the frontend development server to open the application.

## ML Training

If the classification training script is present in your project, run it from the repository root using the script's actual name and dependencies. For example:

```bash
python ml/train_classification_models.py
```

The initial experiment saved model artifacts and evaluation results under the project's ML model/results directories. Confirm these paths in the training script before running it.

## Documentation and Results

- See the project assignment document for the academic project requirements.
- Review `eda/results/` for generated EDA results, if available.
- Review the ML results directory for classification reports, confusion matrices and model comparisons, if generated.

## Limitations

- Initial classification accuracy is modest and should not be treated as financial advice.
- Model performance depends on the dataset, feature quality, class distribution and evaluation design.
- Anomaly flags are indicators of unusual patterns, not proof of fraud or incorrect transactions.
- Forecasts are estimates and can be affected by limited or changing historical data.
- AI-generated responses can be incorrect. Verify important financial information independently.

## Contributors

- Bhumi Gawandi

## License

Add the license applicable to this repository before distributing or reusing the code.

# Multilingual AI-Powered Fake News Detection System Using NLP

## 1. Project Overview

The Multilingual AI-Powered Fake News Detection System is a Machine Learning-based project that aims to identify and classify news articles as **Fake or Real** using Natural Language Processing (NLP) and Machine Learning techniques.

The system analyzes news text, extracts important features using TF-IDF, and uses a Logistic Regression classifier to predict the authenticity of news articles.

**Note:** The current implementation is an English-language prototype. Multilingual support is planned as a future enhancement.

## 2. Objectives

- Detect fake and real news articles automatically.
- Apply NLP techniques for text processing.
- Convert textual data into numerical features using TF-IDF.
- Train a Machine Learning model for classification.
- Evaluate model performance using accuracy.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Programming language |
| Pandas | Dataset handling |
| KaggleHub | Dataset downloading |
| Scikit-learn | Machine Learning |
| TF-IDF | Text feature extraction |
| Logistic Regression | News classification |
| VS Code | Development environment |

## 4. Datasets Used

This project uses multiple fake news datasets for data processing, analysis and model development.

The datasets are not included directly in this GitHub repository because of their large file sizes. Users can download them from the original sources using the links below.

### Dataset Sources

**1. Hindi Fake & Real News Dataset**

- Source: Kaggle
- Link: https://www.kaggle.com/datasets?search=hindi+fake+news

**2. Fake & Real News Dataset (English)**

- Source: Kaggle
- Link: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset

Contains two CSV files:
- `Fake.csv` – Contains fake news articles.
- `True.csv` – Contains real news articles.

**3. Marathi Fake & Real News Dataset**

- Source: Kaggle
- Link: https://www.kaggle.com/datasets?search=marathi+fake+news

**4. TALLIP Fake News Dataset**

- Source: GitHub
- Repository: https://github.com/Arko98/TALLIP-FakeNews-Dataset
- Dataset Download: http://www.iitp.ac.in/~ai-nlp-ml/resources/data/TALLIP-FakeNews-Dataset.zip

### Dataset Download Instructions

1. Open the respective dataset links.
2. Download the required datasets.
3. Extract the downloaded ZIP files.
4. Place the extracted datasets inside their corresponding folders in the `data/raw/` directory.
5. Ensure that the required dataset files are available before running the project.

**Note:** The Hindi and Marathi links open Kaggle search results. Select and download the corresponding datasets used in this project.

### Dataset Features

The English Fake & Real News Dataset contains:

- Title
- Text
- Subject
- Date

The project uses the `text` column for model training and prediction.

## 5. Methodology

The project follows these steps:

1. **Dataset Collection:** Download the Fake & Real News Dataset from Kaggle using KaggleHub.
2. **Data Loading:** Load `Fake.csv` and `True.csv` using Pandas.
3. **Label Encoding:** Assign 0 to fake news and 1 to real news.
4. **Dataset Combination:** Combine both datasets into a single dataset.
5. **Train-Test Split:** Divide the dataset into 80% training data and 20% testing data.
6. **Feature Extraction:** Apply TF-IDF to convert text into numerical features.
7. **Model Training:** Train the Logistic Regression classifier.
8. **Prediction:** Predict whether the news is fake or real.
9. **Evaluation:** Calculate model accuracy using Accuracy Score.

## 6. Machine Learning Model

**Algorithm:** Logistic Regression

**Feature Extraction:** TF-IDF (Term Frequency–Inverse Document Frequency)

TF-IDF assigns importance to words based on their frequency in a document and across the dataset.

Logistic Regression uses these numerical features to classify news into two categories:

- `0` – Fake News
- `1` – Real News

## 7. Model Performance

| Parameter | Result |
|---|---|
| Model | Logistic Regression |
| Feature Extraction | TF-IDF |
| Training Data | 80% |
| Testing Data | 20% |
| Accuracy | 98.61% |

The model achieved approximately **98.61% accuracy** on the test split in the current experiment.

## 8. Installation and Execution

### Step 1: Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### Step 2: Navigate to the Project Folder

```bash
cd your-project-folder
```

### Step 3: Install Required Libraries

```bash
pip install kagglehub pandas scikit-learn
```

### Step 4: Run the Python File

```bash
python fake_news_detection.py
```

### Step 5: Check the Output

The terminal displays the dataset download location and the model accuracy.

## 9. Future Enhancements

- Add multilingual datasets such as Hindi and Marathi news.
- Implement multilingual transformer models such as mBERT and XLM-RoBERTa.
- Support automatic language detection.
- Improve model performance using advanced NLP techniques.
- Develop a user-friendly web application for news verification.

## 10. Conclusion

This project demonstrates how Natural Language Processing and Machine Learning can be used to identify fake news.

TF-IDF and Logistic Regression provide an effective baseline for fake news classification. Future development will focus on extending the system to support multiple languages and improving its reliability across different datasets.

---

## Project Information

- **Project Topic:** Multilingual AI-Powered Fake News Detection System Using NLP
- **Programming Language:** Python
- **Development Tool:** Visual Studio Code
- **Project Type:** Machine Learning and Natural Language Processing
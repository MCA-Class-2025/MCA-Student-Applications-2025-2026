# StudyNova -- Intelligent Academic Learning Assistant

> **Learn Smarter • Search Faster • Understand Better**

StudyNova is an AI-powered academic learning assistant developed to help
students understand study material, practise concepts, and access
learning resources from one application. It began as an Academic Notes
AI chatbot and was extended with PDF question answering, image-based
study support, quiz generation, YouTube learning resources, saved notes,
Firebase authentication, activity dashboards, dataset preparation, and
machine-learning experiments.

The original project/repository name is **AcademicNotesAI**;
**StudyNova** is the application's current name.

------------------------------------------------------------------------

## Table of Contents

-   [Project Overview](#project-overview)
-   [Problem Statement](#problem-statement)
-   [Objectives](#objectives)
-   [Features](#features)
-   [Technology Stack](#technology-stack)
-   [Application Architecture](#application-architecture)
-   [Data Science and Machine
    Learning](#data-science-and-machine-learning)
-   [Project Structure](#project-structure)
-   [Installation and Setup](#installation-and-setup)
-   [Environment Variables and
    Secrets](#environment-variables-and-secrets)
-   [Run the Application](#run-the-application)
-   [How to Use](#how-to-use)
-   [Dataset and Privacy](#dataset-and-privacy)
-   [Limitations](#limitations)
-   [Deployment](#deployment)
-   [Future Enhancements](#future-enhancements)
-   [Developer](#developer)
-   [Acknowledgements](#acknowledgements)

------------------------------------------------------------------------

## Project Overview

Students often need to search through lengthy notes, textbooks, PDFs,
and online resources to find specific information. StudyNova brings
several learning tools together in a single Streamlit application.

The academic chatbot uses **Retrieval-Augmented Generation (RAG)** to
retrieve relevant content from academic documents and provide
context-based answers with source references. Other modules support
visual learning, quizzes, video discovery, saved notes, learning
activity tracking, and exploratory data analysis.

## Problem Statement

Finding a specific explanation in lengthy academic material can be
time-consuming. General-purpose AI answers may also fail to reflect the
content of a student's own notes.

StudyNova addresses this problem by allowing students to ask
natural-language questions about academic PDFs and uploaded documents.
It also provides complementary tools for revision and practice, while
recording application activity for dashboard and academic data-analysis
purposes.

## Objectives

-   Develop an AI-powered academic learning assistant.
-   Retrieve relevant information from academic documents using RAG.
-   Make it easier to ask questions about PDFs and study images.
-   Support revision through AI-generated quizzes and saved notes.
-   Provide educational video discovery through the YouTube Data API.
-   Track learning activity and display dashboard summaries.
-   Combine application activity records into a structured dataset.
-   Explore classification and regression techniques on the generated
    dataset.
-   Present model comparisons, diagnostics, and sample predictions in
    the application.

------------------------------------------------------------------------

## Features

### 1. Academic Notes Chatbot

-   Answers questions using the academic PDF knowledge base.
-   Retrieves relevant document chunks through semantic similarity
    search.
-   Uses Gemini to generate context-aware explanations.
-   Displays source-document references where available.
-   Supports chat history and answer regeneration.
-   Includes answer feedback, text-to-speech, and PDF conversation
    export.

### 2. Upload and Chat with Your Own PDF

Users can upload an academic PDF and ask questions about its contents.
The processing workflow extracts text, splits it into chunks, creates
embeddings, indexes them in FAISS, retrieves relevant passages, and
sends the retrieved context with the question to Gemini.

Typical uses include lecture notes, textbooks, assignments, and research
papers.

### 3. Image Study Assistant

Users can submit an academic image with an instruction. Supported
material may include textbook pages, handwritten notes, diagrams,
charts, tables, questions, and code screenshots. The image-study model
returns a text explanation based on the visible content.

### 4. Automatic Quiz Generator

-   Generates multiple-choice questions from a selected topic.
-   Supports Easy, Medium, and Hard difficulty.
-   Offers configurable question counts (5, 10, or 15).
-   Calculates scores and percentages.
-   Displays correct answers and explanations.
-   Records quiz activity for progress and dataset analysis.

### 5. YouTube Learning Resources

Uses the YouTube Data API to search for educational videos by topic.
Available result information can include the title, channel, publication
date, thumbnail, description, and video URL.

### 6. Saved Notes

-   Save useful AI-generated answers for revision.
-   Search and reopen saved notes.
-   View available source references and saved dates.
-   Remove notes when they are no longer needed.

### 7. Firebase Authentication

The application uses Firebase Authentication for account-related
operations such as signup, login, password reset, and logout. The
Firebase UID is used to associate activity records with an account.

### 8. Study Dashboard

Displays summaries of available learning activity, such as questions
asked, quiz attempts and performance, image-study activity, YouTube
searches, saved notes, and recent activity.

### 9. Dataset and Data Analysis

The Dataset page combines records from application JSON sources into a
Pandas DataFrame. It supports multi-user activity viewing, column
normalization, missing-value handling, and Excel export for further
analysis.

### 10. ML Insights

The ML Insights page presents classification and regression experiments,
evaluation metrics, visual diagnostics, and activity-type predictions
from saved models.

------------------------------------------------------------------------

## Technology Stack

  Area                    Technologies
  ----------------------- -----------------------------
  Programming language    Python
  User interface          Streamlit
  Generative AI           Google Gemini
  RAG framework           LangChain
  Embeddings              Sentence Transformers
  Vector search           FAISS
  Authentication          Firebase Authentication
  Video search            YouTube Data API
  Data handling           Pandas, NumPy
  Machine learning        Scikit-learn
  Visualization           Matplotlib, Seaborn, Plotly
  Model persistence       Joblib
  PDF processing/export   PyPDF, ReportLab
  Text-to-speech          gTTS
  Excel support           OpenPyXL
  Image handling          Pillow

------------------------------------------------------------------------

## Application Architecture

### RAG workflow

``` text
Academic PDF Notes
       |
       v
Document Loading and Text Extraction
       |
       v
Text Chunking
       |
       v
Sentence Transformer Embeddings
       |
       v
FAISS Vector Index
       |
       v
Student Question
       |
       v
Similarity Search and Context Retrieval
       |
       v
Prompt Construction
       |
       v
Google Gemini
       |
       v
Context-Based Answer and Source References
```

The uploaded-PDF workflow follows the same general retrieval process
using the document selected by the user.

### Supporting components

-   **LangChain:** helps connect document loading, splitting,
    embeddings, retrieval, and LLM calls.
-   **FAISS:** stores and searches vector embeddings to retrieve
    relevant document chunks.
-   **Google Gemini:** generates academic explanations and supports
    image understanding and quiz generation.
-   **Firebase:** provides authentication and account identity.
-   **YouTube Data API:** searches for external educational video
    resources.
-   **Streamlit:** provides the interactive application interface.

------------------------------------------------------------------------

## Data Science and Machine Learning

StudyNova includes a data-science and machine-learning extension based
on the activity records generated by the application. This is an
exploratory academic experiment, not a validated student-performance
prediction system.

### Activity data sources

The dataset manager reads and combines records from these JSON sources:

``` text
users.json
chat_history.json
favourites.json
quiz_history.json
image_study_history.json
youtube_history.json
activity_history.json
```

The fused dataset described in the current experiment contains **60
records and 40 attributes**. The exported workbook is:

``` text
ml_module/data/StudyNova_Fused_Dataset.xlsx
```

The exact dataset may change as more application activity is collected.

### Classification

The classification task predicts the activity category represented by
the `activity_type` target. Example categories include chat, quiz,
image, YouTube, saved-note, and user records.

The listed input features are:

``` text
activity_hour
question_length
answer_length
instruction_length
description_length
results_count
message_count
has_question
has_answer
has_source
has_instruction
```

Columns that directly encode the target category (for example, activity
flags, `record_type`, and `source_file`) are excluded from the
classifier to reduce target leakage.

Five algorithms are compared:

1.  Logistic Regression
2.  Gaussian Naive Bayes
3.  Decision Tree
4.  Random Forest
5.  Support Vector Machine (RBF kernel)

The experiment uses 4-fold stratified cross-validation. Reported metrics
include accuracy, weighted precision, weighted recall, and weighted
F1-score.

#### Recorded classification results

The following are the experimental results supplied for the current
60-record dataset:

  Model                   Accuracy   Precision   Recall   F1-score
  --------------------- ---------- ----------- -------- ----------
  Logistic Regression       0.9167      0.8938   0.9167     0.9033
  Naive Bayes               0.9167      0.8917   0.9167     0.9000
  Decision Tree             0.9167      0.8972   0.9167     0.8994
  Random Forest             0.8667      0.8750   0.8667     0.8688
  SVM                       0.9000      0.8542   0.9000     0.8733

Logistic Regression has the highest reported mean F1-score in this
experiment. Because the dataset is small and its classes are imbalanced,
these scores should be treated as exploratory results, not as evidence
of production-level performance.

### Classification diagnostics

The analysis produces confusion matrices, classification reports,
model-comparison visualizations, Random Forest feature-importance
output, overfitting comparisons, and out-of-fold predictions where
implemented.

Typical output files include:

``` text
ml_module/results/
├── classification_results.csv
├── classification_diagnostic_summary.csv
├── overfitting_analysis.csv
├── random_forest_feature_importance.csv
├── model_comparison.png
├── logistic_regression_confusion_matrix.png
├── naive_bayes_confusion_matrix.png
├── decision_tree_confusion_matrix.png
├── random_forest_confusion_matrix.png
└── svm_confusion_matrix.png
```

Feature importance is model-specific and does not establish causal
relationships.

### Regression

The regression component demonstrates continuous-value prediction using
`activity_hour` as its target. The supplied implementation includes:

-   Simple Linear Regression
-   Multiple Linear Regression
-   Polynomial Regression (degree 2)

The listed evaluation metrics are MAE, MSE, RMSE, and R². Results are
saved in:

``` text
ml_module/results/regression_results.csv
```

**Interpretation note:** `activity_hour` is an exploratory target for
demonstrating regression techniques. It should not be interpreted as a
meaningful measure of academic achievement. The current fused dataset
also contains only four records with non-zero quiz percentages, so
percentage-based regression is not considered meaningful for this
dataset.

### Prediction

The prediction module (`ml_module/prediction.py`) loads saved
classification models and predicts an activity category from prepared
input features. The models are stored in `ml_module/models/` using
Joblib.

### ML workflow

``` text
StudyNova Usage
      |
      v
JSON Activity Records
      |
      v
Data Fusion and Excel Export
      |
      v
Preprocessing and Feature Selection
      |
      v
Leakage Checks
      |
      +----------------------+
      |                      |
      v                      v
 Classification           Regression
      |                      |
      v                      v
 Cross-validation and Evaluation
      |
      v
 Diagnostics and Saved Models
      |
      v
 Streamlit ML Insights Page
      |
      v
 Model Comparison and Sample Prediction
```

------------------------------------------------------------------------

## Project Structure

The following is the logical structure described for the application.
Some generated, local-only, or optional files may not be present in
every copy.

``` text
AcademicNotesAI/
│
├── app.py
├── rag.py
├── ingest.py
├── image_processor.py
├── pdf_processor.py
├── pdf_export.py
├── speech.py
├── speech_to_text.py
├── youtube_service.py
├── quiz_generator.py
├── firebase_manager.py
├── progress_manager.py
├── chat_history_manager.py
├── favourites_manager.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── css/
│   └── style.css
├── data/
│   └── (Academic PDF notes)
├── data_science/
│   └── dataset_manager.py
│
├── ml_module/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── classification.py
│   ├── classification_analysis.py
│   ├── prediction.py
│   ├── regression.py
│   ├── data/
│   ├── models/
│   └── results/
│
├── pages/
│   ├── Chatbot.py
│   ├── Dashboard.py
│   ├── Dataset.py
│   ├── FavouriteNotes.py
│   ├── ImageStudy.py
│   ├── Login.py
│   ├── MLInsights.py
│   ├── Quiz.py
│   ├── Signup.py
│   └── YouTubeResources.py
│
├── storage/
│   └── (Local JSON activity files)
│
├── vectorstore/
│   └── (FAISS index files)
│
└── test files and other supporting modules
```

The virtual environment, secrets, private user records, and other
local-only files should remain outside the public submission.

------------------------------------------------------------------------

## Installation and Setup

### 1. Clone the project

If you have access to the standalone project repository:

``` bash
git clone https://github.com/pawarpayal09/AcademicNotesAI.git
cd AcademicNotesAI
```

If you received the source code as a folder, open that folder in VS Code
instead.

### 2. Create a virtual environment

**Windows PowerShell:**

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

``` bat
venv\Scripts\activate
```

**Linux/macOS:**

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

Use the project's `requirements.txt` as the dependency source. The
application uses packages for Streamlit, LangChain, Gemini integration,
FAISS, Sentence Transformers, Firebase, Pandas, NumPy, Scikit-learn,
visualization, PDF processing, and supporting features.

------------------------------------------------------------------------

## Environment Variables and Secrets

Create a local `.env` file in the project root and configure the
credentials required by your local setup. The following names reflect
the configuration variables described for this project; use the exact
names expected by your code.

``` env
MAIN_CHAT_API_KEY_1=YOUR_GEMINI_API_KEY_1
MAIN_CHAT_API_KEY_2=YOUR_GEMINI_API_KEY_2
IMAGE_STUDY_API_KEY=YOUR_IMAGE_STUDY_API_KEY
YOUTUBE_DATA_API_KEY=YOUR_YOUTUBE_DATA_API_KEY
FIREBASE_API_KEY=YOUR_FIREBASE_API_KEY
```

The Firebase Admin SDK may also require service-account credentials,
depending on the local Firebase configuration.

**Never commit real API keys, passwords, Firebase service-account JSON
files, private keys, or `.env` files to a public repository.** Keep a
placeholder file such as `.env.example` if you want to document required
variable names. For Streamlit Cloud, configure secrets in the app's
Secrets settings.

------------------------------------------------------------------------

## Run the Application

From the project root, with the virtual environment activated:

``` bash
streamlit run app.py
```

Streamlit will provide a local browser URL for the application.

------------------------------------------------------------------------

## How to Use

1.  Start StudyNova.
2.  Create an account or log in.
3.  Open the Academic Notes chatbot to ask questions about the available
    notes.
4.  Upload a PDF when you want to ask questions about your own document.
5.  Use Image Study to request explanations of academic images.
6.  Generate quizzes to practise a topic.
7.  Search YouTube for additional learning resources.
8.  Save useful answers for later revision.
9.  Review available learning summaries on the Dashboard.
10. Use Dataset to inspect and export the fused activity data.
11. Open ML Insights to compare the experimental models and try
    activity-type prediction.

------------------------------------------------------------------------

## Dataset and Privacy

The application records activity associated with the signed-in user's
Firebase UID. Depending on the feature, records may include questions,
answers, quiz results, image-study instructions, YouTube searches,
saved-note activity, timestamps, and account-related fields.

The project uses local JSON storage for the activity sources described
above. Treat these files as potentially sensitive. Before publishing a
dataset or sample records, remove or anonymize email addresses, Firebase
UIDs, names, questions, and any other personal or confidential
information.

Do not publish real user records, private academic documents, API
credentials, or Firebase service-account files in a public repository.

------------------------------------------------------------------------

## Limitations

-   The current ML experiment is based on a small dataset of 60 records.
-   Activity classes are unevenly distributed, and some classes have
    very few examples.
-   Cross-validation results may vary when the dataset changes.
-   Classification metrics are exploratory and are not
    production-performance guarantees.
-   Regression on `activity_hour` is a demonstration of regression
    methods, not an academic-performance prediction.
-   The current dataset has too few non-zero quiz-percentage records for
    meaningful percentage regression.
-   More representative, balanced, anonymized activity data is needed
    for stronger evaluation.
-   AI-generated explanations may contain errors; students should verify
    important academic information against trusted course material.

------------------------------------------------------------------------

## Deployment

The application can be deployed on Streamlit Community Cloud, subject to
the platform's current resource and dependency limits.

1.  Push the application source code to a GitHub repository.
2.  Connect the repository to Streamlit Community Cloud.
3.  Select `app.py` as the application entry point.
4.  Add the required secrets in the Streamlit app settings.
5.  Confirm that `requirements.txt` lists the required dependencies.
6.  Ensure required public assets and model files are available.
7.  Deploy and test the main application modules.

Do not commit `.env`, service-account credentials, private keys, virtual
environments, or private user data. Check the size of model and
vector-index files before committing them.

------------------------------------------------------------------------

## Future Enhancements

-   Improved voice interaction and speech support.
-   Multi-language learning support.
-   More advanced quiz and practice modes.
-   Better note categories, tags, and search.
-   Expanded cloud storage and data management.
-   Larger and more balanced activity datasets.
-   More robust machine-learning evaluation.
-   Explainable ML predictions.
-   Personalized study recommendations and learning paths.
-   Mobile-friendly application experience.

------------------------------------------------------------------------

## Developer

**Payal Pramod Pawar**\
Master of Computer Applications (MCA)\
**Project:** StudyNova -- Intelligent Academic Learning Assistant\
**Original project name:** AcademicNotesAI

Developed as an academic project combining generative AI, RAG, document
processing, data analysis, and exploratory machine learning.

------------------------------------------------------------------------

## Acknowledgements

StudyNova uses and integrates open-source libraries and external
services, including Google Gemini, LangChain, Hugging Face Sentence
Transformers, FAISS, Firebase, YouTube Data API, Streamlit, Pandas,
NumPy, Scikit-learn, Matplotlib, Seaborn, Plotly, Joblib, OpenPyXL,
Pillow, PyPDF, ReportLab, and gTTS.

------------------------------------------------------------------------

## License

This project was developed for educational and academic purposes. Please
provide appropriate credit to the original developer if reusing or
extending the project. Check the licenses and terms of the third-party
libraries and services before redistributing them.

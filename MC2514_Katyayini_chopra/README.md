#  FixAI Maharashtra
### AI-Powered Household and Building Defect Detection & Diagnosis System

##  Project Overview

FixAI Maharashtra is an AI-powered application designed to help users identify and understand common household and building defects through image-based analysis.

Users can upload an image of a building or household defect and provide a description. The application analyses the image, combines relevant information from multiple sources, and generates a diagnosis with possible causes and recommendations.

The project also integrates five Machine Learning algorithms to classify defect categories and compare their predictions.

##  Objectives

- Identify common household and building defects using uploaded images.
- Generate AI-based defect analysis and diagnosis.
- Combine information from different data sources for better analysis.
- Use Machine Learning algorithms to classify defect categories.
- Provide users with useful recommendations and relevant professional-service information.
- Present the analysis through an interactive web application.

##  Key Features

### 1. Image-Based Defect Analysis
- Upload an image of a building or household defect.
- Provide an optional description of the problem.
- Use Gemini AI to analyse the uploaded image and extract relevant information.

### 2. Data Fusion
The application combines information from multiple sources, including:

- Image analysis results
- Building defect knowledge dataset
- Location-related information
- Weather information
- Air quality information
- Relevant professional and service information

### 3. AI-Based Diagnosis
- Uses the collected and fused information to generate a final diagnosis.
- Retrieves relevant information using a Retrieval-Augmented Generation (RAG) approach.
- Provides possible explanations and recommendations.

### 4. Five-Algorithm Machine Learning Module

The project integrates the following five Machine Learning algorithms:

1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Support Vector Machine (SVM)
5. K-Nearest Neighbors (KNN)

The algorithms classify defect categories using extracted textual features. Their predictions are compared to determine a consensus result.

### 5. Machine Learning Dashboard

The dashboard provides:

- Latest uploaded-image predictions from all five algorithms.
- Consensus prediction and model voting.
- Performance comparison of algorithms.
- Accuracy, Precision, Recall and F1-score.
- Confusion matrices.
- Dataset class distribution.
- Classification reports.

**Note:** The current dataset is small, so the model evaluation results are experimental and require further validation.

##  Project Workflow

1. User uploads a building or household defect image.
2. Gemini AI analyses the image and extracts relevant details.
3. The extracted information is passed to the data fusion module.
4. The fusion module combines relevant knowledge, location and environmental information.
5. Five Machine Learning algorithms generate defect-category predictions.
6. A consensus is calculated from the five model predictions.
7. The final reasoning module generates the diagnosis using relevant retrieved information and AI reasoning.
8. The results are displayed through the Streamlit application.

##  Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application interface |
| Gemini AI | Image analysis and AI-based reasoning |
| Scikit-learn | Machine Learning algorithms |
| Pandas | Dataset handling |
| NumPy | Numerical operations |
| Matplotlib | Data visualization |
| FAISS | Vector similarity search |
| RAG | Retrieval-Augmented Generation |
| APIs | External data integration |

## 📂 Project Structure

```text
FixAI_Maharashtra/
│
├── app.py
│
├── pages/
│   └── 2_5_Algorithm_ML_Dashboard.py
│
├── services/
│   ├── gemini_service.py
│   ├── fusion_service.py
│   ├── final_reasoning_service.py
│   ├── fused_rag_service.py
│   ├── chat_service.py
│   └── ml_model_service.py
│
├── api/
│   ├── main.py
│   ├── professionals.csv
│   └── service_data.csv
│
├── data/
│   ├── building_defect_knowledge.csv
│   └── fixai_fused_dataset.csv
│
├── analysis/
│
├── output/
│
├── requirements.txt
│
└── README.md
```

*Note: The structure above shows the main project components. Some additional files and folders may be present in the actual project.*

## ⚙️ Installation and Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
```

### Step 2: Navigate to the Project Folder

```bash
cd FixAI_Maharashtra
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory and add the required API credentials.

Example:

```env
GEMINI_API_KEY=your_api_key_here
```

Add other API credentials required by the project configuration.

**Important:** Never upload the `.env` file or expose API keys on GitHub.

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

## Dataset Information

The project uses building defect-related datasets for knowledge retrieval, data fusion and Machine Learning.

The datasets contain information related to:

- Work type
- Building location
- Building elements
- Defect categories
- Example defect descriptions
- Additional fused information

The current dataset is a small experimental dataset. More labelled records are required to improve the reliability and generalisation of the Machine Learning models.

##  Limitations

- The current labelled dataset is limited in size.
- Machine Learning predictions are experimental.
- Model predictions depend on the quality of image analysis and extracted textual features.
- External API availability and internet connectivity can affect certain features.
- The application provides preliminary guidance and does not replace professional building inspection.

##  Future Scope

- Expand the dataset with more real-world building defect images and labelled records.
- Improve the accuracy and reliability of defect classification.
- Explore direct image-based deep learning models.
- Add more defect categories.
- Improve location-based professional recommendations.
- Develop a mobile-friendly application.
- Introduce user feedback and diagnosis history.

##  Project Information

**Project Name:** FixAI Maharashtra

**Project Type:** AI and Machine Learning Based Application

**Domain:** Artificial Intelligence, Machine Learning, Data Fusion and Building Defect Diagnosis

**Developed Using:** Python and Streamlit

---

*FixAI Maharashtra aims to make preliminary building defect identification and understanding more accessible through Artificial Intelligence and Machine Learning.*

# 🎨 ArtSense AI
### AI-Powered Artwork Discovery and Recommendation System

**Developed by:** Shravani Shirke  
**Roll Number:** MC2557  
**Course:** Master of Computer Applications (MCA)  
**University:** SNDT Women's University

---

## 📌 1. Project Overview

ArtSense AI is an AI-powered artwork discovery application that combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), museum APIs, and data analysis techniques.

The application allows users to explore artwork information through natural-language questions. It uses an enhanced artwork dataset created by combining an original dataset with additional information collected from five international museum APIs.

The fused dataset is processed using a RAG pipeline, where artwork records are converted into documents, transformed into embeddings, and stored in a FAISS vector database. Gemini LLM uses the retrieved information to generate contextual responses to user queries.

## 🎯 2. Project Objectives

- Collect additional artwork information from multiple museum APIs.
- Combine the original artwork dataset with API-collected data.
- Perform data cleaning and data-quality assessment.
- Conduct Exploratory Data Analysis (EDA).
- Build a semantic search and retrieval system using FAISS.
- Integrate Gemini LLM with a Retrieval-Augmented Generation pipeline.
- Develop an interactive Streamlit application for artwork discovery.
- Provide informative responses based on retrieved artwork records.

## ✨ 3. Key Features

- **Artwork Discovery:** Search artwork information using natural-language questions.
- **Museum API Integration:** Collect artwork metadata from five museum sources.
- **Data Fusion:** Combine original artwork records with external API records.
- **Exploratory Data Analysis:** Analyze artwork sources, mediums, movements, periods, and prices.
- **Semantic Search:** Retrieve relevant artwork records using vector embeddings.
- **LLM Integration:** Generate contextual answers using Gemini.
- **Interactive Interface:** Use the Streamlit application to interact with the system.
- **Source-Based Retrieval:** Retrieve artwork information with available museum source metadata.

## 🏛️ 4. Data Sources

The project uses an original artwork dataset and additional information collected from the following museum APIs:

| Museum | Purpose |
|---|---|
| The Metropolitan Museum of Art | Artwork and collection information |
| Smithsonian Institution | Artwork and collection metadata |
| Art Institute of Chicago | Artwork records and descriptions |
| Cleveland Museum of Art | Museum artwork information |
| Victoria and Albert Museum | Artwork and collection information |

## 📊 5. Dataset Information

The original dataset contains 754 artwork records and 8 attributes.

After API integration, the final fused dataset contains 957 records and 17 attributes.

| Parameter | Original Dataset | Final Fused Dataset |
|---|---:|---:|
| Records | 754 | 957 |
| Attributes | 8 | 17 |
| Additional API records | - | 203 |

### Original Dataset Attributes

- Price
- Artist
- Title
- Year of Creation
- Signed
- Condition
- Period
- Movement

### Additional API-Derived Attributes

- Date
- Medium
- Department
- Classification
- Culture
- Description
- Image URL
- Object ID
- Source
- Record Source

**Note:** The original and API datasets were combined using concatenation because no matching keys were found between the two datasets. Therefore, the final dataset is an expanded collection rather than a record-level matching of identical artworks.

## 🛠️ 6. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | Interactive application interface |
| Pandas | Dataset processing and manipulation |
| LangChain | RAG pipeline components |
| Sentence Transformers | Text embedding generation |
| all-MiniLM-L6-v2 | Embedding model |
| FAISS | Vector database and similarity search |
| Gemini LLM | Natural-language response generation |
| Matplotlib | Data visualization |
| Seaborn | Statistical visualization |
| Excel / CSV | Dataset storage and analysis |
| VS Code | Development environment |

## 🧠 7. System Architecture

The ArtSense AI application follows this workflow:

```text
Original Artwork Dataset
          +
     Museum APIs
          |
          v
    API Data Collection
          |
          v
    Data Preparation
          |
          v
      Data Fusion
          |
          v
     Final Fused CSV
          |
          v
 Exploratory Data Analysis
          |
          v
  Artwork Document Creation
          |
          v
  Sentence Transformer Model
          |
          v
    Embedding Generation
          |
          v
      FAISS Vector DB
          |
          v
       Retriever
          |
          v
      Gemini LLM
          |
          v
   Generated Response
          |
          v
    Streamlit Interface
```

## 🔍 8. RAG Implementation

The project uses Retrieval-Augmented Generation to provide responses based on artwork information stored in the knowledge base.

The workflow consists of:

1. Loading the final fused CSV dataset.
2. Preparing and cleaning artwork records.
3. Converting records into text documents.
4. Generating embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
5. Storing embeddings in a FAISS vector database.
6. Retrieving relevant documents based on user queries.
7. Passing retrieved context to Gemini LLM.
8. Displaying the generated response through Streamlit.

The RAG approach allows the application to use the additional museum metadata without retraining the underlying Gemini model.

## 📈 9. Exploratory Data Analysis

EDA was performed on the final fused dataset to identify patterns, distributions, and data-quality issues.

The following analyses were performed:

- Source Distribution
- Original vs API Data Comparison
- Art Movement Distribution
- Art Period Distribution
- Top Artists Analysis
- Medium Distribution
- Price Distribution
- Price Boxplot and Outlier Analysis
- Source vs Medium Analysis
- Source vs Period Analysis
- Correlation Heatmap
- API Data Completeness Analysis

EDA outputs are stored in the `fused_data/eda_outputs/` directory.

## 📁 10. Project Structure

```text
artsense-ai/
│
├── README.md
├── requirements.txt
├── app.py
├── rag_pipeline.py
│
├── data/
│   └── artworks.csv.csv
│
├── api_data/
│   ├── met_artworks.csv
│   ├── smithsonian_artworks.csv
│   ├── chicago_artworks.csv
│   ├── cleveland_artworks.csv
│   └── va_artworks.csv
│
├── apis/
│   └── API helper modules
│
├── fetch_met_data.py
├── fetch_smithsonian_data.py
├── fetch_chicago_data.py
├── fetch_cleveland_data.py
├── fetch_va_data.py
│
├── api_fusion.py
├── final_fusion.py
├── eda.py
│
└── fused_data/
    ├── final_fused_dataset.csv
    ├── final_fused_dataset.xlsx
    └── eda_outputs/
        ├── 01_source_distribution.png
        ├── 03_art_movement_distribution.png
        ├── 04_art_period_distribution.png
        ├── 06_medium_distribution.png
        ├── 07_price_distribution.png
        ├── 08_price_boxplot.png
        ├── 12_correlation_heatmap.png
        ├── 13_api_completeness.png
        └── eda_summary.csv
```

*Note: This is a documentation structure based on the project workflow. Adjust filenames and folders to match the actual files uploaded to GitHub.*

## ⚙️ 11. Installation and Setup

### Prerequisites

- Python 3.x
- Visual Studio Code
- Git
- Internet connection
- Gemini API key

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate into the project directory:

```bash
cd artsense-ai
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure Gemini API Key

Configure your Gemini API key using the environment variable or configuration method expected by the application.

Never upload your actual API key or `.env` file to GitHub.

### Step 5: Run the Streamlit Application

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## 💬 12. Example Queries

Users can interact with ArtSense AI by asking questions such as:

- Find artworks from the Met Museum.
- What mediums are used in the collected artworks?
- Find Baroque artworks.
- Find artworks created in 2021.
- What is the artist and price of Bayreuth Opera?
- What museum department information is available?
- Describe an artwork using its available museum description.

The response depends on the information available in the dataset and the records retrieved by the RAG pipeline.

## 📋 13. Testing and Results

The RAG application was tested using two categories of questions:

**Set 1 – Original Dataset Questions**
- Artist and artwork information
- Artwork price
- Year of creation
- Signature and condition
- Art periods and movements

**Set 2 – API/Fused Dataset Questions**
- Museum source
- Artwork medium
- Museum department
- Artwork classification
- Artwork description

The pipeline successfully created 957 artwork documents from the fused dataset.

A test query, "Find artworks from the Met Museum", returned five artwork examples associated with the Met Museum.

The testing also identified limitations in metadata completeness and retrieval of certain classification and descriptive fields.

## ⚠️ 14. Limitations

- Some museum API records contain missing metadata.
- Different museums use different data formats and object identifiers.
- Original and API records were not matched through common keys.
- Some questions may return incomplete information.
- Retrieval accuracy depends on document quality and available metadata.
- Further evaluation is required to establish improvements in answer accuracy.

## 🚀 15. Future Enhancements

- Improve artwork metadata cleaning and standardization.
- Implement more advanced artwork matching techniques.
- Improve semantic retrieval accuracy.
- Add advanced search filters.
- Improve artwork image display.
- Integrate additional museum APIs.
- Expand the testing dataset and evaluation metrics.
- Enhance the user interface and user experience.

## 🎓 16. Conclusion

ArtSense AI demonstrates the integration of museum APIs, data fusion, exploratory data analysis, vector databases, Retrieval-Augmented Generation, and Large Language Models in an artwork discovery application.

By combining the original artwork dataset with additional museum metadata, the project creates an expanded knowledge base that supports more informative artwork searches.

The application demonstrates how external data can enrich an existing LLM/RAG system and provide a foundation for AI-powered artwork exploration.

---

## 📚 17. API References

1. The Metropolitan Museum of Art – https://metmuseum.github.io/
2. Smithsonian Open Access – https://www.si.edu/openaccess
3. Art Institute of Chicago – https://api.artic.edu/docs/
4. Cleveland Museum of Art – https://openaccess-api.clevelandart.org/
5. Victoria and Albert Museum – https://developers.vam.ac.uk/

---

**Project:** ArtSense AI  
**Developed by:** Shravani Shirke  
**Roll Number:** MC2557  
**Program:** MCA  
**University:** SNDT Women's University

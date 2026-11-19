# Career Guidance Chatbot

### AI-Powered Career Guidance Using Retrieval-Augmented Generation (RAG)

A career guidance chatbot built using **Python, Streamlit, Retrieval-Augmented Generation (RAG), FAISS, Sentence Transformers, and Ollama**.

The application is designed to help users explore career-related information by asking questions in natural language. It uses career-related datasets as its knowledge source, retrieves relevant information through semantic search, and generates responses using the **Phi-3 Mini** language model running locally through Ollama.

This project demonstrates how data processing, semantic search, vector databases, and Large Language Models (LLMs) can be combined to build a domain-focused conversational application.

>

---

## Project Overview

Career planning can be challenging for students and job seekers. Information about career paths, job roles, required skills, and educational opportunities may be spread across different sources. Finding relevant information manually can take time, particularly when users are unsure what to search for.

The **Career Guidance Chatbot** aims to make career-related information easier to explore through a conversational interface. Instead of requiring users to search through datasets manually, the application allows them to ask questions and receive responses generated using information retrieved from the project's career-related knowledge base.

The system follows a **Retrieval-Augmented Generation (RAG)** approach. It first retrieves relevant text from the knowledge base and then provides that context to a language model to generate a response.

The project uses:

- Career-related datasets as the information source.
- Sentence Transformers to convert text into vector embeddings.
- FAISS for vector similarity search.
- Ollama to run a language model locally.
- Phi-3 Mini for natural-language response generation.
- Streamlit for the chatbot interface.

## Problem Statement

Students and job seekers may face difficulties when exploring career options because:

- Career-related information is distributed across multiple datasets and sources.
- It can be difficult to identify the skills associated with a particular career or job role.
- Users may not know which career-related information is relevant to their questions.
- Manually searching through large amounts of information can be time-consuming.
- General-purpose language models may not have access to the specific information contained in a project's datasets.

This project addresses these challenges by creating a conversational system that retrieves relevant information from a prepared career knowledge base and uses it to support natural-language question answering.

## Key Features

| Feature                        | Description                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------- |
| Conversational chatbot         | Allows users to ask career-related questions using natural language          |
| Retrieval-Augmented Generation | Retrieves relevant information before generating a response                  |
| Semantic search                | Uses text embeddings to find information based on meaning                    |
| FAISS vector search            | Searches the indexed career-related text chunks                              |
| Local LLM integration          | Uses Ollama to run the Phi-3 Mini language model locally                     |
| Sentence embeddings            | Uses `all-MiniLM-L6-v2` to convert text into vector representations          |
| Career knowledge base          | Uses prepared career-related datasets as the source of retrieved information |
| Streamlit interface            | Provides a web-based interface for interacting with the chatbot              |

_The exact pages and additional features should be described according to the current implementation in `app.py`._

---

## Technology Stack

| Category              | Technology            | Purpose                                   |
| --------------------- | --------------------- | ----------------------------------------- |
| Programming language  | Python                | Main application development              |
| Application framework | Streamlit             | Chatbot web interface                     |
| LLM runtime           | Ollama                | Runs the language model locally           |
| Language model        | Phi-3 Mini (`phi3`)   | Generates natural-language responses      |
| Embedding model       | `all-MiniLM-L6-v2`    | Converts text into embeddings             |
| Embedding framework   | Sentence Transformers | Generates semantic vector representations |
| Vector search         | FAISS                 | Retrieves relevant text chunks            |
| Data processing       | Pandas                | Loads and processes tabular data          |
| Numerical processing  | NumPy                 | Supports numerical operations             |

## Models and Components

### Sentence Transformer — `all-MiniLM-L6-v2`

**Purpose:** Text embedding generation.

The project uses the `all-MiniLM-L6-v2` Sentence Transformer model to convert text into numerical vector representations called embeddings.

These embeddings are used to compare the meaning of a user's question with the text chunks stored in the knowledge base.

Model reference: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

### FAISS

**Purpose:** Vector indexing and similarity search.

FAISS is used to index and search vector embeddings. When a user asks a question, the question is converted into an embedding and compared with the vectors stored in the index. The search returns text chunks that are relevant to the question.

### Ollama — Phi-3 Mini

**Purpose:** Natural-language response generation.

The project uses Ollama to run the Phi-3 Mini language model locally. The retrieved text and the user's question are supplied to the model so that it can generate a response.

Model reference: https://ollama.com/library/phi3

### Role of Each Component

| Component          | Main responsibility                           |
| ------------------ | --------------------------------------------- |
| `all-MiniLM-L6-v2` | Converts text and questions into embeddings   |
| FAISS              | Finds relevant chunks using vector similarity |
| Ollama             | Provides the local model runtime              |
| Phi-3 Mini         | Generates a natural-language response         |
| Streamlit          | Displays the chatbot interface                |

---

## System Workflow

The application follows a retrieval and response-generation workflow.

```text
             CAREER-RELATED DATASETS
                         |
                         v
                  DATA LOADING
                         |
                         v
                 DATA PREPROCESSING
                         |
                         v
                    TEXT CHUNKING
                         |
                         v
              SENTENCE TRANSFORMER
                 all-MiniLM-L6-v2
                         |
                         v
                VECTOR EMBEDDINGS
                         |
                         v
                    FAISS INDEX
                         |
                         |
USER QUESTION             |
      |                   |
      v                   |
STREAMLIT INTERFACE       |
      |                   |
      v                   |
QUESTION EMBEDDING        |
      |                   |
      v                   |
FAISS SIMILARITY SEARCH <--
      |
      v
RELEVANT TEXT CHUNKS
      |
      v
QUESTION + RETRIEVED CONTEXT
      |
      v
       OLLAMA
          |
          v
     PHI-3 MINI
          |
          v
   GENERATED RESPONSE
          |
          v
   STREAMLIT INTERFACE
          |
          v
         USER
```

## RAG Workflow

**Retrieval-Augmented Generation (RAG)** combines information retrieval with language generation. In this project, retrieval is performed before the language model generates an answer.

### 1. Data Loading

The career-related datasets are loaded by the project so that their information can be prepared for the knowledge base.

### 2. Data Preprocessing

The source information is prepared for use in the retrieval pipeline. The exact cleaning and transformation steps depend on the dataset and the implementation.

### 3. Text Chunking

The prepared text is divided into smaller sections called chunks. Chunking makes it possible to retrieve relevant portions of information rather than supplying an entire dataset to the language model.

### 4. Embedding Generation

The `all-MiniLM-L6-v2` model converts each text chunk into a numerical vector representation.

For example:

```text
Text:
"Python is used in data science and machine learning."

                 |
                 v

        all-MiniLM-L6-v2

                 |
                 v

       Numerical embedding
          [0.12, -0.08, ...]
```

The values above are illustrative only.

### 5. FAISS Indexing

The generated embeddings are stored in a FAISS index. This makes it possible to search for semantically relevant text chunks.

### 6. User Query Processing

When a user enters a question, the same embedding model converts the question into a vector.

### 7. Similarity Search

FAISS compares the question embedding with the stored vectors and retrieves relevant text chunks.

### 8. Context-Based Answer Generation

The retrieved context and the original question are passed to the Phi-3 Mini model through Ollama.

### 9. Response Display

The generated answer is returned to the Streamlit interface and displayed to the user.

---

## Project Structure

The following structure is based on the visible portion of the project's VS Code Explorer screenshot. The screenshot is cropped, so additional files may exist below the visible area.

```text
Career-Guidance-Chatbot/
│
├── __pycache__/
├── .git/
├── .streamlit/
│   ├── jobs_api.py
│   └── secrets.toml
│
├── api/
├── dataset/
├── eda_output/
├── faiss_index/
├── machine_learning_results/
├── processed_data/
├── vectorstore/
├── venv/
│
├── .gitignore
├── app.py
├── books_api.py
├── career_recommender.py
├── data_loader.py
├── eda_fused_dataset.py
├── fusion.py
├── github_api.py
├── jobs_api.py
├── machine_learning.py
├── prepare_career_dataset.py
├── preprocess.py
├── rag.py
├── research_api.py
└── resume_analyzer.py
```

### Folder Descriptions

| Folder                      | Purpose                                           |
| --------------------------- | ------------------------------------------------- |
| `.streamlit/`               | Streamlit configuration and related files         |
| `api/`                      | API-related project files                         |
| `dataset/`                  | Original/source datasets                          |
| `eda_output/`               | Exploratory data analysis outputs                 |
| `faiss_index/`              | FAISS index files, if saved by the application    |
| `machine_learning_results/` | Machine-learning output files                     |
| `processed_data/`           | Processed datasets                                |
| `vectorstore/`              | Vector-store files used by the retrieval workflow |
| `venv/`                     | Local Python virtual environment                  |
| `.git/`                     | Git repository metadata                           |
| `__pycache__/`              | Python bytecode cache                             |

### Main Python Files

The descriptions below are based on the filenames visible in the screenshot. Confirm the precise functionality from each file's implementation.

| File                        | Responsibility indicated by the filename  |
| --------------------------- | ----------------------------------------- |
| `app.py`                    | Main Streamlit application                |
| `books_api.py`              | Book-related API integration              |
| `career_recommender.py`     | Career recommendation functionality       |
| `data_loader.py`            | Loading project datasets                  |
| `eda_fused_dataset.py`      | Exploratory analysis of the fused dataset |
| `fusion.py`                 | Dataset fusion                            |
| `github_api.py`             | GitHub API integration                    |
| `jobs_api.py`               | Job-related API integration               |
| `machine_learning.py`       | Machine-learning workflow                 |
| `prepare_career_dataset.py` | Career dataset preparation                |
| `preprocess.py`             | Data preprocessing                        |
| `rag.py`                    | Retrieval-Augmented Generation workflow   |
| `research_api.py`           | Research-related API integration          |
| `resume_analyzer.py`        | Resume analysis functionality             |

---

## Installation and Local Setup

### Prerequisites

- Python 3.10 or a compatible version supported by the project's dependencies.
- Git (if cloning the repository).
- Visual Studio Code or another Python IDE (recommended).
- Ollama installed locally.
- Sufficient system resources to run the selected local language model.
- Internet access for installing dependencies and downloading models.

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Career-Guidance-Chatbot
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the actual repository URL.

If the project is already available on your computer, open its folder in VS Code.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

If `requirements.txt` is available:

```bash
pip install -r requirements.txt
```

If it is not available, create it based on the imports in the project. Common packages for this RAG implementation include:

```text
streamlit
pandas
numpy
sentence-transformers
faiss-cpu
ollama
```

The final dependency list must include every package actually imported by the application and its modules. Use compatible versions from the working environment.

### 5. Install Ollama

Download and install Ollama:

https://ollama.com/

### 6. Download the Phi-3 Mini Model

Open a terminal and run:

```bash
ollama pull phi3
```

Verify that the model is installed:

```bash
ollama list
```

The model list should contain `phi3`.

### 7. Check the Required Project Files

Before running the application, confirm that:

- `app.py` is present in the project root.
- Required datasets are available in the expected locations.
- Required processed data files are available or can be generated.
- FAISS/vector-store files are available, or the project has a process to create them.
- Ollama is installed and the `phi3` model is available.
- All Python dependencies are installed.

---

## Run the Application

Open the terminal in the project root directory, activate the virtual environment, and execute:

```bash
streamlit run app.py
```

Streamlit will display a local URL, normally:

```text
http://localhost:8501
```

Open this URL in your browser to use the Career Guidance Chatbot.

To stop the application, press `Ctrl + C` in the terminal.

---

## Example Questions

The following are example questions for testing, provided the project's knowledge base contains relevant information:

```text
1. What career options are available in the IT field?

2. What skills are required for a data analyst?

3. What is the difference between a data analyst
   and a data scientist?

4. What technologies are commonly used in software development?

5. What skills are useful for a machine learning career?
```

The chatbot's answers depend on the content of the indexed datasets and the context retrieved for each question.

---

## Testing and Evaluation

The application can be evaluated through functional testing, retrieval testing, and response-quality testing.

### Functional Testing

| Test Case                  | Expected Result                           |
| -------------------------- | ----------------------------------------- |
| Launch Streamlit           | Application starts successfully           |
| Load source data           | Required datasets are available           |
| Prepare text chunks        | Text is divided into retrievable sections |
| Load or create FAISS index | Vector search is available                |
| Submit a question          | The question is processed                 |
| Retrieve context           | Relevant chunks are returned              |
| Generate an answer         | Ollama returns a response                 |
| Display response           | The answer appears in the interface       |

### Retrieval Evaluation

Check whether the text chunks retrieved by FAISS are relevant to the user's question.

### Response Evaluation

Review generated answers for:

- Relevance to the question.
- Correctness against the retrieved information.
- Completeness.
- Clarity and readability.
- Appropriate use of the retrieved context.

Do not report a specific accuracy percentage unless it has been measured using a defined test dataset and evaluation method.

---

## Limitations

- **Dataset dependency:** The chatbot can retrieve only information available in its knowledge base.
- **Data quality:** Missing, outdated, or inconsistent source information can affect responses.
- **Retrieval quality:** Chunking and search settings influence which information is retrieved.
- **LLM limitations:** The language model may generate incomplete or incorrect responses.
- **Hardware requirements:** Running a local language model requires sufficient memory and processing resources.
- **Knowledge freshness:** The knowledge base must be updated when new information becomes available.
- **Career guidance limitations:** Generated information should be treated as assistance for exploration, not as a guaranteed or personalized career decision.

## Future Enhancements

1. Add more verified and regularly updated career-related datasets.
2. Improve data cleaning and preprocessing.
3. Improve text chunking and retrieval quality.
4. Add source references for retrieved information.
5. Add multilingual question answering.
6. Improve career recommendations using relevant user-provided interests, skills, and qualifications.
7. Add a feedback mechanism to review chatbot responses.
8. Evaluate retrieval and answer quality using a structured test dataset.
9. Improve the interface and accessibility.
10. Explore alternative embedding models and language models.

## Conclusion

The Career Guidance Chatbot demonstrates how Retrieval-Augmented Generation can be used to build a domain-focused conversational application.

The project combines career-related data preparation, text embeddings, FAISS-based vector search, and local language-model integration. The Sentence Transformer model converts text into embeddings, FAISS retrieves relevant information, and Phi-3 Mini generates natural-language responses using the retrieved context. Streamlit provides the interface for user interaction.

The project provides practical experience in Python application development, data processing, Natural Language Processing, semantic search, vector databases, local LLM integration, and RAG-based systems.

## Author

**Aruna Waghmare**  
Master of Computer Applications (MCA)  
SNDT Women's University, Mumbai

---

## References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Ollama](https://ollama.com/)
- [Phi-3 Mini on Ollama](https://ollama.com/library/phi3)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [all-MiniLM-L6-v2 Model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [FAISS GitHub Repository](https://github.com/facebookresearch/faiss)

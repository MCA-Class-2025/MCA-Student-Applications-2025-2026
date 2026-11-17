# 🍽 AI Food Recommendation Assistant

An AI-powered Food Recommendation Assistant built using **LangChain**, **Hugging Face**, **FAISS**, and **RAG (Retrieval-Augmented Generation)**. The application allows users to ask food-related questions in natural language and receive intelligent recommendations based on recipe documents.

---

## 📌 Features

- 🍛 Food recommendations using natural language
- 📄 Recipe knowledge base from PDF documents
- 🔍 Semantic search with FAISS
- 🤖 LLM-powered responses
- 🧠 Retrieval-Augmented Generation (RAG)
- 💻 Simple Streamlit web interface

---

## 🛠️ Tech Stack

| Technology      | Purpose              |
| --------------- | -------------------- |
| Python          | Programming Language |
| Streamlit       | Web Interface        |
| LangChain       | RAG Pipeline         |
| Hugging Face    | Sentence Embeddings  |
| FAISS           | Vector Database      |
| PyPDF           | PDF Loading          |
| Ollama / Gemini | Large Language Model |

---

## 📂 Project Structure

```
AI-Food-Recommendation/
│
├── app.py
├── rag.py
├── utils.py
├── requirements.txt
├── README.md
├── .env
│
├── recipes/
│   └── Indian_dishes.pdf
│
└── vectorstore/
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/AI-Food-Recommendation.git

cd AI-Food-Recommendation
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file.

If using Gemini:

```text
GOOGLE_API_KEY=YOUR_API_KEY
```

---

## ▶️ Run the Project

Create the vector database:

```bash
python test.py
```

Run Streamlit:

```bash
streamlit run app.py
```

---

## 📚 How It Works

1. Load recipe PDF documents.
2. Split documents into text chunks.
3. Generate embeddings using Hugging Face.
4. Store embeddings in FAISS.
5. Retrieve relevant chunks based on the user's query.
6. Send retrieved context to the LLM.
7. Display the recommendation in the Streamlit interface.

---

## 🧠 RAG Workflow

```
Recipe PDF
      │
      ▼
PyPDF Loader
      │
      ▼
Text Splitter
      │
      ▼
Embeddings
      │
      ▼
FAISS Vector Store
      │
      ▼
Retriever
      │
      ▼
LLM
      │
      ▼
Food Recommendation
```

---

## 📊 Technologies Used

- Python
- Streamlit
- LangChain
- Hugging Face
- FAISS
- RAG
- PyPDF
- Ollama / Gemini

---

## 📸 Screenshots

Add screenshots such as:

- Home Page
- Recipe Database Creation
- Food Recommendation
- Terminal Output
- VS Code Project Structure

---

## 🚀 Future Improvements

- Voice-based food assistant
- Nutrition information
- Image-based food recognition
- User authentication
- Meal planning
- Multi-language support
- Restaurant recommendations
- Cloud deployment

---

## 👩‍💻 Author

**Tanya Singh**

Master of Computer Applications (MCA)

---

## 📄 License

This project is for educational purposes.

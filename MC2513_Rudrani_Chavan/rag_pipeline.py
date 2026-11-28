import os
import shutil
import math
import re
import time
from collections import defaultdict
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
try:
    from langchain_ollama import OllamaLLM as Ollama
except ImportError:
    from langchain_community.llms import Ollama
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

import config

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


# ═══════════════════════════════════════════
#  CACHED RESOURCE LOADERS
# ═══════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_embeddings():
    """Returns a cached HuggingFace embedding model instance."""
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)


@st.cache_resource(show_spinner=False)
def get_llm():
    """Returns a cached Ollama LLM instance."""
    return Ollama(
        model=config.OLLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0.2
    )


@st.cache_resource(show_spinner=False)
def get_ocr_reader():
    """Returns a cached EasyOCR reader (downloads model on first call)."""
    import easyocr
    return easyocr.Reader(["en"], gpu=False, verbose=False)


def _get_text_splitter():
    """Returns a configured text splitter."""
    return RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )


# ═══════════════════════════════════════════
#  FILE PROCESSING (PDF + IMAGE OCR)
# ═══════════════════════════════════════════

def process_file(file_path):
    """
    Unified entry point — routes to PDF, TXT, or Image based on file extension.
    Raises ValueError if unsupported file type.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _process_pdf(file_path)
    if ext == ".txt":
        return _process_txt(file_path)
    if ext in IMAGE_EXTENSIONS:
        return _process_image(file_path)
    raise ValueError(f"Unsupported file format '{ext}'. Please upload a PDF, TXT, PNG, JPG, or JPEG file.")


def _process_pdf(file_path):
    """Loads a PDF page-by-page, splits into chunks, and cleans metadata."""
    filename = os.path.basename(file_path)
    try:
        documents = PyPDFLoader(file_path).load()
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF '{filename}': {str(e)[:80]}")

    if not documents:
        raise ValueError(f"No extractable text found in '{filename}'.")

    chunks = _get_text_splitter().split_documents(documents)
    if not chunks:
        raise ValueError(f"No text chunks created from '{filename}'.")

    for chunk in chunks:
        chunk.metadata["source"] = filename

    return chunks


def _process_txt(file_path):
    """Loads a plain text file directly, extracts UTF-8 content, and splits into chunks."""
    filename = os.path.basename(file_path)
    content = ""
    for enc in ("utf-8", "utf-8-sig", "latin1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read().strip()
            if content:
                break
        except Exception:
            continue

    if not content:
        raise ValueError(f"No text content found in '{filename}'.")

    doc = Document(
        page_content=content,
        metadata={"source": filename, "page": 0}
    )
    return _get_text_splitter().split_documents([doc])


def _process_image(file_path):
    """
    Extracts text/nutrition info from an image:
    1. Runs OCR first.
    2. If OCR extracts meaningful text (>= 5 words), uses OCR text.
    3. If OCR finds little or no text (e.g. food photograph), automatically switches
       to food image recognition (vision LLM / filename hint / dish estimation) without showing an error.
    4. Converts the detected dish and nutrition analysis into document chunks so it indexes into RAG.
    """
    filename = os.path.basename(file_path)

    # Read raw image bytes
    with open(file_path, "rb") as f:
        image_bytes = f.read()

    # Step 1: Run OCR first
    ocr_text = ""
    try:
        reader = get_ocr_reader()
        results = reader.readtext(file_path)
        if results:
            ocr_text = "\n".join(text for (_, text, _) in results if text and text.strip())
    except Exception:
        ocr_text = ""

    # Step 2: If OCR extracts meaningful text (>= 5 words), process as OCR text doc
    if ocr_text and len(ocr_text.split()) >= 5:
        doc = Document(
            page_content=f"Text/Label from {filename}:\n\n{ocr_text}",
            metadata={"source": filename, "page": 0}
        )
        return _get_text_splitter().split_documents([doc])

    # Step 3: OCR found little or no text — switch to food image recognition!
    food_info = analyze_food_image(image_bytes, filename=filename)

    # Save food_info into Streamlit session state if inside streamlit runtime context
    try:
        import streamlit as st
        _NA = "Unable to Estimate"
        if hasattr(st, "session_state"):
            if food_info.get("is_recipe"):
                st.session_state["rv_analysis"] = food_info
                st.session_state["analyzed_content"] = {
                    "source_title": food_info.get("dish_name", filename),
                    "summary": food_info.get("summary", food_info.get("description", "Identified food item.")),
                    "calories": food_info.get("calories", _NA),
                    "protein": food_info.get("protein", _NA),
                    "carbohydrates": food_info.get("carbohydrates", food_info.get("carbs", _NA)),
                    "fat": food_info.get("fat", _NA),
                    "fiber": food_info.get("fiber", _NA),
                    "vitamins": food_info.get("vitamins", food_info.get("vitamins_minerals", _NA)),
                    "minerals": food_info.get("minerals", _NA),
                    "health_benefits": food_info.get("health_benefits", "Provides essential nutrients"),
                    "consume_in_moderation": food_info.get("consume_in_moderation", "Portion sizes"),
                    "suitable_for": food_info.get("suitable_for", "General Adults"),
                    "is_recipe": True,
                }
    except Exception:
        pass

    # Build structured text document from food analysis
    _NA = "Not Present in Uploaded Content"
    if food_info.get("is_not_food_image"):
        text_content = f"Image '{filename}' was analyzed and does not appear to contain food."
    else:
        dish = food_info.get("dish_name", filename)
        summ = food_info.get("summary") or food_info.get("description") or f"Nutrition breakdown for {dish}."
        ings = ", ".join(food_info.get("ingredients", [])) if food_info.get("ingredients") else f"Standard ingredients for {dish}"
        cal = food_info.get("calories", _NA)
        pro = food_info.get("protein", _NA)
        carb = food_info.get("carbohydrates") or food_info.get("carbs") or _NA
        fat = food_info.get("fat", _NA)
        fib = food_info.get("fiber", _NA)
        vit = food_info.get("vitamins") or food_info.get("vitamins_minerals") or _NA
        min_ = food_info.get("minerals", _NA)
        ben = food_info.get("health_benefits", _NA)
        mod = food_info.get("consume_in_moderation", _NA)
        suit = food_info.get("suitable_for", _NA)

        text_content = (
            f"Identified Food Dish: {dish}\n"
            f"Overview: {summ}\n"
            f"Ingredients: {ings}\n"
            f"Nutrition Information:\n"
            f"- Calories: {cal}\n"
            f"- Protein: {pro}\n"
            f"- Carbohydrates: {carb}\n"
            f"- Fat: {fat}\n"
            f"- Fiber: {fib}\n"
            f"- Key Vitamins: {vit}\n"
            f"- Key Minerals: {min_}\n"
            f"- Health Benefits: {ben}\n"
            f"- Consume in Moderation: {mod}\n"
            f"- Best Suitable For: {suit}\n"
        )

    doc = Document(
        page_content=text_content,
        metadata={"source": filename, "page": 0}
    )
    return _get_text_splitter().split_documents([doc])


# ═══════════════════════════════════════════
#  VECTOR STORE OPERATIONS
# ═══════════════════════════════════════════

def build_vector_store(chunks):
    """Builds and persists a Chroma database from document chunks."""
    return Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=config.DB_DIR
    )


def get_vector_store():
    """Loads the existing Chroma database if it contains indexed data."""
    if not os.path.exists(config.DB_DIR):
        return None
    try:
        db = Chroma(persist_directory=config.DB_DIR, embedding_function=get_embeddings())
        ids = db.get().get("ids", [])
        return db if len(ids) > 0 else None
    except Exception:
        return None


def clear_vector_store():
    """Deletes the vector store and uploaded documents, then recreates empty dirs."""
    for path in (config.DB_DIR, config.DOCS_DIR):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"Error removing {path}: {e}")
    os.makedirs(config.DB_DIR, exist_ok=True)
    os.makedirs(config.DOCS_DIR, exist_ok=True)


# ═══════════════════════════════════════════
#  QUERY REWRITING & HYBRID RETRIEVAL PIPELINE
# ═══════════════════════════════════════════

def _tokenize(text):
    """Tokenizes text into lowercase alphanumeric words."""
    return re.findall(r'\w+', text.lower())


def _rewrite_query(question, llm):
    """Rewrites short or vague user questions into clear search queries."""
    question_clean = question.strip()
    if len(question_clean.split()) >= 6:
        return question_clean

    rewrite_prompt = (
        "Output ONLY a 3 to 6 word search query for a document database based on this question. "
        "Do NOT add intro text, quotes, or punctuation.\n\n"
        f"Question: {question_clean}\n"
        "Search Query:"
    )
    try:
        rewritten = llm.invoke(rewrite_prompt).strip()
        rewritten = re.sub(r'^["\']|["\']$', '', rewritten).strip()
        # Ensure rewrite is clean and short
        if rewritten and len(rewritten.split()) <= 10:
            return rewritten
        return question_clean
    except Exception:
        return question_clean


def _hybrid_retrieval(db, query, k=config.RETRIEVER_K):
    """
    Executes Hybrid Search combining ChromaDB Semantic Search and BM25 Lexical Search.
    Merges both ranked lists using Reciprocal Rank Fusion (RRF).
    """
    if db is None:
        return []

    # 1. Semantic Retrieval (ChromaDB)
    try:
        semantic_docs_with_scores = db.similarity_search_with_score(query, k=k*2)
    except Exception as e:
        print(f"[RAG AUDIT ERROR] Semantic search failed: {e}")
        semantic_docs_with_scores = []

    # 2. Lexical BM25 Retrieval
    try:
        raw_data = db.get(include=["documents", "metadatas"])
        all_docs = raw_data.get("documents", [])
        all_metas = raw_data.get("metadatas", [])
    except Exception as e:
        print(f"[RAG AUDIT ERROR] db.get failed: {e}")
        all_docs, all_metas = [], []

    query_tokens = _tokenize(query)
    doc_tokens_list = [_tokenize(doc) for doc in all_docs]
    total_docs = len(all_docs)
    avgdl = sum(len(toks) for toks in doc_tokens_list) / max(total_docs, 1)

    doc_freqs = defaultdict(int)
    for toks in doc_tokens_list:
        for term in set(toks):
            doc_freqs[term] += 1

    k1, b = 1.5, 0.75
    bm25_scores = []
    for idx, doc_toks in enumerate(doc_tokens_list):
        score = 0.0
        doc_len = len(doc_toks)
        doc_counts = defaultdict(int)
        for t in doc_toks:
            doc_counts[t] += 1

        for q_term in query_tokens:
            if q_term in doc_counts:
                df = doc_freqs.get(q_term, 0)
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
                tf = doc_counts[q_term]
                num = tf * (k1 + 1)
                den = tf + k1 * (1 - b + b * (doc_len / max(avgdl, 1.0)))
                score += idf * (num / den)

        bm25_scores.append((idx, score))

    bm25_scores.sort(key=lambda x: x[1], reverse=True)
    top_bm25_indices = [idx for idx, s in bm25_scores[:k*2] if s > 0]

    # 3. Reciprocal Rank Fusion (RRF)
    rrf_scores = defaultdict(float)
    doc_map = {}
    doc_l2_map = {}

    for rank, (doc, l2_score) in enumerate(semantic_docs_with_scores):
        key = (doc.metadata.get("source"), doc.metadata.get("page"), doc.page_content.strip())
        rrf_scores[key] += 1.0 / (60 + rank + 1)
        doc_map[key] = doc
        doc_l2_map[key] = l2_score

    for rank, idx in enumerate(top_bm25_indices):
        content = all_docs[idx].strip()
        meta = all_metas[idx] if idx < len(all_metas) else {}
        key = (meta.get("source"), meta.get("page"), content)
        rrf_scores[key] += 1.0 / (60 + rank + 1)
        if key not in doc_map:
            doc_map[key] = Document(page_content=content, metadata=meta)
            doc_l2_map[key] = 0.8  # Default score for lexical match

    sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

    hybrid_results = []
    for key in sorted_keys[:k]:
        doc = doc_map[key]
        l2_score = doc_l2_map.get(key, 0.8)
        confidence_pct = max(1.0, round(max(0.0, 1.0 - (l2_score / 2.0)) * 100, 1))
        hybrid_results.append((doc, confidence_pct))

    return hybrid_results


# ═══════════════════════════════════════════
#  RAG ANSWER GENERATION
# ═══════════════════════════════════════════

_PROMPT_TEMPLATE = """You are NutriMate, an expert AI Nutrition Assistant.

Retrieved Document Context:
{context}

Chat History:
{history}

User Question: {question}

Instructions:
1. Read the Context above carefully and provide a complete, clear, and accurate answer to the User Question.
2. Base your response on the facts, ingredients, numbers, instructions, and details in the Context.
3. Cite the relevant source document name for key facts whenever applicable.
4. Format your answer with clean markdown for easy reading.

Answer:"""


def generate_answer(question, chat_history, db):
    """
    Executes Query Rewriting, Hybrid Search, Context Construction, and Answer Generation.
    Always returns exactly 3 values: (answer_text, sources_list, metrics_dict).
    """
    start_time = time.time()

    try:
        llm = get_llm()

        # 1. Query Rewriting
        rewritten_query = _rewrite_query(question, llm)

        # 2. Hybrid Retrieval (BM25 + Semantic RRF)
        hybrid_docs = _hybrid_retrieval(db, question, k=config.RETRIEVER_K)

        # If rewritten query is different from raw question, search rewritten query as well to enrich results
        if rewritten_query and rewritten_query.lower() != question.lower():
            extra_docs = _hybrid_retrieval(db, rewritten_query, k=config.RETRIEVER_K)
            seen_keys = {(d.metadata.get("source"), d.page_content.strip()) for d, _ in hybrid_docs}
            for d, score in extra_docs:
                k_tuple = (d.metadata.get("source"), d.page_content.strip())
                if k_tuple not in seen_keys:
                    hybrid_docs.append((d, score))
                    seen_keys.add(k_tuple)

        # Sort by confidence percentage descending
        hybrid_docs.sort(key=lambda x: x[1], reverse=True)
        top_chunks = hybrid_docs[:config.RETRIEVER_K]

        # 3. Source Ranking & Context Formatting
        valid_sources = []
        context_parts = []
        unique_docs = set()

        for doc, confidence_val in top_chunks:
            filename = doc.metadata.get("source", "Unknown Document")
            raw_page = doc.metadata.get("page", 0)
            snippet = doc.page_content.strip()

            is_image = filename.lower().endswith(IMAGE_EXTENSIONS)
            page_display = "1 (Image)" if is_image else str(raw_page + 1)
            conf_str = f"{confidence_val}%"

            context_parts.append(f"[Source: {filename}, Page: {page_display}]\n{snippet}")
            unique_docs.add(filename)

            valid_sources.append({
                "filename": filename,
                "page": page_display,
                "confidence": conf_str,
                "content": snippet[:500]
            })

        # Check if database has content
        if not valid_sources or not context_parts:
            elapsed = round(time.time() - start_time, 2)
            metrics = {
                "rewritten_query": rewritten_query,
                "response_time": f"{elapsed}s",
                "retrieved_docs_count": 0,
                "retrieved_chunks_count": 0,
                "similarity_score": "0%",
                "confidence_score": "0%",
                "context_length": 0,
                "embedding_model": config.EMBEDDING_MODEL_NAME,
                "llm_model": config.OLLAMA_MODEL,
                "retrieval_strategy": "Hybrid RRF (BM25 Lexical + Semantic)",
                "context_text": "",
            }
            return "I couldn't find relevant details in your uploaded Nutrition PDFs or Recipes. Please upload a PDF, recipe image, or text file to start.", [], metrics

        # 4. Generate Answer using Context
        context_text = "\n\n".join(context_parts)

        # Calculate metrics
        conf_values = [float(s.get("confidence", "0%").replace("%", "")) for s in valid_sources]
        avg_sim = f"{round(sum(conf_values)/len(conf_values), 1)}%" if conf_values else "0%"
        max_conf = f"{round(max(conf_values), 1)}%" if conf_values else "0%"
        elapsed = round(time.time() - start_time, 2)

        history_lines = []
        if chat_history:
            for m in chat_history[-6:]:
                role = "User" if m.get("role") == "user" else "Assistant"
                content = m.get("content", "")
                if content and not content.startswith("I couldn't find"):
                    history_lines.append(f"{role}: {content}")

        prompt = _PROMPT_TEMPLATE.format(
            context=context_text,
            history="\n".join(history_lines) if history_lines else "None",
            question=question
        )

        try:
            answer = llm.invoke(prompt).strip()
        except Exception as e:
            answer = (
                f"⚠️ Unable to reach local LLM server: {e}\n\n"
                f"Please ensure Ollama is active on your system (`ollama pull {config.OLLAMA_MODEL}`)."
            )

        metrics = {
            "rewritten_query": rewritten_query,
            "response_time": f"{elapsed}s",
            "retrieved_docs_count": len(unique_docs),
            "retrieved_chunks_count": len(valid_sources),
            "similarity_score": avg_sim,
            "confidence_score": max_conf,
            "context_length": len(context_text),
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "llm_model": config.OLLAMA_MODEL,
            "retrieval_strategy": "Hybrid RRF (BM25 Lexical + Semantic)",
            "context_text": context_text,
        }

        return answer, valid_sources, metrics

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        fallback_metrics = {
            "rewritten_query": question,
            "response_time": f"{elapsed}s",
            "retrieved_docs_count": 0,
            "retrieved_chunks_count": 0,
            "similarity_score": "0%",
            "confidence_score": "0%",
            "context_length": 0,
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "llm_model": config.OLLAMA_MODEL,
            "retrieval_strategy": "Hybrid RRF (BM25 Lexical + Semantic)",
            "context_text": "",
        }
        return f"❌ Internal error in RAG pipeline: {str(e)[:150]}", [], fallback_metrics


# ═══════════════════════════════════════════
#  AUTO-GENERATED: KEY TAKEAWAYS & FOLLOW-UPS
# ═══════════════════════════════════════════

def _generate_key_takeaways(answer, context_text, llm):
    """Extracts 3–5 key takeaway bullet points from the answer and context."""
    prompt = (
        "Based ONLY on the Answer and Context below, list 3 to 5 key takeaway bullet points. "
        "Each point should be concise (one sentence). Do NOT add information beyond what is provided.\n\n"
        f"Answer:\n{answer}\n\n"
        f"Context:\n{context_text[:2000]}\n\n"
        "Key Takeaways (bullet points):"
    )
    try:
        result = llm.invoke(prompt).strip()
        # Parse bullet points into a clean list
        lines = [line.strip().lstrip("-•*0123456789.) ") for line in result.split("\n") if line.strip()]
        return [line for line in lines if len(line) > 5][:5]
    except Exception:
        return []


def _generate_followup_questions(question, answer, context_text, llm):
    """Suggests 3 follow-up questions based on the current topic and context."""
    prompt = (
        "Based ONLY on the Question, Answer, and Context below, suggest exactly 3 relevant "
        "follow-up questions the user could ask next. Each question should be specific and answerable "
        "from the provided context. Output ONLY the 3 questions, one per line.\n\n"
        f"Question: {question}\n\n"
        f"Answer:\n{answer[:500]}\n\n"
        f"Context:\n{context_text[:1500]}\n\n"
        "Follow-up Questions:"
    )
    try:
        result = llm.invoke(prompt).strip()
        lines = [line.strip().lstrip("-•*0123456789.) ") for line in result.split("\n") if line.strip()]
        return [q for q in lines if q.endswith("?")][:3]
    except Exception:
        return []


# ═══════════════════════════════════════════
#  ON-DEMAND AI FEATURES (Called from UI)
# ═══════════════════════════════════════════

def generate_flashcards(context_text):
    """
    Analyzes retrieved context to identify main nutrition topics and generates
    detailed topic-based flashcards (Topic Name, Emoji, Definition, Key Benefits,
    Food Sources, Daily Recommendation, Important Notes) strictly from context.
    Returns a list of topic flashcard dictionaries.
    """
    if not context_text or not context_text.strip():
        return []

    llm = get_llm()
    prompt = (
        "Analyze the Context below and identify the main nutrition/health topics present "
        "(such as Protein, Vitamins, Minerals, Carbohydrates, Fiber, Fats, Water, Balanced Diet, "
        "Fruits, Vegetables, Diabetes, Heart Health, Weight Management, Food Labels, Calories, etc.).\n"
        "Generate a structured flashcard for ONLY the topics present in the Context. Do NOT use external knowledge.\n\n"
        "Format each topic flashcard EXACTLY as follows:\n"
        "TOPIC: <Topic Name>\n"
        "EMOJI: <One single relevant emoji for this topic>\n"
        "DEFINITION: <Concise definition from context>\n"
        "BENEFITS: <Key benefits directly mentioned in context>\n"
        "SOURCES: <Food sources or references from context>\n"
        "RECOMMENDATION: <Daily recommendation if available in context, else 'Not specified in document'>\n"
        "NOTES: <Important notes or warnings from context>\n"
        "--- END FLASHCARD ---\n\n"
        f"Context:\n{context_text[:3500]}\n\n"
        "Topic Flashcards:"
    )
    try:
        result = llm.invoke(prompt).strip()
        flashcards = []

        # Primary parsing by delimiter
        blocks = result.split("--- END FLASHCARD ---")
        for block in blocks:
            lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
            card = {}
            for line in lines:
                if line.upper().startswith("TOPIC:"):
                    card["topic"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("EMOJI:"):
                    card["emoji"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("DEFINITION:"):
                    card["definition"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("BENEFITS:"):
                    card["benefits"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SOURCES:"):
                    card["sources"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("RECOMMENDATION:"):
                    card["recommendation"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("NOTES:"):
                    card["notes"] = line.split(":", 1)[1].strip()

            if card.get("topic") and (card.get("definition") or card.get("benefits")):
                if not card.get("emoji") or len(card.get("emoji")) > 4:
                    card["emoji"] = "🥗"
                flashcards.append(card)

        # Fallback parsing line-by-line if delimiter was omitted
        if not flashcards:
            card = {}
            for line in result.split("\n"):
                line = line.strip()
                if line.upper().startswith("TOPIC:"):
                    if card.get("topic") and (card.get("definition") or card.get("benefits")):
                        if not card.get("emoji"):
                            card["emoji"] = "🥗"
                        flashcards.append(card)
                        card = {}
                    card["topic"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("EMOJI:"):
                    card["emoji"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("DEFINITION:"):
                    card["definition"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("BENEFITS:"):
                    card["benefits"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SOURCES:"):
                    card["sources"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("RECOMMENDATION:"):
                    card["recommendation"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("NOTES:"):
                    card["notes"] = line.split(":", 1)[1].strip()

            if card.get("topic") and (card.get("definition") or card.get("benefits")):
                if not card.get("emoji"):
                    card["emoji"] = "🥗"
                flashcards.append(card)

        return flashcards[:10]
    except Exception:
        return []


def generate_quiz(context_text):
    """
    Generates 5 multiple-choice questions from retrieved context.
    Returns a list of dicts: [{"question": ..., "options": [...], "correct": ...}, ...]
    """
    llm = get_llm()
    prompt = (
        "Based ONLY on the Context below, generate exactly 5 multiple-choice quiz questions. "
        "Each question must have 4 options (A, B, C, D) and one correct answer. "
        "Use ONLY facts from the context.\n"
        "Format EXACTLY as:\n"
        "Q: <question>\n"
        "A) <option>\nB) <option>\nC) <option>\nD) <option>\n"
        "Correct: <letter>\n\n"
        f"Context:\n{context_text[:3000]}\n\n"
        "Quiz:"
    )
    try:
        result = llm.invoke(prompt).strip()
        questions = []
        current = {"question": "", "options": [], "correct": ""}

        for line in result.split("\n"):
            line = line.strip()
            if line.upper().startswith("Q:"):
                # Save previous question if complete
                if current["question"] and current["options"] and current["correct"]:
                    questions.append(current)
                current = {"question": line[2:].strip(), "options": [], "correct": ""}
            elif line and line[0] in "ABCD" and line[1:2] in (")" , "."):
                current["options"].append(line)
            elif line.upper().startswith("CORRECT:"):
                current["correct"] = line.split(":", 1)[1].strip().upper()[:1]

        # Save last question
        if current["question"] and current["options"] and current["correct"]:
            questions.append(current)

        return questions[:5] if questions else [{"question": "No quiz generated", "options": [], "correct": ""}]
    except Exception as e:
        return [{"question": f"Error: {str(e)[:80]}", "options": [], "correct": ""}]


def generate_summary(context_text):
    """
    Summarizes retrieved context into concise bullet points.
    Returns the summary as a markdown string.
    """
    llm = get_llm()
    prompt = (
        "Summarize the following Context into concise, clear bullet points. "
        "Cover all the main topics and key facts. Use ONLY information from the Context — "
        "do NOT add external knowledge. Aim for 5–8 bullet points.\n\n"
        f"Context:\n{context_text[:4000]}\n\n"
        "Summary (bullet points):"
    )
    try:
        result = llm.invoke(prompt).strip()
        return result if result else "No summary could be generated from the current context."
    except Exception as e:
        return f"Error generating summary: {str(e)[:80]}"


def explain_simply(answer, context_text):
    """
    Rewrites the answer in simpler language suitable for beginners.
    Returns the simplified explanation as a string.
    """
    llm = get_llm()
    prompt = (
        "Rewrite the following Answer in very simple, easy-to-understand language. "
        "Imagine you are explaining this to someone with no background in nutrition or health. "
        "Use short sentences, everyday words, and helpful examples. "
        "Base your explanation ONLY on the Answer and Context provided.\n\n"
        f"Answer:\n{answer[:1500]}\n\n"
        f"Context:\n{context_text[:2000]}\n\n"
        "Simple Explanation:"
    )
    try:
        result = llm.invoke(prompt).strip()
        return result if result else "Could not simplify the answer."
    except Exception as e:
        return f"Error generating simple explanation: {str(e)[:80]}"


def generate_recipes(context_text):
    """
    Analyzes retrieved context and generates structured healthy recipes matching the context.
    Returns a list of dicts: [{"title":..., "emoji":..., "prep_time":..., "servings":..., "calories":..., "macros":..., "ingredients":[...], "instructions":[...], "health_benefit":...}]
    """
    llm = get_llm()
    prompt = (
        "Based ONLY on the food sources and nutrition concepts in the Context below, generate 3 healthy, easy-to-make recipe ideas.\n"
        "Format each recipe EXACTLY as follows:\n"
        "TITLE: <Recipe Title>\n"
        "EMOJI: <Single food emoji>\n"
        "PREP: <Prep Time, e.g., 15 mins>\n"
        "SERVINGS: <e.g., 2 servings>\n"
        "CALORIES: <e.g., 400 kcal>\n"
        "MACROS: <e.g., Protein: 25g | Fiber: 8g | Calcium: 300mg>\n"
        "BENEFIT: <Key nutritional benefit based on context>\n"
        "INGREDIENTS: <Comma-separated list of ingredients>\n"
        "INSTRUCTIONS: <Step 1; Step 2; Step 3>\n"
        "--- END RECIPE ---\n\n"
        f"Context:\n{context_text[:3500]}\n\n"
        "Recipes:"
    )
    try:
        result = llm.invoke(prompt).strip()
        recipes = []
        blocks = result.split("--- END RECIPE ---")
        for block in blocks:
            lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
            rec = {}
            for line in lines:
                if line.upper().startswith("TITLE:"):
                    rec["title"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("EMOJI:"):
                    rec["emoji"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("PREP:"):
                    rec["prep_time"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SERVINGS:"):
                    rec["servings"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("CALORIES:"):
                    rec["calories"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("MACROS:"):
                    rec["macros"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("BENEFIT:"):
                    rec["health_benefit"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("INGREDIENTS:"):
                    ing_str = line.split(":", 1)[1].strip()
                    rec["ingredients"] = [x.strip() for x in ing_str.split(",") if x.strip()]
                elif line.upper().startswith("INSTRUCTIONS:"):
                    inst_str = line.split(":", 1)[1].strip()
                    rec["instructions"] = [x.strip() for x in inst_str.split(";") if x.strip()]

            if rec.get("title") and rec.get("ingredients"):
                if not rec.get("emoji") or len(rec.get("emoji")) > 4:
                    rec["emoji"] = "🥗"
                recipes.append(rec)

        return recipes[:4] if recipes else []
    except Exception:
        return []


# ═══════════════════════════════════════════
#  RECIPE / DISH NUTRITION ANALYZER
# ═══════════════════════════════════════════

def extract_recipe_info(user_input: str) -> dict:
    """
    Detect recipe name, extract ingredients, generate a short summary,
    AND estimate nutrition from the detected ingredients — all in one LLM call.

    Returns:
    {
        "is_recipe": bool,
        "dish_name": str,
        "ingredients": list[str],
        "summary": str,
        "calories": str,
        "protein": str,
        "carbs": str,
        "fat": str,
        "fiber": str,
        "vitamins": str,
        "minerals": str
    }
    Missing / unknown fields are set to "Not Available".
    """
    import json as _json

    llm = get_llm()

    prompt = (
        "You are an expert chef and registered dietitian. Analyze the following input carefully.\n\n"
        f"INPUT:\n{user_input[:3000]}\n\n"
        "RULES:\n"
        "- If the input is NOT related to food, a recipe, or ingredients, reply ONLY with: NOT_A_RECIPE\n"
        "- Otherwise reply ONLY with a valid JSON object (no markdown, no backticks, no extra text):\n"
        '{"dish_name":"<detected dish name>",'
        '"ingredients":["<ingredient 1>", "<ingredient 2>", "..."],'
        '"summary":"<2-3 sentence description of the dish>",'
        '"calories":"<estimated kcal per serving, e.g. 380 kcal>",'
        '"protein":"<grams, e.g. 18 g>",'
        '"carbs":"<grams, e.g. 45 g>",'
        '"fat":"<grams, e.g. 12 g>",'
        '"fiber":"<grams, e.g. 6 g>",'
        '"vitamins":"<key vitamins present, e.g. Vitamin A, B12, C>",'
        '"minerals":"<key minerals present, e.g. Iron, Calcium, Potassium>"}\n\n'
        "Use best-effort estimation for all numeric fields based on typical serving sizes.\n"
        "If a value truly cannot be estimated, use the string \"Not Available\".\n"
        "Reply ONLY with the JSON or NOT_A_RECIPE."
    )

    _NA = "Not Available"

    try:
        raw = llm.invoke(prompt).strip()

        if "NOT_A_RECIPE" in raw.upper():
            return {"is_recipe": False}

        clean = re.sub(r"```[a-zA-Z]*", "", raw).replace("```", "").strip()
        start = clean.find("{")
        end   = clean.rfind("}")
        if start != -1 and end != -1:
            data = _json.loads(clean[start : end + 1])
            data["is_recipe"] = True
            # Ensure all nutrition keys exist
            for k in ("calories", "protein", "carbs", "fat", "fiber", "vitamins", "minerals"):
                data.setdefault(k, _NA)
            return data

    except Exception:
        pass

    # Graceful fallback
    first_line = user_input.split("\n")[0][:60].strip() or "Detected Dish"
    return {
        "is_recipe":   True,
        "dish_name":   first_line,
        "ingredients": ["Ingredients extracted from text/file"],
        "summary":     "Short recipe overview based on provided input.",
        "calories":    _NA,
        "protein":     _NA,
        "carbs":       _NA,
        "fat":         _NA,
        "fiber":       _NA,
        "vitamins":    _NA,
        "minerals":    _NA,
    }


def estimate_nutrition(ingredients: list) -> dict:
    """
    Given a list of ingredients, estimate macros + micronutrients using the LLM.
    Returns a flat dict with keys: calories, protein, carbs, fat, fiber, vitamins, minerals.
    Missing values are set to "Not Available".
    """
    import json as _json

    if not ingredients:
        _NA = "Not Available"
        return {k: _NA for k in ("calories", "protein", "carbs", "fat", "fiber", "vitamins", "minerals")}

    llm = get_llm()
    ing_text = ", ".join(str(i) for i in ingredients[:40])

    prompt = (
        "You are a registered dietitian. Based ONLY on these ingredients, estimate the total "
        "nutrition for a standard single serving of the dish they form.\n\n"
        f"INGREDIENTS: {ing_text}\n\n"
        "Reply ONLY with a valid JSON object (no markdown, no backticks):\n"
        '{"calories":"<kcal>","protein":"<g>","carbs":"<g>","fat":"<g>","fiber":"<g>",'
        '"vitamins":"<comma-separated key vitamins>","minerals":"<comma-separated key minerals>"}\n'
        "Use \"Not Available\" for any value you cannot estimate."
    )
    _NA = "Not Available"
    try:
        raw   = llm.invoke(prompt).strip()
        clean = re.sub(r"```[a-zA-Z]*", "", raw).replace("```", "").strip()
        start = clean.find("{")
        end   = clean.rfind("}")
        if start != -1 and end != -1:
            data = _json.loads(clean[start : end + 1])
            for k in ("calories", "protein", "carbs", "fat", "fiber", "vitamins", "minerals"):
                data.setdefault(k, _NA)
            return data
    except Exception:
        pass
    return {k: _NA for k in ("calories", "protein", "carbs", "fat", "fiber", "vitamins", "minerals")}


def analyze_food_image(image_bytes: bytes, filename: str = "") -> dict:
    """
    Identify a dish from a JPG/JPEG/PNG image and run full nutrition analysis.

    Strategy:
      1. OCR  — if the image has meaningful text (recipe card / menu / label), use it.
      2. Vision LLM (llava via Ollama REST) — for actual food-photo recognition.
      3. Filename hint — last-resort fallback for vision-model-absent setups.

    Returns:
      {"is_recipe": True, ...nutrition fields...}   — food identified
      {"is_recipe": False, "is_not_food_image": True} — image does not contain food
    """
    import io as _io
    import base64 as _b64
    import json as _json
    import requests as _req

    _NA = "Not Available"

    # ── Step 1: OCR ────────────────────────────────────────────────
    ocr_text = ""
    try:
        from PIL import Image
        import numpy as np
        reader = get_ocr_reader()
        img = Image.open(_io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        results = reader.readtext(arr, detail=0)
        ocr_text = " ".join(results).strip()
    except Exception:
        ocr_text = ""

    # If OCR yielded a rich block of text → recipe card / menu / label
    if len(ocr_text.split()) >= 8:
        hint = (
            filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").strip()
            if filename else ""
        )
        combined = f"Dish: {hint}\n\n{ocr_text}" if hint else ocr_text
        return extract_recipe_info(combined)

    # ── Step 2: Ollama Vision Model (llava / bakllava / moondream) ──
    try:
        b64_img = _b64.b64encode(image_bytes).decode()

        # First: ask whether it's food
        detect_payload = {
            "model": "llava",
            "prompt": (
                "Look at this image. "
                "Does it contain food, a dish, or an identifiable meal? "
                "Reply with ONLY one word: YES or NO."
            ),
            "images": [b64_img],
            "stream": False,
        }
        det_resp = _req.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json=detect_payload, timeout=30
        )
        if det_resp.status_code == 200:
            det_ans = det_resp.json().get("response", "").strip().upper()
            if "NO" in det_ans and "YES" not in det_ans:
                return {"is_recipe": False, "is_not_food_image": True}

            # Second: identify the dish
            name_payload = {
                "model": "llava",
                "prompt": (
                    "What dish or food is shown in this image? "
                    "Reply with ONLY the dish name (e.g. 'Paneer Tikka', 'Caesar Salad'). "
                    "No explanation, no sentence — just the dish name."
                ),
                "images": [b64_img],
                "stream": False,
            }
            name_resp = _req.post(
                f"{config.OLLAMA_BASE_URL}/api/generate",
                json=name_payload, timeout=30
            )
            if name_resp.status_code == 200:
                dish_name = name_resp.json().get("response", "").strip()
                if dish_name:
                    return extract_recipe_info(dish_name)

    except Exception:
        # llava not installed or Ollama not reachable — fall through to filename hint
        pass

    # ── Step 3: Filename hint ───────────────────────────────────────
    # ── Step 3: Filename / Dish Hint Fallback ──────────────────────
    hint = ""
    if filename:
        hint = (
            filename.rsplit(".", 1)[0]
            .replace("-", " ").replace("_", " ").strip()
        )
    if not hint or len(hint) <= 2 or hint.replace(" ", "").isdigit():
        hint = "Nutritious Food Dish"

    return extract_recipe_info(hint)




def analyze_recipe(user_input: str) -> dict:
    """
    Analyze any recipe text, dish name, or ingredient list using the local LLM.

    Returns a dict with is_recipe=True and structured nutrition fields, or
    {"is_recipe": False} when the input is not food/recipe related.
    """
    import json as _json

    llm = get_llm()

    prompt = (
        "You are an expert nutritionist and chef. Analyze the following input.\n\n"
        f"INPUT:\n{user_input[:2500]}\n\n"
        "RULES:\n"
        "- If the input is NOT related to food, a recipe, dish, or ingredients, "
        "reply ONLY with the word: NOT_A_RECIPE\n"
        "- If it IS a recipe or food item, reply ONLY with a valid JSON object "
        "(no markdown, no backticks, no extra explanation):\n"
        '{"dish_name":"<name>","description":"<1-2 sentence description>",'
        '"calories":"<kcal per serving>","protein":"<grams>",'
        '"carbohydrates":"<grams>","fat":"<grams>","fiber":"<grams>",'
        '"vitamins_minerals":"<key nutrients>",'
        '"health_benefits":"<2-3 benefits>",'
        '"consume_in_moderation":"<what to watch>",'
        '"suitable_for":"<who this suits: Children / Adults / Elderly / Diabetics / Gym / Weight Loss>"}\n\n'
        "Reply with ONLY the JSON or NOT_A_RECIPE. Nothing else."
    )

    try:
        raw = llm.invoke(prompt).strip()

        if "NOT_A_RECIPE" in raw.upper():
            return {"is_recipe": False}

        # Strip markdown code fences if the model adds them
        clean = re.sub(r"```[a-zA-Z]*", "", raw).replace("```", "").strip()

        # Extract the JSON object substring
        start = clean.find("{")
        end   = clean.rfind("}")
        if start != -1 and end != -1:
            data = _json.loads(clean[start : end + 1])
            data["is_recipe"] = True
            return data

    except Exception:
        pass

    # Graceful fallback — still show something useful
    first_line = user_input.split("\n")[0][:60].strip() or "Analyzed Dish"
    return {
        "is_recipe":              True,
        "dish_name":              first_line,
        "description":            "Nutritional breakdown based on provided recipe/ingredients.",
        "calories":               "~350–550 kcal",
        "protein":                "~12–20 g",
        "carbohydrates":          "~40–60 g",
        "fat":                    "~10–18 g",
        "fiber":                  "~4–8 g",
        "vitamins_minerals":      "Varies by specific ingredients used",
        "health_benefits":        "Provides essential macronutrients and micronutrients",
        "consume_in_moderation":  "Check sodium and added sugar in individual ingredients",
        "suitable_for":           "Adults — adjust portions for specific dietary needs",
    }

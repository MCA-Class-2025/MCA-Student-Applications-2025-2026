import os
import re
import csv
import sys
import json
import pandas as pd
from datetime import datetime

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

from database import (
    get_expenses,
    get_category_totals,
    get_total_income
)

# Raise CSV field size limit so large Gemma_Answer / API_Result cells never fail
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2147483647)


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_DB = "chroma_db"

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

LLM_MODEL = "gemma3:1b"

TOP_K = 5


# ============================================================
# ORIGINAL DATASETS
# ============================================================

API_DATASET_PATHS = {
    "alpha_vantage": "csv/stock_dataset.csv",
    "frankfurter": "csv/economic_dataset.csv",
    "coingecko": "csv/crypto_dataset.csv",
    "fred": "csv/fred_dataset.csv",
    "financial_news": "csv/raw_partner_headlines.csv"
}


# ============================================================
# FUSED CSV FILES
# ============================================================

FUSED_CSV_PATHS = {
    "alpha_vantage": "csv/fused/fused_alpha_vantage.csv",
    "frankfurter": "csv/fused/fused_frankfurter.csv",
    "coingecko": "csv/fused/fused_coingecko.csv",
    "fred": "csv/fused/fused_fred.csv",
    "financial_news": "csv/fused/fused_financial_news.csv"
}


# ============================================================
# EMBEDDINGS, CHROMA, RETRIEVER & GEMMA
# ============================================================

embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

db = Chroma(
    persist_directory=CHROMA_DB,
    embedding_function=embedding
)

retriever = db.as_retriever(
    search_kwargs={
        "k": TOP_K
    }
)

llm = OllamaLLM(
    model=LLM_MODEL
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_filename(value):
    value = str(value)
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "unknown"


def _normalise_col_name(col):
    return re.sub(r"\s+", " ", str(col).replace("\ufeff", "").replace("\xa0", " ")).strip()


def _normalise_key(value):
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def _find_column(df, candidates):
    lookup = {
        _normalise_col_name(column).lower(): column
        for column in df.columns
    }
    for candidate in candidates:
        key = _normalise_col_name(candidate).lower()
        if key in lookup:
            return lookup[key]
    return None


def ask_gemma(instruction_prompt, fallback):
    try:
        result = llm.invoke(instruction_prompt)
        return result
    except Exception as error:
        print("Gemma 3 error:", error)
        return fallback


# ============================================================
# API FUSION HELPERS
# ============================================================

def _clean_api_value(value):
    """Convert API values into stable CSV-safe scalar values."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _api_response_to_rows(api_name, api_result):
    timestamp = datetime.now().isoformat(timespec="seconds")

    if isinstance(api_result, dict):
        row = {
            "Timestamp": timestamp,
            "API_Type": api_name
        }
        for key, value in api_result.items():
            row[key] = _clean_api_value(value)
        return [row]

    return [{
        "Timestamp": timestamp,
        "API_Type": api_name,
        "API_Response": _clean_api_value(api_result)
    }]


def _write_csv(rows, path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if not rows:
        return path

    new_df = pd.DataFrame(rows)

    if os.path.exists(path):
        try:
            existing_df = pd.read_csv(path, low_memory=False)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(keep="last")
            combined_df.to_csv(path, index=False)
        except Exception as error:
            print("CSV append error:", error)
            new_df.to_csv(path, index=False)
    else:
        new_df.to_csv(path, index=False)

    return path


# ============================================================
# FUSE API WITH ORIGINAL DATASET (ALL ORIGINAL VALUES + API_Result)
# ============================================================

def _fuse_with_original_dataset(
    api_name,
    original_csv,
    api_rows,
    answer_row,
    key_mapping=None,
    selected_original_df=None
):
    """
    Fuses ONLY genuine records that exist in the original dataset.
    Preserves 100% of original dataset columns and values without overwriting,
    and appends Timestamp, Question, API_Result, and Gemma_Answer.
    """
    if not original_csv or not os.path.exists(original_csv):
        return {
            "success": False,
            "message": f"Original dataset not found: {original_csv}"
        }

    # Skip fusion completely when no matching record exists in original dataset
    if selected_original_df is None or selected_original_df.empty:
        return {
            "success": True,
            "message": "Record not found in original dataset; fusion skipped.",
            "original_csv": original_csv
        }

    try:
        original_df = pd.read_csv(original_csv, low_memory=False, encoding="utf-8-sig")
        original_df.columns = [_normalise_col_name(c) for c in original_df.columns]
        original_columns = list(original_df.columns)

        working_df = selected_original_df.copy()
        working_df.columns = [_normalise_col_name(c) for c in working_df.columns]

        # Build case/whitespace-insensitive column lookup so original values NEVER get lost
        working_lookup = {col.lower(): col for col in working_df.columns}

        fused_data = {}
        for orig_col in original_columns:
            matched_col = working_lookup.get(orig_col.lower())
            if matched_col is not None:
                fused_data[orig_col] = working_df[matched_col].values
            else:
                fused_data[orig_col] = ["null"] * len(working_df)

        fused_df = pd.DataFrame(fused_data)

        timestamp = (
            answer_row.get("Timestamp", datetime.now().isoformat(timespec="seconds"))
            if isinstance(answer_row, dict)
            else datetime.now().isoformat(timespec="seconds")
        )
        question_text = answer_row.get("Question", "") if isinstance(answer_row, dict) else ""
        api_result_text = answer_row.get("API_Result", "") if isinstance(answer_row, dict) else ""
        answer_text = answer_row.get("Gemma_Answer", "") if isinstance(answer_row, dict) else ""

        fused_df["Timestamp"] = timestamp
        fused_df["Question"] = question_text
        fused_df["API_Result"] = api_result_text
        fused_df["Gemma_Answer"] = answer_text

        extra_cols = ["Timestamp", "Question", "API_Result", "Gemma_Answer"]
        final_cols = original_columns + [c for c in extra_cols if c not in original_columns]
        fused_df = fused_df[final_cols].copy()

        # Clean empty/NaN values cleanly without corrupting numbers
        fused_df = fused_df.astype(object)
        fused_df = fused_df.where(pd.notna(fused_df), "null")
        fused_df = fused_df.replace(r"^\s*$", "null", regex=True)

        fused_path = os.path.join(
            "csv",
            "fused",
            f"fused_{_safe_filename(api_name)}.csv"
        )
        os.makedirs(os.path.dirname(fused_path), exist_ok=True)

        if os.path.exists(fused_path):
            try:
                existing_df = pd.read_csv(fused_path, low_memory=False, encoding="utf-8-sig")
                existing_df.columns = [_normalise_col_name(c) for c in existing_df.columns]
                for col in final_cols:
                    if col not in existing_df.columns:
                        existing_df[col] = "null"
                existing_df = existing_df[final_cols]
                combined_df = pd.concat([existing_df, fused_df], ignore_index=True)
                dedup_cols = original_columns + ["Question"]
                combined_df = combined_df.drop_duplicates(subset=dedup_cols, keep="last")
                combined_df.to_csv(fused_path, index=False)
            except Exception as append_err:
                print("Fused CSV append fallback:", append_err)
                fused_df.to_csv(fused_path, index=False)
        else:
            fused_df.to_csv(fused_path, index=False)

        return {
            "success": True,
            "data": fused_df,
            "fused_csv": fused_path,
            "fusion_mode": "full_original_plus_api_result_and_answer",
            "original_csv": original_csv
        }

    except Exception as error:
        print("Fusion error:", error)
        return {
            "success": False,
            "message": f"CSV fusion failed: {error}"
        }


# ============================================================
# SAVE API ANSWER + FUSION (ONLY 1 FUSED CSV PER API + 1 HISTORY CSV)
# ============================================================

def save_api_answer_and_fuse(
    api_name,
    question,
    api_result,
    answer,
    key_mapping=None,
    original_csv=None,
    selected_original_df=None
):
    """
    1. Always appends every API interaction to csv/fused/api_conversation_history.csv
    2. Fuses matching original dataset rows + API_Result + Gemma_Answer into
       csv/fused/fused_<api_name>.csv ONLY when selected_original_df has genuine rows.
    """
    api_name = _safe_filename(api_name)
    if original_csv is None:
        original_csv = API_DATASET_PATHS.get(api_name)

    FUSION_FOLDER = "csv/fused"
    os.makedirs(FUSION_FOLDER, exist_ok=True)

    timestamp = datetime.now().isoformat(timespec="seconds")
    cleaned_api_result = _clean_api_value(api_result)

    # 1. Central Conversation History
    history_file = os.path.join(FUSION_FOLDER, "api_conversation_history.csv")
    history_row = {
        "Timestamp": timestamp,
        "API_Type": api_name,
        "Question": question,
        "API_Result": cleaned_api_result,
        "Gemma_Answer": str(answer)
    }
    _write_csv([history_row], history_file)

    # 2. Fuse into single API file (fused_<api_name>.csv)
    answer_row = {
        "Timestamp": timestamp,
        "API_Type": api_name,
        "Question": question,
        "API_Result": cleaned_api_result,
        "Gemma_Answer": str(answer)
    }

    fusion_result = _fuse_with_original_dataset(
        api_name=api_name,
        original_csv=original_csv,
        api_rows=_api_response_to_rows(api_name, api_result),
        answer_row=answer_row,
        key_mapping=key_mapping,
        selected_original_df=selected_original_df
    )

    if not fusion_result.get("success"):
        return {
            "success": False,
            "message": fusion_result.get("message", "Fusion failed."),
            "history_file": history_file
        }

    fusion_result.update({"history_file": history_file})
    return fusion_result


# ============================================================
# USER FINANCIAL DATA (PERSONAL EXPENSE DATABASE)
# ============================================================

def get_financial_context():
    try:
        expenses = get_expenses()
        total_expenses = sum(expense[1] for expense in expenses)
        total_income = get_total_income()
        category_totals = get_category_totals()
        balance = total_income - total_expenses

        category_text = ""
        if category_totals:
            for category, amount in category_totals:
                category_text += f"- {category}: ₹{amount:,.2f}\n"
        else:
            category_text = "No category data available."

        expense_text = ""
        if expenses:
            for expense in expenses[:20]:
                amount = expense[1]
                category = expense[2]
                expense_date = expense[3]
                description = expense[4]
                expense_text += f"- ₹{amount:,.2f} | {category} | {expense_date}"
                if description:
                    expense_text += f" | {description}"
                expense_text += "\n"
        else:
            expense_text = "No expenses recorded."

        if total_income > 0:
            income_text = f"Recorded income: ₹{total_income:,.2f}"
            balance_text = f"₹{balance:,.2f}"
        else:
            income_text = "No income has been recorded in the database."
            balance_text = "Cannot calculate a meaningful balance because income is not recorded."

        return f"""
USER FINANCIAL DATA

===================

RECORDED INCOME:

{income_text}

TOTAL RECORDED EXPENSES:

₹{total_expenses:,.2f}

CALCULATED INCOME MINUS EXPENSES:

{balance_text}

EXPENSES BY CATEGORY:

{category_text}

RECORDED EXPENSE TRANSACTIONS:

{expense_text}
"""
    except Exception as error:
        print("Error loading financial data:", error)
        return """
USER FINANCIAL DATA

Financial data could not be loaded from the database.

Do not invent any financial information.
"""


# ============================================================
# FUSED CSV CONTEXT
# ============================================================

def get_fused_csv_context(api_name, question, max_rows=5):
    fused_file = FUSED_CSV_PATHS.get(api_name)
    if not fused_file:
        return f"No fused CSV is configured for {api_name}."
    if not os.path.exists(fused_file):
        return f"Fused CSV not found:\n{fused_file}"

    try:
        question_lower = question.lower()
        search_terms = []

        company_mapping = {
            "apple": ["apple", "aapl"],
            "aapl": ["apple", "aapl"],
            "microsoft": ["microsoft", "msft"],
            "msft": ["microsoft", "msft"],
            "tesla": ["tesla", "tsla"],
            "tsla": ["tesla", "tsla"],
            "amazon": ["amazon", "amzn"],
            "amzn": ["amazon", "amzn"],
            "google": ["google", "alphabet", "googl"],
            "alphabet": ["google", "alphabet", "googl"],
            "googl": ["google", "alphabet", "googl"],
            "meta": ["meta", "facebook"],
            "facebook": ["meta", "facebook"],
            "nvidia": ["nvidia", "nvda"],
            "nvda": ["nvidia", "nvda"],
            "bitcoin": ["bitcoin", "btc"],
            "btc": ["bitcoin", "btc"],
            "ethereum": ["ethereum", "eth"],
            "eth": ["ethereum", "eth"],
            "dogecoin": ["dogecoin", "doge"],
            "doge": ["dogecoin", "doge"],
            "solana": ["solana", "sol"],
            "sol": ["solana", "sol"],
            "cardano": ["cardano", "ada"],
            "ada": ["cardano", "ada"],
            "ripple": ["ripple", "xrp"],
            "xrp": ["ripple", "xrp"]
        }

        for company, terms in company_mapping.items():
            if company in question_lower:
                search_terms.extend(terms)

        ticker_match = re.search(
            r"\b(?:ticker|symbol)\s+(?:is\s+)?([A-Z]{2,10})\b",
            question
        )
        if ticker_match:
            search_terms.append(ticker_match.group(1).upper())

        from apis.financial_news import extract_news_symbol
        market_symbol = extract_news_symbol(question)
        if market_symbol:
            search_terms.append(market_symbol)

        search_terms = list(dict.fromkeys(search_terms))

        if api_name == "financial_news":
            matches = []
            for chunk in pd.read_csv(fused_file, low_memory=False, chunksize=1100000):
                chunk.columns = [str(column).strip() for column in chunk.columns]
                if search_terms:
                    mask = pd.Series(False, index=chunk.index)
                    for column in chunk.columns:
                        if chunk[column].dtype == "object":
                            values = chunk[column].astype(str).str.lower()
                            for term in search_terms:
                                mask = mask | values.str.contains(str(term).lower(), na=False, regex=False)
                    filtered = chunk[mask]
                else:
                    filtered = chunk

                if not filtered.empty:
                    matches.append(filtered)
                    combined = pd.concat(matches, ignore_index=True)
                    if len(combined) >= max_rows:
                        matches = [combined.head(max_rows)]
                        break

            if matches:
                result_df = pd.concat(matches, ignore_index=True).head(max_rows)
            else:
                result_df = pd.read_csv(fused_file, nrows=max_rows, low_memory=False)
        else:
            df = pd.read_csv(fused_file, low_memory=False)
            if df.empty:
                return "The fused CSV is empty."
            df.columns = [str(column).strip() for column in df.columns]

            if search_terms:
                mask = pd.Series(False, index=df.index)
                for column in df.columns:
                    if df[column].dtype == "object":
                        values = df[column].astype(str).str.lower()
                        for term in search_terms:
                            mask = mask | values.str.contains(str(term).lower(), na=False, regex=False)
                result_df = df[mask].head(max_rows)
            else:
                result_df = df.head(max_rows)

        if result_df.empty:
            return "No matching records were found in the fused CSV."

        return result_df.to_string(index=False)

    except Exception as error:
        print("Fused CSV read error:", error)
        return "Unable to read the fused CSV."


# ============================================================
# IMPORT SEPARATED API MODULES & ROUTING
# ============================================================

from apis import (
    alpha_vantage,
    fred,
    frankfurter,
    coingecko,
    financial_news,
)

# Priority order prevents collisions between overlapping datasets/keywords:
# 1. alpha_vantage  -> Stock dataset (Date + price/indicators) & Alpha Vantage news
# 2. fred           -> FRED / Federal Reserve dataset & macro series
# 3. frankfurter    -> Country macro dataset & live currency conversion
# 4. coingecko      -> Crypto dataset & live price
# 5. financial_news -> Headlines/publisher dataset & Marketaux live news
API_MODULES = [
    alpha_vantage,
    fred,
    frankfurter,
    coingecko,
    financial_news,
]


def get_relevant_fused_csv_context(question):
    contexts = []

    if alpha_vantage.can_handle(question):
        context = get_fused_csv_context("alpha_vantage", question, max_rows=5)
        contexts.append(f"ALPHA VANTAGE FUSED CSV\n\n{context}")

    if coingecko.can_handle(question):
        context = get_fused_csv_context("coingecko", question, max_rows=5)
        contexts.append(f"COINGECKO FUSED CSV\n\n{context}")

    if frankfurter.can_handle(question):
        context = get_fused_csv_context("frankfurter", question, max_rows=5)
        contexts.append(f"FRANKFURTER FUSED CSV\n\n{context}")

    if fred.can_handle(question):
        context = get_fused_csv_context("fred", question, max_rows=5)
        contexts.append(f"FRED FUSED CSV\n\n{context}")

    if financial_news.can_handle(question):
        context = get_fused_csv_context("financial_news", question, max_rows=5)
        contexts.append(f"MARKETAUX FINANCIAL NEWS FUSED CSV\n\n{context}")

    if not contexts:
        return "No API-specific fused CSV context is required for this question."

    return "\n\n".join(contexts)


# ============================================================
# NORMAL RAG PROMPT
# ============================================================

prompt = PromptTemplate(
    template="""

You are Finance AI, a personal finance assistant.

You have access to FOUR types of information:

1. USER FINANCIAL DATA
2. INFORMATION FROM UPLOADED FINANCIAL DOCUMENTS
3. FUSED API CSV DATA
4. API information when a live API route is used

Your most important rule is:

DO NOT INVENT OR ASSUME FINANCIAL DATA.

When the user's question is about their own spending,
expenses, income, savings, categories or transactions,
use USER FINANCIAL DATA.

When the question is about financial concepts,
definitions, financial planning concepts, or information
from uploaded documents, use DOCUMENT CONTEXT when relevant.

When the question is about market, economic, currency,
cryptocurrency or financial-news information, use the
FUSED API CSV DATA when relevant.

IMPORTANT RULES:

- Use actual numbers from USER FINANCIAL DATA.
- Do not create expenses that do not exist.
- Do not assume an income amount.
- If no income is recorded, clearly say so.
- Do not claim that an expense exists unless it appears
  in the provided data.
- Do not recommend specific stocks or financial products.
- Give general educational financial guidance.
- Do not invent information.
- Do not change values from the fused API CSV.
- If the fused CSV does not contain the answer, say so.
- Do not treat old CSV data as today's live API data.
- Clearly distinguish historical/fused CSV information
  from live API information.
- Keep the answer clear and practical.

============================================================
USER FINANCIAL DATA
============================================================

{financial_context}

============================================================
DOCUMENT CONTEXT
============================================================

{document_context}

============================================================
FUSED API CSV CONTEXT
============================================================

{fused_api_context}

============================================================
USER QUESTION
============================================================

{question}

============================================================
ANSWER
============================================================
""",
    input_variables=[
        "financial_context",
        "document_context",
        "fused_api_context",
        "question"
    ]
)


# ============================================================
# CHROMA DOCUMENT RETRIEVAL
# ============================================================

def retrieve_documents(question):
    """Retrieve document chunks from Chroma without crashing the request."""
    try:
        docs = retriever.invoke(question)
    except Exception as error:
        print("Error retrieving documents:", error)
        return []

    if not docs:
        return []

    unique_docs = []
    seen = set()

    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", 0)
        content = str(getattr(doc, "page_content", "")).strip()

        key = (
            doc.metadata.get("id")
            or doc.metadata.get("chunk_id")
            or f"{source}|{page}|{content}"
        )

        if key in seen:
            continue

        seen.add(key)
        unique_docs.append(doc)

    return unique_docs


# ============================================================
# MAIN ASK QUESTION ENTRY POINT
# ============================================================

def ask_question(question):
    print("\n[RUNNING RAG FILE]", os.path.abspath(__file__))

    question = question.strip()
    if not question:
        return ("Please enter a question.", [])

    # ========================================================
    # 1. API + DATASET + FUSION ROUTING (5 SEPARATED APIs)
    # ========================================================
    for api_module in API_MODULES:
        if api_module.can_handle(question):
            print(f"[ROUTING TO API MODULE]: {api_module.API_NAME}")
            return api_module.handle(question)

    # ========================================================
    # 2. NORMAL RAG (PERSONAL EXPENSES + PDFs + FUSED CSVs)
    # ========================================================
    financial_context = get_financial_context()
    docs = retrieve_documents(question)

    print("\n======================================")
    print("USER QUESTION:")
    print(question)
    print("\nRETRIEVED DOCUMENTS:")
    print("Number of documents:", len(docs))

    for index, doc in enumerate(docs):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", 0)
        print(f"{index + 1}. {source} | Page {page + 1}")
    print("======================================\n")

    if docs:
        context_parts = []
        seen_chunks = set()

        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", 0)
            content = str(getattr(doc, "page_content", "")).strip()

            chunk_id = (
                doc.metadata.get("id")
                or doc.metadata.get("chunk_id")
                or f"{source}|{page}|{content}"
            )

            if chunk_id in seen_chunks:
                continue

            seen_chunks.add(chunk_id)

            context_parts.append(
                f"""
SOURCE: {os.path.basename(source)}
PAGE: {page + 1}

{content}
"""
            )

        document_context = (
            "\n\n".join(context_parts)
            if context_parts
            else "No relevant information was found in the uploaded documents."
        )
    else:
        document_context = "No relevant information was found in the uploaded documents."

    fused_api_context = get_relevant_fused_csv_context(question)

    print("\n======================================")
    print("FUSED API CSV CONTEXT")
    print(fused_api_context)
    print("======================================\n")

    final_prompt = prompt.format(
        financial_context=financial_context,
        document_context=document_context,
        fused_api_context=fused_api_context,
        question=question
    )

    answer = ask_gemma(
        final_prompt,
        "Sorry, I was unable to generate an answer using Gemma 3."
    )

    return answer, docs
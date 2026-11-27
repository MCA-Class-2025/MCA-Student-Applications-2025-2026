import os
import re
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from groq import Groq

# Load .env variables
if not os.environ.get("GROQ_API_KEY") and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_CLIENT = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def build_documents(df):
    """Builds targeted semantic chunks per country tagged with metadata."""
    docs = []
    
    # Global baselines for comparative evaluation
    avg_happiness = df["happiness_score"].mean() if "happiness_score" in df.columns else 5.40
    avg_life_exp = df["wb_life_expectancy"].mean() if "wb_life_expectancy" in df.columns else 73.4

    for _, row in df.iterrows():
        c = row.get("country", "")
        iso3 = row.get("iso3", "N/A")
        
        # 1. Quantitative Indicators Chunk
        q_metrics = [
            f"[Country: {c} | ISO3: {iso3} | Domain: Quantitative Indicators]",
            f"Happiness Rank: {row.get('happiness_rank', 'N/A')}",
            f"Happiness Score: {row.get('happiness_score', 'N/A')} (Global Avg: {avg_happiness:.2f})",
            f"Log GDP Per Capita: {row.get('log_gdp_per_capita', 'N/A')}",
            f"Social Support: {row.get('social_support', 'N/A')}",
            f"Healthy Life Expectancy (WHR): {row.get('healthy_life_expectancy', 'N/A')}",
            f"World Bank Life Expectancy: {row.get('wb_life_expectancy', 'N/A')} years (Global Avg: {avg_life_exp:.2f})",
            f"World Bank GDP: ${row.get('wb_gdp_usd', 0):,.0f} USD" if pd.notna(row.get('wb_gdp_usd')) else "World Bank GDP: N/A",
            f"Freedom: {row.get('freedom', 'N/A')}, Generosity: {row.get('generosity', 'N/A')}, Corruption Perception: {row.get('corruption_perception', 'N/A')}"
        ]
        docs.append("\n".join(q_metrics))

        # 2. Climate & Geography Chunk
        geo = [
            f"[Country: {c} | ISO3: {iso3} | Domain: Climate & Geography]",
            f"Capital City: {row.get('capital', 'N/A')}",
            f"Continental Region: {row.get('region', 'N/A')} ({row.get('subregion', 'N/A')})",
            f"Coordinates: {row.get('latitude', 'N/A')}°N, {row.get('longitude', 'N/A')}°E",
            f"Annual Mean Temperature: {row.get('annual_mean_temp_c', 'N/A')}°C",
            f"Annual Precipitation: {row.get('annual_precipitation_mm', 'N/A')} mm",
            f"Official Currency: {row.get('currency_code', 'N/A')} (Exchange Rate to USD: {row.get('exchange_rate_usd', 'N/A')})"
        ]
        docs.append("\n".join(geo))

        # 3. Domain Section Chunks
        hist = row.get("wiki_history")
        if pd.notna(hist) and len(str(hist)) > 30:
            docs.append(f"[Country: {c} | ISO3: {iso3} | Domain: History]\n{hist}")
        
        gov = row.get("wiki_government")
        if pd.notna(gov) and len(str(gov)) > 30:
            docs.append(f"[Country: {c} | ISO3: {iso3} | Domain: Government & Geopolitics]\n{gov}")

        econ = row.get("wiki_economy")
        if pd.notna(econ) and len(str(econ)) > 30:
            docs.append(f"[Country: {c} | ISO3: {iso3} | Domain: Economy & Industry]\n{econ}")

        culture = row.get("wiki_culture")
        if pd.notna(culture) and len(str(culture)) > 30:
            docs.append(f"[Country: {c} | ISO3: {iso3} | Domain: Culture, Society & Demographics]\n{culture}")

        lead = row.get("wiki_summary")
        if pd.notna(lead) and len(str(lead)) > 30:
            docs.append(f"[Country: {c} | ISO3: {iso3} | Domain: Overview & Identity]\n{lead}")

    # Top-10 Leaderboard Chunk
    if "happiness_rank" in df.columns:
        sorted_df = df.sort_values("happiness_rank")
        t5 = [f"#{int(r['happiness_rank'])} {r['country']} (Score: {r['happiness_score']:.2f})" for _, r in sorted_df.head(5).iterrows()]
        docs.append("[Domain: Global Leaderboard]\nTop 5 Happiest Nations:\n" + "\n".join(t5))

    return docs

def build_faiss_index(docs):
    embeddings = EMBED_MODEL.encode(docs, normalize_embeddings=True).astype("float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index

def retrieve_context(query, index, docs, k=8):
    """Entity-aware hybrid retrieval with metadata prioritization and k=8 scaling."""
    q_lower = query.lower()
    
    # 1. Identify country entity in query
    matched_country = None
    for doc in docs:
        if "[Country:" in doc:
            c_name = doc.split("[Country:")[1].split("|")[0].strip()
            if c_name.lower() in q_lower:
                matched_country = c_name
                break

    # 2. Dense vector search
    q_vec = EMBED_MODEL.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(q_vec, k * 3)

    retrieved = []
    seen = set()

    for score, idx in zip(scores[0], indices[0]):
        text = docs[idx]
        final_score = float(score)
        
        # Entity boost
        if matched_country and f"[Country: {matched_country}" in text:
            final_score += 0.25

        retrieved.append({"text": text, "score": final_score})

    retrieved.sort(key=lambda x: x["score"], reverse=True)

    final_chunks = []
    for item in retrieved:
        if item["text"] not in seen:
            seen.add(item["text"])
            final_chunks.append(item)
        if len(final_chunks) == k:
            break

    return final_chunks

SYSTEM_PROMPT = """You are CountryWise AI, the definitive Sovereign Country Knowledge Encyclopedia.
Your objective is to provide comprehensive, factual, and encyclopedic answers using solely the verified context below.

Structure your responses using the following framework whenever answering country profile queries:
1. **Quick Facts Bar**: Bulleted list summarizing Capital, Region, Currency, Annual Climate, and Happiness Rank/Score (if available in context).
2. **Thematic Breakdown**: Provide in-depth narrative paragraphs with bold headers addressing the user's specific questions (e.g., History, Economy, Governance, Culture).
3. **Comparative Context**: Relate the country's indicators (e.g., Life Expectancy, Happiness Score, GDP) against global or regional averages present in the context.

Rules:
- Strictly adhere to the provided context. Do not invent facts, events, or statistics.
- If a specific indicator or topic is not in the context, explicitly state that it is not recorded in the database.
- For non-country queries (e.g., stock market tickers, medical advice, cooking recipes), respond: 'I do not have that information in my knowledge base.'"""

def stream_rag(query, index, docs, k=8):
    global GROQ_CLIENT, GROQ_API_KEY
    if not GROQ_CLIENT:
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
        if GROQ_API_KEY:
            GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)
        else:
            raise ValueError("GROQ_API_KEY not configured.")

    retrieved = retrieve_context(query, index, docs, k=k)
    context_str = "\n\n---\n\n".join([item["text"] for item in retrieved])

    response = GROQ_CLIENT.chat.completions.create(
        model="openai/gpt-oss-20b",
        temperature=0.1,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
        ]
    )
    return response, retrieved
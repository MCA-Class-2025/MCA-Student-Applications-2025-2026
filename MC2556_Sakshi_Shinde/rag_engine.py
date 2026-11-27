import os
import pickle
import numpy as np
import faiss

# Dynamic imports to avoid loading local models unless selected
_local_embedding_model = None


# ============================================================
# EMBEDDING SERVICE
# ============================================================

class EmbeddingService:

    def __init__(self, provider="local", api_key=None, model_name=None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name

        # ----------------------------------------------------
        # Gemini Embeddings
        # ----------------------------------------------------
        if self.provider == "gemini":

            import google.generativeai as genai

            if not self.api_key:
                raise ValueError(
                    "Gemini API key is required for Gemini Embeddings."
                )

            genai.configure(api_key=self.api_key)

            self.model_name = (
                model_name or "models/text-embedding-004"
            )

            self.dimension = 768

        # ----------------------------------------------------
        # OpenAI Embeddings
        # ----------------------------------------------------
        elif self.provider == "openai":

            from openai import OpenAI

            if not self.api_key:
                raise ValueError(
                    "OpenAI API key is required for OpenAI Embeddings."
                )

            self.client = OpenAI(api_key=self.api_key)

            self.model_name = (
                model_name or "text-embedding-3-small"
            )

            if "3-small" in self.model_name:
                self.dimension = 1536

            elif "3-large" in self.model_name:
                self.dimension = 3072

            else:
                self.dimension = 1536

        # ----------------------------------------------------
        # Local Sentence Transformer Embeddings
        # ----------------------------------------------------
        else:

            global _local_embedding_model

            if _local_embedding_model is None:

                from sentence_transformers import SentenceTransformer

                # Cache local model globally to avoid reloading
                _local_embedding_model = SentenceTransformer(
                    model_name or "all-MiniLM-L6-v2"
                )

            self.model = _local_embedding_model

            self.dimension = (
                self.model.get_sentence_embedding_dimension()
            )

    # ========================================================
    # GET EMBEDDINGS
    # ========================================================

    def get_embeddings(
        self,
        texts: list[str],
        is_query=False
    ) -> np.ndarray:

        if not texts:
            return np.empty(
                (0, self.dimension),
                dtype=np.float32
            )

        # ----------------------------------------------------
        # Gemini
        # ----------------------------------------------------
        if self.provider == "gemini":

            import google.generativeai as genai

            task_type = (
                "retrieval_query"
                if is_query
                else "retrieval_document"
            )

            embeddings = []

            # Maximum batch size
            batch_size = 100

            for i in range(
                0,
                len(texts),
                batch_size
            ):

                batch = texts[
                    i:i + batch_size
                ]

                response = genai.embed_content(
                    model=self.model_name,
                    content=batch,
                    task_type=task_type
                )

                if "embedding" in response:

                    if len(batch) == 1:

                        embeddings.append(
                            response["embedding"]
                        )

                    else:

                        embeddings.extend(
                            response["embedding"]
                        )

            return np.array(
                embeddings,
                dtype=np.float32
            )

        # ----------------------------------------------------
        # OpenAI
        # ----------------------------------------------------
        elif self.provider == "openai":

            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )

            embeddings = [
                item.embedding
                for item in response.data
            ]

            return np.array(
                embeddings,
                dtype=np.float32
            )

        # ----------------------------------------------------
        # Local Sentence Transformers
        # ----------------------------------------------------
        else:

            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True
            )

            return embeddings.astype(
                np.float32
            )


# ============================================================
# FAISS INDEX
# ============================================================

class FAISSIndex:

    def __init__(self, dimension: int):

        self.dimension = dimension

        # Inner Product index
        # After L2 normalization this behaves like
        # cosine similarity
        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.documents = []

    # ========================================================
    # ADD DOCUMENTS
    # ========================================================

    def add_documents(
        self,
        docs: list[dict],
        embeddings: np.ndarray
    ):

        if len(embeddings) == 0:
            return

        # L2 normalization
        norms = np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True
        )

        normalized_embeddings = (
            embeddings /
            (norms + 1e-10)
        )

        self.index.add(
            normalized_embeddings.astype(
                "float32"
            )
        )

        self.documents.extend(
            docs
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 4
    ) -> list[dict]:

        if self.index.ntotal == 0:
            return []

        # Flatten query
        query_embedding = (
            query_embedding.flatten()
        )

        # Normalize query
        norm = np.linalg.norm(
            query_embedding
        )

        normalized_query = (
            query_embedding /
            (norm + 1e-10)
        )

        query_vec = np.expand_dims(
            normalized_query,
            axis=0
        ).astype("float32")

        # Search FAISS
        scores, indices = self.index.search(
            query_vec,
            min(k, self.index.ntotal)
        )

        results = []

        for score, idx in zip(
            scores[0],
            indices[0]
        ):

            if (
                idx == -1
                or idx >= len(self.documents)
            ):
                continue

            doc = self.documents[idx]

            results.append(
                {
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": float(score)
                }
            )

        return results

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        filepath: str
    ):

        # Save FAISS index
        faiss.write_index(
            self.index,
            filepath + ".index"
        )

        # Save documents
        with open(
            filepath + ".docs",
            "wb"
        ) as f:

            pickle.dump(
                self.documents,
                f
            )

    # ========================================================
    # LOAD
    # ========================================================

    @classmethod
    def load(
        cls,
        filepath: str
    ):

        # Load FAISS index
        index = faiss.read_index(
            filepath + ".index"
        )

        # Load document mapping
        with open(
            filepath + ".docs",
            "rb"
        ) as f:

            documents = pickle.load(f)

        instance = cls(
            index.d
        )

        instance.index = index
        instance.documents = documents

        return instance


# ============================================================
# LLM QUERY SERVICE
# ============================================================

class LLMQueryService:

    def __init__(
        self,
        provider="local",
        api_key=None,
        model_name=None
    ):

        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name

    # ========================================================
    # GENERATE RESPONSE
    # ========================================================

    def generate_response(
        self,
        question: str,
        retrieved_docs: list[dict],
        temperature: float = 0.3
    ) -> str:

        # ----------------------------------------------------
        # 1. BUILD CONTEXT
        # ----------------------------------------------------

        context_items = []

        for idx, doc in enumerate(
            retrieved_docs
        ):

            src = doc["metadata"]["source"]
            page = doc["metadata"]["page"]
            text = doc["text"]

            context_items.append(
                f"[{idx + 1}] "
                f"Source: {src} "
                f"(Page {page})\n"
                f"Content: {text}"
            )

        if context_items:

            context_str = "\n\n".join(
                context_items
            )

        else:

            context_str = (
                "No relevant context found "
                "in documents."
            )

        # ----------------------------------------------------
        # 2. BUILD PROMPT
        # ----------------------------------------------------

        prompt = (
            "You are DocuMind AI, an advanced "
            "Retrieval-Augmented Generation (RAG) assistant.\n\n"

            "Your task is to answer the user's question "
            "based strictly on the provided retrieved context.\n\n"

            "If the answer cannot be found or inferred "
            "from the context, state that you do not know "
            "or that the information is not present "
            "in the files.\n\n"

            "Do not fabricate facts.\n\n"

            "Guidelines:\n"
            "- Answer clearly and comprehensively.\n"
            "- Cite source documents using their "
            "bracketed numbers such as [1], [2].\n"
            "- Rely only on the provided facts.\n"
            "- Do not invent information.\n\n"

            f"--- RETRIEVED CONTEXT ---\n"
            f"{context_str}\n\n"

            f"--- USER QUESTION ---\n"
            f"{question}\n\n"

            "--- RESPONSE ---"
        )

        # ====================================================
        # GEMINI
        # ====================================================

        if self.provider == "gemini":

            import google.generativeai as genai

            if not self.api_key:

                return (
                    "Error: Gemini API key is missing. "
                    "Please check your .env file."
                )

            try:

                # Configure Gemini
                genai.configure(
                    api_key=self.api_key
                )

                # IMPORTANT:
                # Old model gemini-1.5-flash was removed.
                # We now use Gemini 2.5 Flash.
                model_to_use = (
                    self.model_name
                    or "gemini-3.5-flash"
                )

                model = genai.GenerativeModel(
                    model_to_use
                )

                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=temperature
                    )
                )

                if response.text:

                    return response.text

                return (
                    "Gemini returned an empty response."
                )

            except Exception as e:

                return (
                    "Error calling Gemini LLM API: "
                    f"{str(e)}"
                )

        # ====================================================
        # OPENAI
        # ====================================================

        elif self.provider == "openai":

            from openai import OpenAI

            if not self.api_key:

                return (
                    "Error: OpenAI API key is missing."
                )

            try:

                client = OpenAI(
                    api_key=self.api_key
                )

                model_to_use = (
                    self.model_name
                    or "gpt-4o-mini"
                )

                response = (
                    client.chat.completions.create(
                        model=model_to_use,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=temperature
                    )
                )

                return (
                    response
                    .choices[0]
                    .message
                    .content
                )

            except Exception as e:

                return (
                    "Error calling OpenAI API: "
                    f"{str(e)}"
                )

        elif self.provider == "groq":
            return "Error: Groq API is not supported in this version. Only Gemini, OpenAI, and local modes are enabled."

        # ====================================================
        # LOCAL OFFLINE MODE
        # ====================================================

        else:

            if not retrieved_docs:

                return (
                    "**[Offline Mode]** "
                    "I could not find any relevant "
                    "context in the uploaded files. "
                    "Please upload files and build "
                    "the vector database, or check "
                    "your query terms."
                )

            synthesis = (
                "**[Offline Mode Synthesis]**\n\n"
                "I am running in local offline synthesis "
                "mode because no API keys are active.\n\n"
                "Here is a compilation of the most "
                "relevant points found in your documents:\n\n"
            )

            for idx, doc in enumerate(
                retrieved_docs
            ):

                src = doc["metadata"]["source"]
                page = doc["metadata"]["page"]
                snippet = doc["text"]

                # Limit snippet length
                if len(snippet) < 300:

                    short_snippet = snippet

                else:

                    short_snippet = (
                        snippet[:300]
                        + "..."
                    )

                synthesis += (
                    f"- **Excerpt [{idx + 1}] "
                    f"from '{src}' "
                    f"(Page {page})**:\n"
                    f'  "{short_snippet}"\n\n'
                )

            synthesis += (
                "\n*This answer was generated locally from the retrieved document context. "
                "No Gemini or OpenAI chatbot quota was used.*"
            )

            return synthesis

    # ========================================================
    # BUILD CONTEXT HELPER (shared by extended features)
    # ========================================================

    def _build_context_str(self, retrieved_docs: list[dict]) -> str:
        """Format retrieved FAISS chunks into a single context string."""
        context_items = []
        for idx, doc in enumerate(retrieved_docs):
            src = doc["metadata"]["source"]
            page = doc["metadata"]["page"]
            text = doc["text"]
            context_items.append(
                f"[{idx + 1}] Source: {src} (Page {page})\nContent: {text}"
            )
        return "\n\n".join(context_items) if context_items else "No relevant context found."

    def _call_llm(self, prompt: str, temperature: float = 0.3) -> str:
        """Low-level LLM invocation for extended document features."""
        if self.provider == "gemini":
            import google.generativeai as genai
            if not self.api_key:
                return "Error: Gemini API key is missing."
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name or "gemini-3.5-flash")
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(temperature=temperature),
                )
                return response.text or "Gemini returned an empty response."
            except Exception as e:
                return f"Error calling Gemini LLM API: {str(e)}"

        elif self.provider == "openai":
            from openai import OpenAI
            if not self.api_key:
                return "Error: OpenAI API key is missing."
            try:
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model_name or "gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Error calling OpenAI API: {str(e)}"

        return "**[Offline Mode]** API key required for this feature."

    # ========================================================
    # DOCUMENT FEATURES: questions, evaluation, summary
    # ========================================================

    def generate_questions(
        self,
        retrieved_docs: list[dict],
        num_questions: int = 5,
        temperature: float = 0.4,
    ) -> str:
        """Generate comprehension questions from retrieved document context."""
        context_str = self._build_context_str(retrieved_docs)
        prompt = (
            f"You are DocuMind AI. Based ONLY on the document context below, "
            f"generate exactly {num_questions} thoughtful comprehension questions.\n\n"
            "Format as a numbered list (1. ... 2. ...).\n"
            "Questions must be answerable from the context.\n\n"
            f"--- DOCUMENT CONTEXT ---\n{context_str}\n\n"
            f"--- GENERATE {num_questions} QUESTIONS ---"
        )
        return self._call_llm(prompt, temperature=temperature)

    def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        retrieved_docs: list[dict],
        temperature: float = 0.2,
    ) -> str:
        """Evaluate a user's answer against document context."""
        context_str = self._build_context_str(retrieved_docs)
        prompt = (
            "You are DocuMind AI acting as an answer evaluator.\n\n"
            "Using ONLY the document context, evaluate the user's answer to the question.\n\n"
            "Return your evaluation in this exact structure:\n"
            "**Score:** X/10\n"
            "**Correct Points:**\n- ...\n"
            "**Missing Points:**\n- ...\n"
            "**Improvement Suggestions:**\n- ...\n\n"
            f"--- DOCUMENT CONTEXT ---\n{context_str}\n\n"
            f"--- QUESTION ---\n{question}\n\n"
            f"--- USER ANSWER ---\n{user_answer}\n\n"
            "--- EVALUATION ---"
        )
        return self._call_llm(prompt, temperature=temperature)

    def generate_document_summary(
        self,
        retrieved_docs: list[dict],
        temperature: float = 0.3,
    ) -> str:
        """Generate structured document summary from retrieved context."""
        context_str = self._build_context_str(retrieved_docs)
        prompt = (
            "You are DocuMind AI. Summarize the document context below.\n\n"
            "Return your response in this exact structure:\n"
            "**Short Summary:** (2-3 sentences)\n\n"
            "**Detailed Summary:** (1-2 paragraphs)\n\n"
            "**Key Points:**\n- ...\n\n"
            "**Important Entities:**\n- ...\n\n"
            f"--- DOCUMENT CONTEXT ---\n{context_str}\n\n"
            "--- SUMMARY ---"
        )
        return self._call_llm(prompt, temperature=temperature)
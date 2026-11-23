import math
import re
from typing import List, Dict, Any

try:
    from backend.fusion import DataLevelFusion, FeatureLevelFusion, DecisionLevelFusion
except ModuleNotFoundError:
    from fusion import DataLevelFusion, FeatureLevelFusion, DecisionLevelFusion

class RAGEngine:
    """
    Retrieval-Augmented Generation (RAG) Engine.
    Provides semantic vector-like TF-IDF retrieval across technical knowledge bases,
    database question banks, ideal answers, and job domain profiles.
    """

    def __init__(self, base_dir=None):
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self.data_fusion = DataLevelFusion(base_dir)
        self.feature_fusion = FeatureLevelFusion()
        self.decision_fusion = DecisionLevelFusion()
        self.fusion_status: Dict[str, Any] = {}
        self._database_indexed = False

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        text = text.lower()
        tokens = re.findall(r"[a-z0-9+#.]+", text)
        stop_words = {
            "a", "an", "the", "in", "on", "of", "to", "is", "are", "was", "were",
            "and", "or", "for", "with", "what", "how", "why", "which", "this", "that",
            "can", "you", "explain", "difference", "between", "used", "does", "do"
        }
        return [t for t in tokens if len(t) > 1 and t not in stop_words]

    def build_index(self, db_session=None):
        """Build the index from local database and pre-stored technical domain knowledge."""
        database_records = []
        
        # 1. Pull database items if session is provided
        if db_session:
            try:
                try:
                    from backend.models import AnswerKnowledge, QuestionItem
                except ModuleNotFoundError:
                    from models import AnswerKnowledge, QuestionItem

                # Add AnswerKnowledge records
                records = db_session.query(AnswerKnowledge).all()
                for r in records:
                    database_records.append({
                        "source": "database_answer_knowledge",
                        "title": r.question_text,
                        "content": f"Question: {r.question_text}\nIdeal Answer: {r.ideal_answer}\nKeywords: {r.keywords_json}",
                        "ideal_answer": r.ideal_answer,
                        "category": "technical"
                    })

                # Add QuestionItem records
                questions = db_session.query(QuestionItem).all()
                for q in questions:
                    database_records.append({
                        "source": "database_question_item",
                        "title": q.question_text,
                        "content": f"Question: {q.question_text}\nCategory: {q.category}\nDifficulty: {q.difficulty}\nRound: {q.round_type}",
                        "ideal_answer": "",
                        "category": q.category
                    })
            except Exception as e:
                print("RAGEngine DB indexing notice:", e)

        knowledge_records = []
        question_bank_records = []
        try:
            try:
                from backend.ai_service import ANSWER_KNOWLEDGE, QUESTION_BANK
            except ModuleNotFoundError:
                from ai_service import ANSWER_KNOWLEDGE, QUESTION_BANK

            for q_text, data in ANSWER_KNOWLEDGE.items():
                knowledge_records.append({
                    "source": "knowledge_base",
                    "title": q_text,
                    "content": f"Question: {q_text}\nIdeal Answer: {data.get('answer', '')}\nKeywords: {data.get('keywords', [])}",
                    "ideal_answer": data.get("answer", ""),
                    "category": "technical"
                })

            for domain, q_list in QUESTION_BANK.items():
                for q_item in q_list:
                    question_bank_records.append({
                        "source": "question_bank",
                        "title": q_item,
                        "content": f"Domain: {domain}\nQuestion: {q_item}",
                        "ideal_answer": "",
                        "category": domain
                    })
        except Exception as e:
            print("RAGEngine static knowledge indexing notice:", e)

        unified_records = self.data_fusion.fuse(
            database_records,
            knowledge_records,
            question_bank_records,
        )
        self.documents = [
            {
                **record,
                "title": record["question"],
                "content": (
                    f"Question: {record['question']}\n"
                    f"Ideal Answer: {record['answer']}\n"
                    f"Category: {record['category']}\n"
                    f"Skill: {record['skill']}\n"
                    f"Difficulty: {record['difficulty']}"
                ),
                "ideal_answer": record["answer"],
            }
            for record in unified_records
        ]
        self.fusion_status = {
            "data_level_fusion": True,
            "feature_level_fusion": True,
            "decision_level_fusion": True,
            **self.data_fusion.last_status,
        }
        self._database_indexed = db_session is not None
        self._compute_tfidf()

    def _compute_tfidf(self):
        N = len(self.documents)
        if N == 0:
            return

        doc_tokens = [self._tokenize(doc["content"]) for doc in self.documents]
        df: Dict[str, int] = {}
        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1

        self.idf = {t: math.log((N + 1) / (df_val + 1)) + 1.0 for t, df_val in df.items()}
        self.doc_vectors = []

        for tokens in doc_tokens:
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            
            vec = {}
            total = len(tokens) or 1
            for t, count in tf.items():
                vec[t] = (count / total) * self.idf.get(t, 1.0)
            self.doc_vectors.append(vec)

    def retrieve_relevant_context(self, query: str, top_k: int = 3, category_filter: str = None, query_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve candidates, apply feature fusion, then rank with decision fusion."""
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)

        # Calculate query TF-IDF vector
        q_tf: Dict[str, int] = {}
        for t in query_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1
        
        q_vec = {}
        total = len(query_tokens)
        for t, count in q_tf.items():
            if t in self.idf:
                q_vec[t] = (count / total) * self.idf[t]

        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        scores = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            doc = self.documents[idx]
            if category_filter and doc.get("category") != category_filter:
                continue

            dot_product = sum(q_vec[t] * doc_vec[t] for t in q_vec if t in doc_vec)
            doc_norm = math.sqrt(sum(v * v for v in doc_vec.values())) or 1.0
            similarity = dot_product / (q_norm * doc_norm)

            # Extra boost if exact keyword or role matches title
            if any(qt in doc["title"].lower() for qt in query_tokens):
                similarity += 0.2

            similarity = max(0.0, min(1.0, similarity))
            features = self.feature_fusion.score(query, doc, similarity, query_metadata)
            decisions = self.decision_fusion.score(
                similarity,
                features["feature_fusion_score"],
                doc.get("source", ""),
            )
            doc_with_scores = {**doc, **features, **decisions}
            scores.append((decisions["final_score"], doc_with_scores))

        scores.sort(key=lambda x: x[0], reverse=True)
        for _, result in scores[:top_k]:
            print(
                "FEATURE-LEVEL FUSION "
                f"TF-IDF score: {result['tfidf_score']:.3f}, "
                f"Lexical score: {result['lexical_score']:.3f}, "
                f"Category score: {result['category_score']:.3f}, "
                f"Skill score: {result['skill_score']:.3f}, "
                f"Difficulty score: {result['difficulty_score']:.3f}, "
                f"Metadata score: {result['metadata_score']:.3f}, "
                f"Feature fusion score: {result['feature_fusion_score']:.3f}"
            )
            print(
                "DECISION-LEVEL FUSION "
                f"TF-IDF decision: {result['tfidf_decision']:.3f}, "
                f"Feature fusion decision: {result['feature_fusion_decision']:.3f}, "
                f"Source reliability: {result['source_reliability']:.3f}, "
                f"Final decision score: {result['final_score']:.3f}"
            )
        return [item[1] for item in scores[:top_k]]

    def get_job_role_context(self, job_role: str, skills: str) -> str:
        """Construct a synthesized RAG context string for question generation or reporting."""
        combined_query = f"{job_role} {skills}"
        results = self.retrieve_relevant_context(
            combined_query,
            top_k=4,
            query_metadata={"category": job_role, "skill": skills},
        )
        
        snippets = []
        for idx, res in enumerate(results, 1):
            snippets.append(f"[{idx}] {res['title']} ({res.get('category', 'general')}):\n{res['content']}")
        
        return "\n\n".join(snippets)

# Global singleton RAG instance
_rag_instance = None

def get_rag_engine(db_session=None) -> RAGEngine:
    global _rag_instance
    if _rag_instance is None:
        import os
        base_dir = os.path.dirname(os.path.dirname(__file__))
        _rag_instance = RAGEngine(base_dir=base_dir)
        _rag_instance.build_index(db_session)
    elif db_session is not None and not _rag_instance._database_indexed:
        _rag_instance.build_index(db_session)
    return _rag_instance

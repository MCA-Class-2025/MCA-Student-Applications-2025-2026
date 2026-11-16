import re

from modules.rag.retriever import Retriever
from modules.rag.fused_retriever import FusedRetriever


class HybridRetriever:

    def __init__(self):
        # Original PDF/document RAG
        self.original_retriever = Retriever(
            model_folder="models"
        )

        # Fused CSV + API RAG
        self.fused_retriever = FusedRetriever(
            vector_folder="models/fused_rag",
            top_k=3
        )

    def contains_ip(self, question):
        pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        return re.search(pattern, question) is not None

    def is_fused_query(self, question):

        question_lower = question.lower()

        api_keywords = [
            "virustotal",
            "abuseipdb",
            "alienvault",
            "otx",
            "shodan",
            "threatfox",
            "threat fox",
            "api intelligence",
            "external threat intelligence",
            "enrichment",
            "enriched ip",
            "ip reputation",
            "abuse confidence",
            "pulse count",
            "malicious detection"
        ]

        # IP-based question
        if self.contains_ip(question):
            return True

        # API/threat-intelligence question
        for keyword in api_keywords:
            if keyword in question_lower:
                return True

        return False

    def retrieve(self, question, top_k=3):

        if self.is_fused_query(question):

            return self.fused_retriever.retrieve(question)

        return self.original_retriever.retrieve(
            question,
            top_k=top_k
        )
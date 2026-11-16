import re
import ipaddress

from modules.rag.embeddings import generate_embeddings
from modules.rag.vector_store import VectorStore


class FusedRetriever:

    def __init__(self, vector_folder="models/fused_rag", top_k=3):
        self.store = VectorStore.load(vector_folder)
        self.top_k = top_k

    def extract_ip(self, question):
        matches = re.findall(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            question
        )

        for candidate in matches:
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                continue

        return None

    def retrieve(self, question):

        # Exact IP match first
        ip = self.extract_ip(question)

        if ip:
            exact_results = []

            for document in self.store.chunks:
                if f"Enrichment Ip: {ip}" in document:
                    exact_results.append(document)

            if exact_results:
                return exact_results[:self.top_k]

        # FAISS semantic search fallback
        query_embedding = generate_embeddings([question])[0]

        return self.store.search(
            query_embedding,
            top_k=self.top_k
        )
from modules.rag.vector_store import VectorStore
from modules.rag.embeddings import generate_embeddings


class Retriever:

    def __init__(self, model_folder="models"):
        self.store = VectorStore.load(model_folder)

    def retrieve(self, query, top_k=3):
        """
        Retrieve the most relevant chunks for a user query.
        """

        query_embedding = generate_embeddings([query])[0]

        results = self.store.search(
            query_embedding,
            top_k=top_k
        )

        return results
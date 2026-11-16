import faiss
import numpy as np
import pickle
import os


class VectorStore:

    def __init__(self, dimension):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunks = []

    def add_embeddings(self, embeddings, chunks):

        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)

        self.chunks.extend(chunks)

    def search(self, query_embedding, top_k=3):

        query_embedding = np.array([query_embedding]).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []

        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])

        return results

    def save(self, folder="models"):

        os.makedirs(folder, exist_ok=True)

        faiss.write_index(
            self.index,
            os.path.join(folder, "faiss_index.bin")
        )

        with open(os.path.join(folder, "chunks.pkl"), "wb") as f:
            pickle.dump(self.chunks, f)

    @classmethod
    def load(cls, folder="models"):

        index = faiss.read_index(
            os.path.join(folder, "faiss_index.bin")
        )

        with open(os.path.join(folder, "chunks.pkl"), "rb") as f:
            chunks = pickle.load(f)

        store = cls(index.d)

        store.index = index

        store.chunks = chunks

        return store
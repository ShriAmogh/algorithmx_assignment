from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient 
from chromadb.utils import embedding_functions
from app.config import EMBED_MODEL_NAME 

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "pdf_chunks"

class Retriever:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)
        self.client = PersistentClient(path=CHROMA_DIR)
        
        self.embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL_NAME
        )
        self.collection = self.client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embed_func
        )

    def search(self, query, top_k=3):
        vec = self.embedder.encode([query])[0].tolist()
        results = self.collection.query(
            query_embeddings=[vec],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )

        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "score": results["distances"][0][i],
                "doc_id": results["metadatas"][0][i].get("doc_id"),
                "doc_name": results["metadatas"][0][i].get("doc_name"),
                "page_num": results["metadatas"][0][i].get("page_num"),
                "chunk_id": results["metadatas"][0][i].get("chunk_id"),
                "text": results["documents"][0][i]
            })
        return hits

    def build_prompt(self, query, hits, max_context_chars=3000):
        context_parts = []
        total = 0
        for h in hits:
            t = h.get("text") or ""
            if total + len(t) > max_context_chars:
                t = t[: max(0, max_context_chars - total)]
            context_parts.append(f"[{h['doc_name']}:p{h['page_num']}] {t}")
            total += len(t)
            if total >= max_context_chars:
                break
        context = "\n\n".join(context_parts)
        prompt = (
    "You are an assistant. Only use the context provided to answer. If the answer cannot be found, say you don't know.\n\n"
    "When you use information from the Context, append a citation to the answer in the format (Source).\n\n"
    f"Context:\n{context}\n\nQuestion: {query}\nAnswer (brief):"
)
        return prompt
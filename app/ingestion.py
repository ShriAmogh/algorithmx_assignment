from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid
from app.config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, EMBED_MODEL_NAME
from app.db import crud

EMBED_DIM = 384 

class Ingestor:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        try:
            self.qdrant.recreate_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
            )
        except Exception:
            pass

    def load_pdf(self, file_bytes):
        reader = PdfReader(file_bytes)
        pages = []
        for i, p in enumerate(reader.pages):
            text = p.extract_text()
            if text and text.strip():
                pages.append({"page_num": i+1, "text": text})
        return pages

    def _chunk_text(self, text, chunk_size=1000, overlap=200):
        chunks = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + chunk_size, n)
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def ingest(self, file_bytes, filename):
        doc = crud.create_document(filename)
        run = crud.create_ingest_run(doc.id)
        total_chunks = 0
        try:
            pages = self.load_pdf(file_bytes)
            for p in pages:
                chunks = self._chunk_text(p["text"])
                if not chunks:
                    continue
                embeddings = self.embedder.encode(chunks)
                points = []
                for idx, emb in enumerate(embeddings):
                    points.append(PointStruct(
                        id=str(uuid.uuid4()),
                        vector=emb.tolist(),
                        payload={
                            "doc_id": str(doc.id),
                            "doc_name": filename,
                            "page_num": p["page_num"],
                            "chunk_id": idx,
                            "text": chunks[idx][:2000]
                        }
                    ))
                self.qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
                total_chunks += len(points)
            crud.mark_document_indexed(doc.id, page_count=len(pages))
            return {"status": "ok", "document_id": doc.id, "chunks": total_chunks}
        except Exception as e:
            crud.mark_document_error(doc.id, str(e))
            crud.fail_ingest_run(run.id, str(e))
            return {"status": "error", "error": str(e)}

# app/ingestion_chroma.py
from sentence_transformers import SentenceTransformer
# CHANGED: Import PersistentClient
from chromadb import PersistentClient
# REMOVED: from chromadb.config import Settings (It's no longer needed) 
from chromadb.utils import embedding_functions
from app.db import crud
from fastapi import UploadFile
from PyPDF2 import PdfReader
import uuid, io

EMBED_DIM = 384
CHROMA_DIR = "chroma_db"  
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "pdf_chunks"


class Ingestor:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBED_MODEL)
        # FIX: Use PersistentClient with the path argument for local persistence
        self.client = PersistentClient(path=CHROMA_DIR)
        
        self.embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )

        try:
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embed_func
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embed_func
            )

    def load_pdf(self, file_stream):
        reader = PdfReader(file_stream)
        pages = []
        for i, p in enumerate(reader.pages):
            text = p.extract_text()
            if text and text.strip():
                pages.append({"page_num": i + 1, "text": text})
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

    def ingest(self, file_stream: io.BytesIO, filename: str):
        doc = crud.create_document(filename)
        run = crud.create_ingest_run(doc.id)
        total_chunks = 0

        try:
            file_stream.seek(0)
            pages = self.load_pdf(file_stream)
            crud.mark_document_indexed(doc.id, page_count=len(pages))

            for p in pages:
                chunks = self._chunk_text(p["text"])
                if not chunks:
                    continue

                # Embed chunks
                embeddings = self.embedder.encode(chunks)

                # Prepare data for Chroma
                ids = [str(uuid.uuid4()) for _ in chunks]
                metadatas = [{
                    "doc_id": str(doc.id),
                    "doc_name": filename,
                    "page_num": p["page_num"],
                    "chunk_id": idx,
                    "text": chunks[idx][:2000]
                } for idx in range(len(chunks))]

                # Upsert into Chroma
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    metadatas=metadatas,
                    documents=chunks
                )

                total_chunks += len(chunks)

            crud.finish_ingest_run(run.id, total_chunks)
            return {"status": "ok", "document_id": doc.id, "chunks": total_chunks}

        except Exception as e:
            crud.mark_document_error(doc.id, str(e))
            crud.fail_ingest_run(run.id, str(e))
            return {"status": "error", "error": str(e)}
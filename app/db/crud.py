import sqlalchemy as sa
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from .models import Base, Document, IngestionRun, Session, Message, Telemetry

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def create_document(filename: str) -> Document:
    with SessionLocal() as db:
        doc = Document(filename=filename, status="uploading")
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

def mark_document_indexed(doc_id: str, page_count: int):
    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        if doc:
            doc.status = "indexed"
            doc.page_count = page_count
            db.commit()

def mark_document_error(doc_id: str, error: str):
    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        if doc:
            doc.status = "error"
            doc.error = error
            db.commit()

def create_ingest_run(document_id: str) -> IngestionRun:
    with SessionLocal() as db:
        run = IngestionRun(document_id=document_id)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

def finish_ingest_run(run_id: str, total_chunks: int):
    with SessionLocal() as db:
        run = db.get(IngestionRun, run_id)
        if run:
            run.finished_at = func.now()
            run.total_chunks = total_chunks
            db.commit()

def fail_ingest_run(run_id: str, error: str):
    with SessionLocal() as db:
        run = db.get(IngestionRun, run_id)
        if run:
            run.finished_at = func.now()
            run.error = error
            db.commit()

def create_session(name: str = None, user_id: str = None) -> Session:
    with SessionLocal() as db:
        s = Session(name=name, user_id=user_id)
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

def create_message(session_id: str, role: str, content: str, meta: dict = None) -> Message:
    with SessionLocal() as db:
        m = Message(session_id=session_id, role=role, content=content, meta_data=meta or {})
        db.add(m)
        db.commit()
        db.refresh(m)
        return m

def create_telemetry(session_id: str, message_id: str, query: str, retrieved_ids: list,
                     retrieval_time_ms: float, llm_time_ms: float, top_k: int, extra: dict = None) -> Telemetry:
    with SessionLocal() as db:
        t = Telemetry(
            session_id=session_id,
            message_id=message_id,
            query=query,
            retrieved_ids=retrieved_ids,
            retrieval_time_ms=retrieval_time_ms,
            llm_time_ms=llm_time_ms,
            top_k=top_k,
            extra=extra or {}
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return t

def list_documents():
    with SessionLocal() as db:
        return db.query(Document).order_by(Document.uploaded_at.desc()).all()

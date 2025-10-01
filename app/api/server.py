from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.ingestion import Ingestor
from app.retriever import Retriever
from app.llm.gemini_client import GeminiClient
from app.db import crud
import time

crud.init_db()

ingestor = Ingestor()
retriever = Retriever()
gemini = GeminiClient()

app = FastAPI(title="RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    #content = await file.read()
    res = ingestor.ingest(file.file, file.filename)
    return res

@app.get("/documents")
def list_documents():
    docs = crud.list_documents()
    return [{"id": d.id, "filename": d.filename, "status": d.status, "page_count": d.page_count} for d in docs]

@app.post("/query")
def query(session_id: str = Form(None), query: str = Form(...), top_k: int = Form(3)):
    if session_id is None:
        session = crud.create_session(name=f"session-{int(time.time())}")
    else:
        session = crud.create_session(name=session_id)  

    user_msg = crud.create_message(session.id, "user", query)
    # retrieve
    t0 = time.time()
    hits = retriever.search(query, top_k=top_k)
    retrieval_time_ms = int((time.time() - t0) * 1000)
    # optional guard
    if not hits:
        answer = "I couldn't find relevant information in the uploaded documents."
        crud.create_message(session.id, "assistant", answer, meta_data={"sources": []})
        return {"answer": answer, "sources": []}
    # build prompt and call gemini
    prompt = retriever.build_prompt(query, hits)
    llm_resp = gemini.generate(prompt)
    answer = llm_resp["text"]
    assistant_msg = crud.create_message(session.id, "assistant", answer, meta={"sources": hits})  # <-- fixed
    crud.create_telemetry(session.id, assistant_msg.id, query, [h.get("chunk_id") for h in hits], retrieval_time_ms, llm_resp["llm_time_ms"], top_k)
    return {"answer": answer, "sources": hits}

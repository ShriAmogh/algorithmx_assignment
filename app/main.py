import streamlit as st
import requests
from config import API_BASE
from io import BytesIO

st.set_page_config(layout="wide", page_title="PDF RAG")
st.title("PDF RAG")

with st.sidebar:
    st.header("Upload PDFs")
    uploaded = st.file_uploader("Upload one or more PDFs", type="pdf", accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            with st.spinner(f"Uploading {f.name}..."):
                files = {"file": (f.name, f.read(), "application/pdf")}
                resp = requests.post(f"{API_BASE}/upload_pdf", files=files)
                st.write(resp.json())
    st.markdown("---")
    st.header("Settings")
    top_k = st.number_input("top_k", min_value=1, max_value=10, value=3)
    only_with_sources = st.checkbox("Only answer if sources found", value=True)
    st.session_state.setdefault("top_k", top_k)
    st.session_state.setdefault("only_with_sources", only_with_sources)

# Files panel
cols = st.columns([1, 3])
with cols[0]:
    st.subheader("Indexed Files")
    try:
        docs = requests.get(f"{API_BASE}/documents").json()
        for d in docs:
            st.write(f"- {d['filename']} ({d['status']})")
    except Exception:
        st.write("No documents (API may be down).")

# Chat area
with cols[1]:
    st.subheader("Chat")
    if "history" not in st.session_state:
        st.session_state.history = []

    query = st.text_input("Ask something about your PDFs:")
    if st.button("Send"):
        if not query:
            st.warning("Type a question.")
        else:
            payload = {"session_id": None, "query": query, "top_k": st.session_state.top_k}
            resp = requests.post(f"{API_BASE}/query", data=payload).json()
            st.session_state.history.append({"role": "user", "text": query})
            st.session_state.history.append({"role": "assistant", "text": resp["answer"], "sources": resp["sources"]})

    for msg in st.session_state.history[::-1]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['text']}")
        else:
            st.markdown(f"**Assistant:** {msg['text']}")
            with st.expander("Show Context / Sources"):
                for s in msg.get("sources", []):
                    st.markdown(f"- **{s['doc_name']} (page {s['page_num']})** — {s['text'][:400]}...")
    if st.button("Clear Chat"):
        st.session_state.history = []

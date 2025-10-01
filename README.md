# algorithmx_assignment

PDF Retrieval-Augmented Generation (RAG) API

A FastAPI-based RAG system that allows you to upload PDFs, index them into embeddings using SentenceTransformers, store them in Chroma, and query the documents using semantic search. The system also logs sessions, messages, and telemetry in PostgreSQL.

Features

Upload and index PDF documents

Chunk and embed text using all-MiniLM-L6-v2

Store embeddings persistently in Chroma

Retrieve relevant chunks for a query using semantic search

Generate answers using Gemini LLM

Track sessions, messages, and retrieval telemetry in PostgreSQL

Full FastAPI endpoints for programmatic access

Cross-Origin support with CORS middleware

Tech Stack

Backend: Python, FastAPI

Vector Database: Chroma (DuckDB + Parquet)

Embeddings: SentenceTransformers (all-MiniLM-L6-v2)

LLM: Gemini API

Relational DB: PostgreSQL

PDF Parsing: PyPDF2

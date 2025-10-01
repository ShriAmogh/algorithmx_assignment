import uuid

def gen_uuid():
    return str(uuid.uuid4())

from sqlalchemy import (
    Column, String, Integer, Text, TIMESTAMP, JSON, Enum, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import sqlalchemy as sa

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    filename = Column(Text, nullable=False)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=sa.text("now()"))
    page_count = Column(Integer)
    status = Column(Text, default="indexed")
    error = Column(Text) 

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    started_at = Column(TIMESTAMP(timezone=True), server_default=sa.text("now()"))
    finished_at = Column(TIMESTAMP(timezone=True))
    total_chunks = Column(Integer)
    error = Column(Text)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.text("now()"))
    name = Column(Text)

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    role = Column(Enum("user", "assistant", name="role_enum"), nullable=False)
    content = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.text("now()"))
    meta_data = Column(JSON)

class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    query = Column(Text)
    retrieved_ids = Column(JSON)
    retrieval_time_ms = Column(Integer)
    llm_time_ms = Column(Integer)
    top_k = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.text("now()"))
    extra = Column(JSON)

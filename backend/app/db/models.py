"""SQLAlchemy ORM models. See docs/DB_SCHEMA.md for the full schema rationale.

Two halves: the read-only knowledge corpus (documents/issues/slack/commits) and the
reasoning runtime (questions/answers/evidence/human answers/learning events).
"""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, created_at_column

_DIM = get_settings().embedding_dim


# --- Knowledge corpus -----------------------------------------------------------------


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_type: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    service: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(_DIM))

    document: Mapped[Document] = relationship(back_populates="chunks")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(Text, nullable=True)
    labels: Mapped[list[str]] = mapped_column(JSONB, default=list)
    service: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = created_at_column()


class SlackMessage(Base):
    __tablename__ = "slack_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = created_at_column()
    is_root: Mapped[bool] = mapped_column(default=False)


class Commit(Base):
    __tablename__ = "commits"

    id: Mapped[int] = mapped_column(primary_key=True)
    sha: Mapped[str] = mapped_column(Text, unique=True)
    message: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    service: Mapped[str | None] = mapped_column(Text, nullable=True)
    files: Mapped[list[str]] = mapped_column(JSONB, default=list)
    committed_at: Mapped[datetime] = created_at_column()


# --- Reasoning runtime ----------------------------------------------------------------


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    asker: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="new")
    created_at: Mapped[datetime] = created_at_column()

    ai_answers: Mapped[list["AIAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    human_answers: Mapped[list["HumanAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class AIAnswer(Base):
    __tablename__ = "ai_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    answer_text: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning_trace: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    model_info: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = created_at_column()

    question: Mapped[Question] = relationship(back_populates="ai_answers")
    evidence: Mapped[list["AnswerEvidence"]] = relationship(
        back_populates="ai_answer", cascade="all, delete-orphan"
    )


class AnswerEvidence(Base):
    __tablename__ = "answer_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    ai_answer_id: Mapped[int] = mapped_column(ForeignKey("ai_answers.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    snippet: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    ai_answer: Mapped[AIAnswer] = relationship(back_populates="evidence")


class HumanAnswer(Base):
    __tablename__ = "human_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    answer_text: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    expert_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at_column()

    question: Mapped[Question] = relationship(back_populates="human_answers")


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    ai_answer_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_answers.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(Text)
    missed_sources: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    missed_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(_DIM))
    created_at: Mapped[datetime] = created_at_column()

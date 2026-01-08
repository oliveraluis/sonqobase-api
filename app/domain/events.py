"""
Domain Events para SonqoBase.
Eventos inmutables que representan hechos que ocurrieron en el sistema.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from abc import ABC


# Base abstracta sin campos (solo para type checking)
class DomainEvent(ABC):
    """Base class para todos los eventos de dominio"""
    pass


# Eventos de Proyectos
@dataclass(frozen=True)
class ProjectCreatedEvent(DomainEvent):
    """Evento cuando se crea un proyecto"""
    user_id: str
    project_id: str
    project_slug: str
    project_name: str
    plan_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Eventos de Documentos (CRUD)
@dataclass(frozen=True)
class DocumentReadEvent(DomainEvent):
    """Evento cuando se leen documentos de una colección"""
    user_id: str
    project_id: str
    collection: str
    document_count: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DocumentWrittenEvent(DomainEvent):
    """Evento cuando se escribe/actualiza un documento"""
    user_id: str
    project_id: str
    collection: str
    document_id: str
    operation: str  # "insert" | "update" | "delete"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Eventos de RAG
@dataclass(frozen=True)
class RagIngestStartedEvent(DomainEvent):
    """Evento cuando inicia la ingesta de texto/PDF para RAG"""
    user_id: str
    project_id: str
    collection: str
    source_type: str  # "text" | "pdf"
    source_size_bytes: int
    job_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class RagIngestCompletedEvent(DomainEvent):
    """Evento cuando completa la ingesta para RAG"""
    user_id: str
    project_id: str
    collection: str
    job_id: str
    chunks_inserted: int
    embeddings_generated: int
    processing_time_ms: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class RagQueryExecutedEvent(DomainEvent):
    """Evento cuando se ejecuta una query RAG"""
    user_id: str
    project_id: str
    collection: str
    query: str
    results_count: int
    response_time_ms: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Eventos de PDF - Pipeline Asíncrono
@dataclass(frozen=True)
class PdfIngestStartedEvent(DomainEvent):
    """Evento cuando inicia el procesamiento de un PDF (antes de guardar en GridFS)"""
    user_id: str
    project_id: str
    collection: str
    pdf_size_bytes: int
    pdf_filename: str
    job_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PdfSavedToGridFSEvent(DomainEvent):
    """Evento cuando el PDF se guardó exitosamente en GridFS y está listo para procesarse"""
    user_id: str
    project_id: str
    collection: str
    pdf_size_bytes: int
    pdf_filename: str
    job_id: str
    content_hash: str  # Hash del PDF guardado
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PdfPageExtractedEvent(DomainEvent):
    """Evento cuando se extrae UNA página (streaming incremental)"""
    job_id: str
    user_id: str
    project_id: str
    collection: str
    page_number: int
    total_pages: int
    page_text: str
    page_metadata: Dict
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PdfTextExtractedEvent(DomainEvent):
    """Evento cuando se extrae el texto completo (legacy)"""
    job_id: str
    user_id: str
    project_id: str
    collection: str
    text: str
    pdf_metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PdfChunkedEvent(DomainEvent):
    """Evento cuando se divide el texto en chunks"""
    job_id: str
    user_id: str
    project_id: str
    collection: str
    chunks: List[str]
    chunk_metadata: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class EmbeddingsGeneratedEvent(DomainEvent):
    """Evento cuando se generan embeddings"""
    job_id: str
    user_id: str
    project_id: str
    collection: str
    embeddings: List[List[float]]
    chunks: List[str]
    metadata: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PdfIngestCompletedEvent(DomainEvent):
    """Evento cuando completa el procesamiento de un PDF"""
    user_id: str
    project_id: str
    collection: str
    job_id: str
    pages_processed: int
    chunks_created: int
    processing_time_ms: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PdfIngestFailedEvent(DomainEvent):
    """Evento cuando falla el procesamiento de un PDF"""
    user_id: str
    project_id: str
    collection: str
    job_id: str
    stage: str  # "extraction" | "chunking" | "embedding" | "storage"
    error_message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Eventos de Límites
@dataclass(frozen=True)
class UsageLimitExceededEvent(DomainEvent):
    """Evento cuando un usuario excede un límite de su plan"""
    user_id: str
    limit_type: str  # "reads" | "writes" | "rag_queries" | "projects"
    current_usage: int
    limit: int
    plan_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class UsageLimitWarningEvent(DomainEvent):
    """Evento cuando un usuario se acerca a un límite (80%)"""
    user_id: str
    limit_type: str
    current_usage: int
    limit: int
    percentage: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Eventos de Autenticación
@dataclass(frozen=True)
class OtpCreatedEvent(DomainEvent):
    """Event when OTP is generated (in-memory) and ready to be processed"""
    otp_id: str
    user_id: str
    email: str
    otp_code: str
    otp_type: str = "login"
    user_name: Optional[str] = None
    should_send_email: bool = True
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

# Deprecated: OtpRequestedEvent (Replaced by OtpCreatedEvent for full event driven flow)

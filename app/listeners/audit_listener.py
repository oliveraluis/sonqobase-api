"""
Listener de auditoría para tracking de operaciones.
Escucha eventos de dominio y registra en audit_logs.
"""
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional

from app.infra.event_bus import get_event_bus
from app.domain.events import (
    DocumentReadEvent,
    DocumentWrittenEvent,
    RagQueryExecutedEvent,
    RagIngestCompletedEvent,
)

logger = logging.getLogger(__name__)

# Obtener event bus global
event_bus = get_event_bus()


@dataclass
class AuditEvent:
    """Evento de auditoría para persistir en MongoDB"""
    user_id: str
    project_id: str
    operation: Literal["read", "write", "rag_query", "rag_ingest"]
    collection: Optional[str] = None
    document_count: int = 1
    metadata: Optional[dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


# Cola en memoria para batch processing
_audit_queue: deque[AuditEvent] = deque(maxlen=10000)


def track_operation(event: AuditEvent):
    """
    Fire-and-forget: agregar evento a cola de auditoría.
    Overhead < 0.001ms
    """
    _audit_queue.append(event)


# Listeners de eventos de dominio
@event_bus.subscribe(DocumentReadEvent)
async def on_document_read(event: DocumentReadEvent):
    """Registrar lectura de documentos"""
    track_operation(AuditEvent(
        user_id=event.user_id,
        project_id=event.project_id,
        operation="read",
        collection=event.collection,
        document_count=event.document_count,
        timestamp=event.timestamp,
    ))
    logger.debug(f"📖 Audit: Read {event.document_count} docs from {event.collection}")


@event_bus.subscribe(DocumentWrittenEvent)
async def on_document_written(event: DocumentWrittenEvent):
    """Registrar escritura de documento"""
    track_operation(AuditEvent(
        user_id=event.user_id,
        project_id=event.project_id,
        operation="write",
        collection=event.collection,
        document_count=1,
        metadata={"operation": event.operation, "document_id": event.document_id},
        timestamp=event.timestamp,
    ))
    logger.debug(f"✍️  Audit: {event.operation.upper()} doc in {event.collection}")


@event_bus.subscribe(RagQueryExecutedEvent)
async def on_rag_query(event: RagQueryExecutedEvent):
    """Registrar consulta RAG"""
    track_operation(AuditEvent(
        user_id=event.user_id,
        project_id=event.project_id,
        operation="rag_query",
        collection=event.collection,
        metadata={
            "query": event.query[:100],  # Truncar query larga
            "results_count": event.results_count,
            "response_time_ms": event.response_time_ms,
        },
        timestamp=event.timestamp,
    ))
    logger.debug(f"🔍 Audit: RAG query in {event.collection}")


@event_bus.subscribe(RagIngestCompletedEvent)
async def on_rag_ingest_completed(event: RagIngestCompletedEvent):
    """Registrar ingesta RAG completada"""
    track_operation(AuditEvent(
        user_id=event.user_id,
        project_id=event.project_id,
        operation="rag_ingest",
        collection=event.collection,
        document_count=event.chunks_inserted,
        metadata={
            "job_id": event.job_id,
            "embeddings_generated": event.embeddings_generated,
            "processing_time_ms": event.processing_time_ms,
        },
        timestamp=event.timestamp,
    ))
    logger.debug(f"📥 Audit: RAG ingest completed in {event.collection}")


# TODO: Implementar background worker para procesar _audit_queue
# async def audit_worker():
#     """Worker que procesa eventos de auditoría cada 5 segundos"""
#     while True:
#         await asyncio.sleep(5)
#         await process_audit_batch()
#
# async def process_audit_batch():
#     """Procesar batch de eventos y persistir en MongoDB"""
#     if not _audit_queue:
#         return
#     
#     batch = []
#     while _audit_queue and len(batch) < 1000:
#         batch.append(_audit_queue.popleft())
#     
#     # Insertar en MongoDB (bulk)
#     # Actualizar contadores de uso

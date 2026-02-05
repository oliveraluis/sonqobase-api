"""
Listener para generación de embeddings.
Escucha PdfChunkedEvent y genera embeddings para cada chunk.
"""
import logging

from app.infra.event_bus import get_event_bus
from app.domain.events import PdfChunkedEvent, TextChunkedEvent
from app.services.embedding_generation import EmbeddingGenerationService
from app.infra.gemini_embeddings import GeminiEmbeddingProvider
from app.infra.job_repository import JobRepository
from app.config import settings

logger = logging.getLogger(__name__)

# Obtener event bus global
event_bus = get_event_bus()


@event_bus.subscribe(PdfChunkedEvent)
async def on_pdf_chunked(event: PdfChunkedEvent):
    """
    Listener que genera embeddings para los chunks de PDF.
    
    Pipeline: PdfChunkedEvent → Generar embeddings → EmbeddingsGeneratedEvent
    """
    # Crear servicio con dependencias
    service = EmbeddingGenerationService(
        embedding_provider=GeminiEmbeddingProvider(settings.gemini_api_key),
        job_repo=JobRepository(),
    )
    
    # Delegar toda la lógica al servicio
    await service.execute(
        job_id=event.job_id,
        user_id=event.user_id,
        project_id=event.project_id,
        collection=event.collection,
        chunks=event.chunks,
        chunk_metadata=event.chunk_metadata,
    )


@event_bus.subscribe(TextChunkedEvent)
async def on_text_chunked(event: TextChunkedEvent):
    """
    Listener que genera embeddings para los chunks de texto.
    
    Pipeline: TextChunkedEvent → Generar embeddings → EmbeddingsGeneratedEvent
    """
    # Crear servicio con dependencias
    service = EmbeddingGenerationService(
        embedding_provider=GeminiEmbeddingProvider(settings.gemini_api_key),
        job_repo=JobRepository(),
    )
    
    # Delegar toda la lógica al servicio
    await service.execute(
        job_id=event.job_id,
        user_id=event.user_id,
        project_id=event.project_id,
        collection=event.collection,
        chunks=event.chunks,
        chunk_metadata=event.chunk_metadata,
    )


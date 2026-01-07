"""
Listener para almacenamiento de vectores en MongoDB.
Escucha EmbeddingsGeneratedEvent e inserta en la colección vectorial.
"""
import logging
from pymongo import MongoClient

from app.infra.event_bus import get_event_bus
from app.domain.events import EmbeddingsGeneratedEvent
from app.services.vector_storage import VectorStorageService
from app.infra.job_repository import JobRepository
from app.infra.pdf_storage import PdfStorage
from app.config import settings

logger = logging.getLogger(__name__)

# Obtener event bus global
event_bus = get_event_bus()


@event_bus.subscribe(EmbeddingsGeneratedEvent)
async def on_embeddings_generated(event: EmbeddingsGeneratedEvent):
    """
    Listener que almacena embeddings en la colección vectorial.
    
    Pipeline: EmbeddingsGeneratedEvent → Insertar en MongoDB → PdfIngestCompletedEvent
    """
    # Inicializar dependencias
    client = MongoClient(settings.mongo_uri)
    meta_db = client[settings.mongo_meta_db]
    
    # Crear servicio con dependencias
    service = VectorStorageService(
        job_repo=JobRepository(),
        pdf_storage=PdfStorage(meta_db),
    )
    
    # Delegar toda la lógica al servicio
    await service.execute(
        job_id=event.job_id,
        user_id=event.user_id,
        project_id=event.project_id,
        collection=event.collection,
        chunks=event.chunks,
        embeddings=event.embeddings,
        metadata=event.metadata,
    )

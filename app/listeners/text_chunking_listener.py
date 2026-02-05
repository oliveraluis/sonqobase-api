"""
Listener para chunking de texto plano.
Escucha TextIngestStartedEvent y divide el texto en chunks.
"""
import logging

from app.infra.event_bus import get_event_bus
from app.domain.events import TextIngestStartedEvent
from app.services.text_chunking import TextChunkingService
from app.infra.job_repository import JobRepository

logger = logging.getLogger(__name__)

# Event bus
event_bus = get_event_bus()


@event_bus.subscribe(TextIngestStartedEvent)
async def on_text_ingest_started(event: TextIngestStartedEvent):
    """
    Listener que procesa texto y lo divide en chunks.
    
    Pipeline: TextIngestStartedEvent → Chunking → TextChunkedEvent
    """
    logger.info(f"📝 Text ingest started event received: job_id={event.job_id}")
    
    # Obtener el texto del job
    job_repo = JobRepository()
    job = job_repo.get(event.job_id)
    
    if not job:
        logger.error(f"❌ Job not found: job_id={event.job_id}")
        return
    
    # El texto está almacenado en metadata del job
    text = job.get('metadata', {}).get('text', '')
    
    if not text:
        logger.error(f"❌ No text found in job metadata: job_id={event.job_id}")
        job_repo.update_status(event.job_id, "failed", error="No text found in job")
        return
    
    # Crear servicio con dependencias
    service = TextChunkingService(
        job_repo=job_repo,
    )
    
    # Delegar toda la lógica al servicio
    await service.execute(
        job_id=event.job_id,
        user_id=event.user_id,
        project_id=event.project_id,
        collection=event.collection,
        text=text,
        chunk_size=event.chunk_size,
    )

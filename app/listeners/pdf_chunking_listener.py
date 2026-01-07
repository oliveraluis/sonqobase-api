"""
Listener para chunking de páginas (procesamiento incremental).
Escucha PdfPageExtractedEvent y divide SOLO esa página en chunks.
"""
import logging

from app.infra.event_bus import get_event_bus
from app.domain.events import PdfPageExtractedEvent
from app.services.pdf_chunking import PdfChunkingService
from app.infra.pdf_processor import PdfProcessor
from app.infra.job_repository import JobRepository

logger = logging.getLogger(__name__)

# Event bus
event_bus = get_event_bus()


@event_bus.subscribe(PdfPageExtractedEvent)
async def on_pdf_page_extracted(event: PdfPageExtractedEvent):
    """
    Listener que procesa UNA página a la vez.
    
    Divide el texto de la página en chunks y publica evento.
    Memoria: Solo chunks de UNA página en RAM.
    
    Pipeline: PdfPageExtractedEvent → Chunking → PdfChunkedEvent
    """
    # Crear servicio con dependencias
    service = PdfChunkingService(
        pdf_processor=PdfProcessor(),
        job_repo=JobRepository(),
    )
    
    # Delegar toda la lógica al servicio
    await service.execute(
        job_id=event.job_id,
        user_id=event.user_id,
        project_id=event.project_id,
        collection=event.collection,
        page_number=event.page_number,
        total_pages=event.total_pages,
        page_text=event.page_text,
    )

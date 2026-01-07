"""
Listener con streaming real usando PyMuPDF.
Procesa página por página sin cargar PDF completo en memoria.
"""
import logging
from pymongo import MongoClient

from app.infra.event_bus import get_event_bus
from app.domain.events import PdfSavedToGridFSEvent
from app.services.pdf_text_extraction import PdfTextExtractionService
from app.infra.pdf_storage import PdfStorage
from app.infra.pdf_processor import PdfProcessor
from app.infra.job_repository import JobRepository
from app.config import settings

logger = logging.getLogger(__name__)

# Event bus
event_bus = get_event_bus()


@event_bus.subscribe(PdfSavedToGridFSEvent)
async def on_pdf_saved_to_gridfs(event: PdfSavedToGridFSEvent):
    """
    Listener con streaming real usando PyMuPDF.
    
    Procesa página por página directamente desde GridFS.
    Memoria: Solo 1 página en RAM a la vez.
    """
    # Inicializar dependencias
    client = MongoClient(settings.mongo_uri)
    meta_db = client[settings.mongo_meta_db]
    
    # Crear servicio con dependencias
    service = PdfTextExtractionService(
        pdf_storage=PdfStorage(meta_db),
        pdf_processor=PdfProcessor(),
        job_repo=JobRepository(),
    )
    
    # Delegar toda la lógica al servicio
    await service.execute(
        job_id=event.job_id,
        user_id=event.user_id,
        project_id=event.project_id,
        collection=event.collection,
    )

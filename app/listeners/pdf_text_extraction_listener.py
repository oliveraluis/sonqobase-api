"""
Listener con streaming real usando PyMuPDF.
Procesa página por página sin cargar PDF completo en memoria.
"""
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.infra.event_bus import get_event_bus
from app.domain.events import PdfSavedToGridFSEvent, PdfPageExtractedEvent, PdfIngestFailedEvent
from app.infra.pdf_storage import PdfStorage
from app.infra.pdf_processor import PdfProcessor
from app.infra.job_repository import JobRepository
from app.infra.pdf_concurrency_limiter import get_concurrency_limiter
from app.config import settings
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Event bus
event_bus = get_event_bus()

# Dependencias
client = MongoClient(settings.mongo_uri)
meta_db = client[settings.mongo_meta_db]
pdf_storage = PdfStorage(meta_db)
pdf_processor = PdfProcessor()
job_repo = JobRepository(meta_db)
concurrency_limiter = get_concurrency_limiter()


@event_bus.subscribe(PdfSavedToGridFSEvent)
async def on_pdf_saved_to_gridfs(event: PdfSavedToGridFSEvent):
    """
    Listener con streaming real usando PyMuPDF.
    
    Procesa página por página directamente desde GridFS.
    Memoria: Solo 1 página en RAM a la vez.
    """
    job_id = event.job_id
    
    # Obtener plan
    job = job_repo.get(job_id)
    if not job:
        logger.error(f"❌ Job not found: {job_id}")
        return
    
    plan_name = job.get('metadata', {}).get('plan_name', 'Free')
    
    try:
        logger.info(f"📄 Starting streaming extraction: job_id={job_id}")
        
        # Rate limiting
        try:
            await concurrency_limiter.acquire(plan_name, job_id)
        except ValueError as e:
            logger.error(f"❌ Concurrency limit: {e}")
            job_repo.update_status(job_id, "failed", error=str(e))
            return
        
        # Obtener archivo de GridFS
        logger.info(f"📥 Accessing PDF in GridFS: job_id={job_id}")
        pdf_file = pdf_storage.fs.find_one({"metadata.job_id": job_id})
        
        if not pdf_file:
            raise RuntimeError(f"PDF not found despite PdfSavedToGridFSEvent for job {job_id}")
        
        # Actualizar progreso inicial
        job_repo.update_status(job_id, "extracting_text", progress=10)
        
        # Streaming real con PyMuPDF
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        # Crear generador (PyMuPDF procesa página por página)
        page_generator = pdf_processor.extract_pages_streaming(pdf_file)
        
        page_number = 0
        total_pages = None
        
        logger.info(f"📄 Starting page-by-page streaming...")
        
        # Procesar cada página
        while True:
            # Wrapper para manejar StopIteration correctamente
            def get_next_page():
                try:
                    return next(page_generator)
                except StopIteration:
                    return None  # Sentinel value
            
            # Extraer siguiente página en thread pool
            page_data = await loop.run_in_executor(executor, get_next_page)
            
            # Si es None, terminamos
            if page_data is None:
                break
            
            page_number = page_data["page_number"]
            total_pages = page_data["total_pages"]
            text_length = len(page_data["text"])
            
            logger.info(f"📄 Page {page_number}/{total_pages}: {text_length} chars extracted")
            
            # Publicar evento de página
            await event_bus.publish(
                PdfPageExtractedEvent(
                    job_id=job_id,
                    user_id=event.user_id,
                    project_id=event.project_id,
                    collection=event.collection,
                    page_number=page_number,
                    total_pages=total_pages,
                    page_text=page_data["text"],
                    page_metadata=page_data["metadata"],
                )
            )
            
            # Incrementar progreso (10% a 40% = 30% total / total_pages)
            progress_per_page = int(30 / total_pages) if total_pages > 0 else 1
            job_repo.increment_progress(
                job_id,
                delta=progress_per_page,
                status="extracting_text",
                result={
                    "pages_processed": page_number,
                    "total_pages": total_pages
                }
            )
            
            logger.info(f"✅ Page {page_number}/{total_pages} streamed")
        
        logger.info(f"🎉 All {total_pages} pages processed with streaming")
        
    except Exception as e:
        logger.error(f"❌ Streaming failed: {job_id}, error={e}", exc_info=True)
        job_repo.update_status(job_id, "failed", error=str(e))
        
        await event_bus.publish(PdfIngestFailedEvent(
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            job_id=job_id,
            stage="extraction",
            error_message=str(e),
        ))
    
    finally:
        concurrency_limiter.release(plan_name, job_id)

"""
Listener para chunking de páginas (procesamiento incremental).
Escucha PdfPageExtractedEvent y divide SOLO esa página en chunks.
"""
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.infra.event_bus import get_event_bus
from app.domain.events import PdfPageExtractedEvent, PdfChunkedEvent, PdfIngestFailedEvent
from app.infra.pdf_processor import PdfProcessor
from app.infra.job_repository import JobRepository
from app.config import settings
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Event bus
event_bus = get_event_bus()

# Dependencias
client = MongoClient(settings.mongo_uri)
meta_db = client[settings.mongo_meta_db]
pdf_processor = PdfProcessor()
job_repo = JobRepository(meta_db)


@event_bus.subscribe(PdfPageExtractedEvent)
async def on_pdf_page_extracted(event: PdfPageExtractedEvent):
    """
    Listener que procesa UNA página a la vez.
    
    Divide el texto de la página en chunks y publica evento.
    Memoria: Solo chunks de UNA página en RAM.
    
    Pipeline: PdfPageExtractedEvent → Chunking → PdfChunkedEvent
    """
    job_id = event.job_id
    page_num = event.page_number
    
    try:
        logger.info(f"📦 Starting chunking: job_id={job_id}, page={page_num}/{event.total_pages}")
        
        # Diagnosticar texto vacío
        text_length = len(event.page_text) if event.page_text else 0
        logger.info(f"📝 Page {page_num} text length: {text_length} characters")
        
        # Mostrar primeros 100 caracteres para debug
        if text_length > 0:
            preview = event.page_text[:100].replace('\n', ' ')
            logger.info(f"📄 Text preview: {preview}...")
        
        if text_length == 0:
            logger.warning(f"⚠️  Page {page_num} has no text, skipping chunking")
            return  # No publicar evento si no hay texto
        
        # Obtener chunk_size del job
        job = job_repo.get(job_id)
        chunk_size = job.get('metadata', {}).get('chunk_size', 500)
        
        # Chunk SOLO esta página (thread pool)
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()
        
        chunks = await loop.run_in_executor(
            executor,
            pdf_processor.chunk_text,
            event.page_text,
            chunk_size
        )
        
        logger.info(f"✅ Page chunked: page={page_num}, chunks={len(chunks)}")
        
        # Validar que hay chunks
        if not chunks:
            logger.warning(f"⚠️  No chunks created for page {page_num}, skipping")
            return
        
        # Crear metadata para cada chunk
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                "chunk_index": i,
                "chunk_size": len(chunk),
                "page_number": page_num,
                "total_pages": event.total_pages,
                "pdf_filename": job.get('metadata', {}).get('filename'),
                **job.get('metadata', {}).get('user_metadata', {})
            })
        
        # Publicar evento de chunks (de esta página)
        await event_bus.publish(PdfChunkedEvent(
            job_id=job_id,
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            chunks=chunks,
            chunk_metadata=chunk_metadata,
        ))
        
        # Actualizar progreso (40% a 60% = 20% total / total_pages)
        progress_per_page = int(20 / event.total_pages) if event.total_pages > 0 else 1
        job_repo.increment_progress(
            job_id,
            delta=progress_per_page,
            status="chunking",
            result={
                "pages_processed": page_num,
                "total_pages": event.total_pages,
                "chunks_created": len(chunks)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Chunking failed: job_id={job_id}, page={page_num}, error={e}", exc_info=True)
        job_repo.update_status(job_id, "failed", error=f"Chunking failed: {str(e)}")
        
        await event_bus.publish(PdfIngestFailedEvent(
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            job_id=job_id,
            stage="chunking",
            error_message=str(e),
        ))

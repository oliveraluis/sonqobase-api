"""
Servicio para chunking de texto de PDFs.
"""
import logging
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from app.infra.pdf_processor import PdfProcessor
from app.infra.job_repository import JobRepository
from app.infra.event_bus import get_event_bus
from app.domain.events import PdfChunkedEvent, PdfIngestFailedEvent

logger = logging.getLogger(__name__)


class PdfChunkingService:
    """Servicio para dividir texto de páginas en chunks"""
    
    def __init__(
        self,
        pdf_processor: PdfProcessor,
        job_repo: JobRepository,
    ):
        self.pdf_processor = pdf_processor
        self.job_repo = job_repo
        self.event_bus = get_event_bus()
    
    async def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        collection: str,
        page_number: int,
        total_pages: int,
        page_text: str,
    ) -> None:
        """
        Dividir texto de una página en chunks.
        
        Args:
            job_id: ID del job
            user_id: ID del usuario
            project_id: ID del proyecto
            collection: Nombre de la colección
            page_number: Número de página
            total_pages: Total de páginas
            page_text: Texto de la página
        
        Raises:
            Exception: Si falla el chunking
        """
        try:
            logger.info(f"📦 Starting chunking: job_id={job_id}, page={page_number}/{total_pages}")
            
            # Diagnosticar texto vacío
            text_length = len(page_text) if page_text else 0
            logger.info(f"📝 Page {page_number} text length: {text_length} characters")
            
            # Mostrar primeros 100 caracteres para debug
            if text_length > 0:
                preview = page_text[:100].replace('\n', ' ')
                logger.info(f"📄 Text preview: {preview}...")
            
            if text_length == 0:
                logger.warning(f"⚠️  Page {page_number} has no text, skipping chunking")
                return  # No publicar evento si no hay texto
            
            # Obtener chunk_size del job
            job = self.job_repo.get(job_id)
            chunk_size = job.get('metadata', {}).get('chunk_size', 500)
            
            # Chunk SOLO esta página (thread pool)
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor()
            
            chunks = await loop.run_in_executor(
                executor,
                self.pdf_processor.chunk_text,
                page_text,
                chunk_size
            )
            
            logger.info(f"✅ Page chunked: page={page_number}, chunks={len(chunks)}")
            
            # Validar que hay chunks
            if not chunks:
                logger.warning(f"⚠️  No chunks created for page {page_number}, skipping")
                return
            
            # Crear metadata para cada chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_metadata.append({
                    "chunk_index": i,
                    "chunk_size": len(chunk),
                    "page_number": page_number,
                    "total_pages": total_pages,
                    "pdf_filename": job.get('metadata', {}).get('filename'),
                    **job.get('metadata', {}).get('user_metadata', {})
                })
            
            # Publicar evento de chunks (de esta página)
            await self.event_bus.publish(PdfChunkedEvent(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                collection=collection,
                chunks=chunks,
                chunk_metadata=chunk_metadata,
            ))
            
            # Actualizar progreso (40% a 60% = 20% total / total_pages)
            progress_per_page = int(20 / total_pages) if total_pages > 0 else 1
            self.job_repo.increment_progress(
                job_id,
                delta=progress_per_page,
                status="chunking",
                result={
                    "pages_processed": page_number,
                    "total_pages": total_pages,
                    "chunks_created": len(chunks)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Chunking failed: job_id={job_id}, page={page_number}, error={e}", exc_info=True)
            self.job_repo.update_status(job_id, "failed", error=f"Chunking failed: {str(e)}")
            
            await self.event_bus.publish(PdfIngestFailedEvent(
                user_id=user_id,
                project_id=project_id,
                collection=collection,
                job_id=job_id,
                stage="chunking",
                error_message=str(e),
            ))
            
            raise

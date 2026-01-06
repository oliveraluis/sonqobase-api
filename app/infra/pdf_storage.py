"""
Content-Addressable Storage para PDFs usando MongoDB GridFS con deduplicación.
"""
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from gridfs import GridFS
from pymongo.database import Database

logger = logging.getLogger(__name__)


class PdfStorage:
    """
    Almacenamiento de PDFs con deduplicación automática usando content hashing.
    
    Características:
    - Deduplicación: PDFs idénticos se guardan una sola vez
    - Content-addressable: Usa SHA-256 del contenido como identificador
    - TTL automático: Archivos se eliminan después de expirar
    - Reference counting: Rastrea cuántos jobs usan cada PDF
    """
    
    def __init__(self, db: Database):
        self.db = db  # Guardar referencia a database
        self.fs = GridFS(db, collection='pdf_temp')
        
        # Acceder a colección de archivos
        files_collection = db['pdf_temp.files']
        
        # Eliminar índice único antiguo si existe
        try:
            files_collection.drop_index("metadata.content_hash_1")
            logger.info("🗑️  Dropped old unique index on content_hash")
        except Exception:
            pass  # No existe, ignorar
        
        # Crear índices
        # Índice TTL en expires_at
        files_collection.create_index(
            "metadata.expires_at",
            expireAfterSeconds=0
        )
        
        # Índice en content_hash (NO único)
        files_collection.create_index("metadata.content_hash")
        
        # Índice en job_id para búsqueda rápida
        files_collection.create_index("metadata.job_id")
        
        logger.info("✅ PdfStorage initialized with TTL + indexes")
    
    async def save_or_reuse(
        self,
        pdf_bytes: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Guardar PDF en GridFS.
        
        Calcula hash para tracking, pero SIEMPRE guarda el archivo
        (esto permite múltiples jobs usar el mismo PDF).
        
        Args:
            pdf_bytes: Contenido del PDF
            metadata: Metadatos (debe incluir job_id)
        
        Returns:
            content_hash: SHA-256 del PDF
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # 1. Calcular hash (para estadísticas)
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()
        
        def _calculate_hash():
            return hashlib.sha256(pdf_bytes).hexdigest()
        
        content_hash = await loop.run_in_executor(executor, _calculate_hash)
        
        # 2. Guardar en GridFS (siempre, con job_id único)
        def _save_sync():
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            return self.fs.put(
                pdf_bytes,
                filename=f"{metadata.get('job_id', content_hash)}.pdf" if metadata else f"{content_hash}.pdf",
                metadata={
                    "content_hash": content_hash,
                    "size_bytes": len(pdf_bytes),
                    "expires_at": expires_at,
                    "created_at": datetime.now(timezone.utc),
                    **(metadata or {})
                }
            )
        
        file_id = await loop.run_in_executor(executor, _save_sync)
        
        logger.info(
            f"💾 PDF saved: hash={content_hash[:8]}..., "
            f"size={len(pdf_bytes)/1024:.2f}KB, "
            f"job_id={metadata.get('job_id') if metadata else 'N/A'}"
        )
        
        return content_hash
    
    def get_by_hash(self, content_hash: str) -> bytes:
        """
        Obtener PDF por su content hash.
        
        Args:
            content_hash: SHA-256 del PDF
        
        Returns:
            Contenido del PDF en bytes
        
        Raises:
            FileNotFoundError: Si el PDF no existe o ya expiró
        """
        file = self.fs.find_one({"metadata.content_hash": content_hash})
        if not file:
            raise FileNotFoundError(
                f"PDF not found for hash {content_hash[:8]}... (may have expired)"
            )
        
        pdf_bytes = file.read()
        logger.info(
            f"📥 PDF retrieved: hash={content_hash[:8]}..., "
            f"size={len(pdf_bytes)/1024:.2f}KB"
        )
        return pdf_bytes
    
    def _increment_reference(self, content_hash: str):
        """Incrementar contador de referencias"""
        files_collection = self.db['pdf_temp.files']
        
        result = files_collection.update_one(
            {"metadata.content_hash": content_hash},
            {"$inc": {"metadata.reference_count": 1}}
        )
        
        if result.modified_count > 0:
            logger.debug(f"📊 Reference count incremented for hash={content_hash[:8]}...")
    
    def _extend_ttl(self, content_hash: str, hours: int = 24):
        """Extender TTL de un PDF"""
        files_collection = self.db['pdf_temp.files']
        
        new_expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        
        result = files_collection.update_one(
            {"metadata.content_hash": content_hash},
            {"$set": {"metadata.expires_at": new_expires_at}}
        )
        
        if result.modified_count > 0:
            logger.debug(f"⏰ TTL extended for hash={content_hash[:8]}... until {new_expires_at}")
    
    def delete_by_hash(self, content_hash: str) -> bool:
        """Eliminar PDF por hash (decrementar referencia)"""
        files_collection = self.db['pdf_temp.files']
        
        file = files_collection.find_one({"metadata.content_hash": content_hash})
        
        if not file:
            return False
        
        ref_count = file.get('metadata', {}).get('reference_count', 1)
        
        if ref_count <= 1:
            # Última referencia - eliminar físicamente
            self.fs.delete(file['_id'])
            logger.info(f"🗑️  PDF deleted: hash={content_hash[:8]}...")
            return True
        else:
            # Aún hay referencias - solo decrementar
            files_collection.update_one(
                {"metadata.content_hash": content_hash},
                {"$inc": {"metadata.reference_count": -1}}
            )
            logger.debug(f"📉 Reference count decremented for hash={content_hash[:8]}...")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de storage.
        
        Returns:
            Diccionario con estadísticas
        """
        files_collection = self.db['pdf_temp.files']
        
        total_files = files_collection.count_documents({})
        total_size = sum(
            f.get('metadata', {}).get('size_bytes', 0)
            for f in files_collection.find({}, {"metadata.size_bytes": 1})
        )
        total_references = sum(
            f.get('metadata', {}).get('reference_count', 1)
            for f in files_collection.find({}, {"metadata.reference_count": 1})
        )
        
        dedup_rate = ((total_references - total_files) / total_references * 100) if total_references > 0 else 0
        
        return {
            "total_files": total_files,
            "total_size_mb": total_size / (1024 * 1024),
            "total_references": total_references,
            "deduplication_rate": f"{dedup_rate:.1f}%",
            "storage_saved_mb": (total_size * (total_references - total_files) / total_references) / (1024 * 1024) if total_references > 0 else 0
        }

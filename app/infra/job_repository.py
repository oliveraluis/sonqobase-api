"""
Repository para gestión de Jobs de procesamiento.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.infra.mongo_client import get_mongo_client
from app.config import settings

logger = logging.getLogger(__name__)


class JobRepository:
    """
    Repositorio para tracking de jobs de procesamiento asíncrono.
    """
    
    def __init__(self):
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        self.collection = meta_db['jobs']
        
        # Crear índices
        self.collection.create_index("job_id", unique=True)
        self.collection.create_index("user_id")
        self.collection.create_index("status")
        self.collection.create_index("created_at")
        
        # Índice TTL para limpiar jobs completados después de 7 días
        self.collection.create_index(
            "completed_at",
            expireAfterSeconds=7 * 24 * 60 * 60  # 7 días
        )
        
        logger.info("✅ JobRepository initialized")
    
    def create(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        collection_name: str,
        job_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crear un nuevo job.
        
        Args:
            job_id: ID único del job
            user_id: ID del usuario
            project_id: ID del proyecto
            collection_name: Nombre de la colección destino
            job_type: Tipo de job ("pdf_ingest", "text_ingest", etc.)
            metadata: Metadatos adicionales
        
        Returns:
            Job creado
        """
        job = {
            "job_id": job_id,
            "user_id": user_id,
            "project_id": project_id,
            "collection": collection_name,
            "type": job_type,
            "status": "queued",
            "progress": 0,
            "metadata": metadata,
            "result": {},
            "error": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "completed_at": None
        }
        
        self.collection.insert_one(job)
        logger.info(f"📝 Job created: {job_id} ({job_type})")
        return job
    
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener un job por ID.
        
        Args:
            job_id: ID del job
        
        Returns:
            Job o None si no existe
        """
        job = self.collection.find_one({"job_id": job_id}, {"_id": 0})
        return job
    
    def update_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """
        Actualizar estado de un job.
        
        Args:
            job_id: ID del job
            status: Nuevo estado
            progress: Progreso (0-100)
            result: Resultado parcial o final
            error: Mensaje de error si falló
        """
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if progress is not None:
            update_data["progress"] = progress
        
        if result is not None:
            update_data["result"] = result
        
        if error is not None:
            update_data["error"] = error
        
        if status == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc)
            update_data["progress"] = 100
        
        if status == "failed":
            update_data["completed_at"] = datetime.now(timezone.utc)
        
        self.collection.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        logger.info(f"📊 Job updated: {job_id} → {status} ({progress}%)")
    
    def increment_progress(
        self,
        job_id: str,
        delta: int,
        status: Optional[str] = None,
        result: Optional[Dict] = None
    ):
        """
        Incrementar progreso de forma atómica (thread-safe).
        
        Args:
            job_id: ID del job
            delta: Cantidad a incrementar
            status: Nuevo status (opcional)
            result: Resultado parcial (opcional)
        """
        update = {
            "$inc": {"progress": delta},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
        
        if status:
            update["$set"]["status"] = status
        
        if result:
            update["$set"]["result"] = result
        
        self.collection.update_one(
            {"job_id": job_id},
            update
        )
        
        # Log para debugging
        job = self.get(job_id)
        new_progress = job.get('progress', 0) if job else 0
        logger.info(f"📊 Job progress: {job_id} +{delta}% → {new_progress}%")
    
    def get_user_jobs(
        self,
        user_id: str,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener jobs de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de jobs
            status: Filtrar por estado (opcional)
        
        Returns:
            Lista de jobs
        """
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        jobs = list(
            self.collection
            .find(query, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
        
        return jobs
    
    def find_by_filter(
        self,
        filter_query: Dict[str, Any],
        limit: int = 50,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar jobs con filtro personalizado.
        
        Args:
            filter_query: Filtro MongoDB (ej: {"project_id": "proj_123", "status": "completed"})
            limit: Número máximo de jobs
            sort: Lista de tuplas para ordenamiento (ej: [("created_at", -1)])
        
        Returns:
            Lista de jobs que coinciden con el filtro
        """
        cursor = self.collection.find(filter_query, {"_id": 0})
        
        if sort:
            cursor = cursor.sort(sort)
        
        jobs = list(cursor.limit(limit))
        
        logger.info(f"Found {len(jobs)} jobs matching filter")
        return jobs

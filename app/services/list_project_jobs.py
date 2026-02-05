"""
Service para listar jobs de un proyecto específico.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.infra.job_repository import JobRepository

logger = logging.getLogger(__name__)


class ListProjectJobsService:
    """
    Servicio para listar jobs de un proyecto.
    """
    
    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo
    
    def execute(
        self,
        project_id: str,
        user_id: str,
        limit: int = 50,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Listar jobs de un proyecto específico.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario (para verificar permisos)
            limit: Número máximo de jobs a retornar
            status_filter: Filtrar por estado (pending, processing, completed, failed)
        
        Returns:
            Dict con lista de jobs
        """
        # Validar limit
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 10
        
        # Construir filtro
        filter_query = {
            "project_id": project_id,
            "user_id": user_id  # Solo jobs del usuario
        }
        
        if status_filter:
            valid_statuses = ["queued", "extracting_text", "generating_embeddings", "completed", "failed"]
            if status_filter not in valid_statuses:
                raise ValueError(f"Invalid status filter. Must be one of: {valid_statuses}")
            filter_query["status"] = status_filter
        
        # Obtener jobs del repositorio
        jobs = self.job_repo.find_by_filter(
            filter_query=filter_query,
            limit=limit,
            sort=[("created_at", -1)]  # Más recientes primero
        )
        
        # Formatear respuesta
        jobs_list = []
        for job in jobs:
            jobs_list.append({
                "job_id": job.get("job_id"),
                "collection": job.get("collection"),  # Campo correcto de la BD
                "status": job.get("status"),
                "created_at": job.get("created_at").isoformat() if job.get("created_at") else None,
                "completed_at": job.get("completed_at").isoformat() if job.get("completed_at") else None,
                "error_message": job.get("error_message"),
                "result": job.get("result"),
                "metadata": job.get("metadata", {})
            })
        
        logger.info(f"Retrieved {len(jobs_list)} jobs for project {project_id}")
        
        return {
            "jobs": jobs_list,
            "count": len(jobs_list),
            "project_id": project_id
        }

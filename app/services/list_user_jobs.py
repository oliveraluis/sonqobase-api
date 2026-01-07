"""
Servicio para listar jobs de un usuario.
"""
from typing import Dict, Any, Optional, List

from app.infra.job_repository import JobRepository


class ListUserJobsService:
    """Servicio para listar los jobs de un usuario"""
    
    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo
    
    def execute(
        self,
        user_id: str,
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Listar jobs del usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de jobs (default: 10, max: 50)
            status_filter: Filtrar por estado (queued, processing, completed, failed)
        
        Returns:
            Diccionario con lista de jobs y conteo
        """
        # Limitar máximo
        limit = min(limit, 50)
        
        # Obtener jobs del usuario
        jobs = self.job_repo.get_user_jobs(user_id, limit=limit, status=status_filter)
        
        # Formatear respuesta
        return {
            "jobs": [
                {
                    "job_id": job['job_id'],
                    "type": job['type'],
                    "status": job['status'],
                    "progress": job['progress'],
                    "collection": job['collection'],
                    "created_at": job['created_at'].isoformat(),
                    "completed_at": job['completed_at'].isoformat() if job['completed_at'] else None,
                }
                for job in jobs
            ],
            "count": len(jobs)
        }

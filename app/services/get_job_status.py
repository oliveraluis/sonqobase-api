"""
Servicio para obtener el estado de un job.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from app.infra.job_repository import JobRepository


class GetJobStatusService:
    """Servicio para obtener el estado de un job con validación de permisos"""
    
    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo
    
    def execute(self, job_id: str, user_id: str) -> Dict[str, Any]:
        """
        Obtener estado de un job de procesamiento.
        
        Args:
            job_id: ID del job a consultar
            user_id: ID del usuario que hace la consulta
        
        Returns:
            Información formateada del job
        
        Raises:
            ValueError: Si el job no existe o el usuario no tiene acceso
        """
        # Obtener job
        job = self.job_repo.get(job_id)
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Verificar que el job pertenece al usuario
        if job['user_id'] != user_id:
            raise ValueError("Access denied to this job")
        
        # Formatear y retornar información del job
        return {
            "job_id": job['job_id'],
            "type": job['type'],
            "status": job['status'],
            "progress": job['progress'],
            "collection": job['collection'],
            "created_at": job['created_at'].isoformat(),
            "updated_at": job['updated_at'].isoformat(),
            "completed_at": job['completed_at'].isoformat() if job['completed_at'] else None,
            "result": job.get('result', {}),
            "error": job.get('error'),
            "metadata": job.get('metadata', {})
        }

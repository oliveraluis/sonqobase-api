"""
API endpoints para consulta de Jobs.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional, List

from app.infra.job_repository import JobRepository
from app.config import settings
from pymongo import MongoClient

router = APIRouter()
logger = logging.getLogger(__name__)

# Inicializar repositorio
client = MongoClient(settings.mongo_uri)
meta_db = client[settings.mongo_meta_db]
job_repo = JobRepository(meta_db)


@router.get("/{job_id}")
def get_job_status(job_id: str, request: Request):
    """
    Obtener estado de un job de procesamiento.
    
    Requiere autenticación (User o Project API Key).
    Solo puede ver jobs propios.
    """
    # Verificar autenticación
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_id = request.state.user_id
    
    # Obtener job
    job = job_repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Verificar que el job pertenece al usuario
    if job['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job"
        )
    
    # Retornar información del job
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


@router.get("")
def list_user_jobs(
    request: Request,
    limit: int = 10,
    status_filter: Optional[str] = None
):
    """
    Listar jobs del usuario autenticado.
    
    Query params:
    - limit: Número máximo de jobs (default: 10, max: 50)
    - status: Filtrar por estado (queued, processing, completed, failed)
    """
    # Verificar autenticación
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_id = request.state.user_id
    
    # Limitar máximo
    limit = min(limit, 50)
    
    # Obtener jobs del usuario
    jobs = job_repo.get_user_jobs(user_id, limit=limit, status=status_filter)
    
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

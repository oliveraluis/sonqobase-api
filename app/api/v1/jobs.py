"""
API endpoints para consulta de Jobs.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional

from app.services.get_job_status import GetJobStatusService
from app.services.list_user_jobs import ListUserJobsService
from app.services.list_project_jobs import ListProjectJobsService
from app.infra.job_repository import JobRepository
from app.dependencies.auth import require_user_or_project_key

router = APIRouter()
logger = logging.getLogger(__name__)


# Dependency Injection
def get_job_status_service() -> GetJobStatusService:
    return GetJobStatusService(job_repo=JobRepository())


def get_list_user_jobs_service() -> ListUserJobsService:
    return ListUserJobsService(job_repo=JobRepository())


def get_list_project_jobs_service() -> ListProjectJobsService:
    return ListProjectJobsService(job_repo=JobRepository())


# Endpoints
@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    service: GetJobStatusService = Depends(get_job_status_service),
    auth: dict = Depends(require_user_or_project_key),
):
    """
    Obtener estado de un job de procesamiento.
    
    Requiere autenticación (User o Project API Key).
    Solo puede ver jobs propios.
    """
    user_id = auth["user_id"]
    
    try:
        result = service.execute(job_id=job_id, user_id=user_id)
        return result
    
    except ValueError as e:
        error_msg = str(e)
        
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "Access denied" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.get("")
async def list_user_jobs(
    limit: int = 10,
    status_filter: Optional[str] = None,
    service: ListUserJobsService = Depends(get_list_user_jobs_service),
    auth: dict = Depends(require_user_or_project_key),
):
    """
    Listar jobs del usuario autenticado.
    
    Query params:
    - limit: Número máximo de jobs (default: 10, max: 50)
    - status: Filtrar por estado (queued, processing, completed, failed)
    """
    user_id = auth["user_id"]
    
    try:
        result = service.execute(
            user_id=user_id,
            limit=limit,
            status_filter=status_filter
        )
        return result
    
    except ValueError as e:
        logger.warning(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

from fastapi import APIRouter, Depends, status, Request, HTTPException
from typing import List
from app.models.requests import ProjectCreateRequest
from app.models.responses import ProjectResponse
from app.services.create_project import CreateProjectService
from app.services.list_user_projects import ListUserProjectsService
from app.services.get_project_details import GetProjectDetailsService
from app.services.list_project_jobs import ListProjectJobsService
from app.infra.project_repository import ProjectRepository
from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository
from app.infra.job_repository import JobRepository
from app.dependencies.auth import require_user_key

router = APIRouter()

def get_create_project_service() -> CreateProjectService:
    repo = ProjectRepository()
    user_repo = UserRepository()
    plan_repo = PlanRepository()
    return CreateProjectService(repo, user_repo, plan_repo)

def get_list_projects_service() -> ListUserProjectsService:
    repo = ProjectRepository()
    return ListUserProjectsService(repo)

def get_project_details_service() -> GetProjectDetailsService:
    repo = ProjectRepository()
    return GetProjectDetailsService(repo)

def get_list_project_jobs_service() -> ListProjectJobsService:
    return ListProjectJobsService(job_repo=JobRepository())


@router.get("", response_model=List[dict])
async def list_projects(
    user: dict = Depends(require_user_key),
    service: ListUserProjectsService = Depends(get_list_projects_service),
):
    """
    Listar todos los proyectos del usuario autenticado.
    Requiere User API Key.
    """
    return service.execute(user["user_id"])


@router.get("/{project_id}", response_model=dict)
async def get_project(
    project_id: str,
    user: dict = Depends(require_user_key),
    service: GetProjectDetailsService = Depends(get_project_details_service),
):
    """
    Obtener detalles de un proyecto específico.
    Requiere User API Key.
    """
    try:
        return service.execute(project_id, user["user_id"])
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


@router.get("/{project_id}/api-key", response_model=dict)
async def get_project_api_key(
    project_id: str,
    user: dict = Depends(require_user_key),
):
    """
    Obtener la API key de un proyecto.
    Requiere User API Key.
    """
    from app.services.get_project_api_key import GetProjectApiKeyService
    
    service = GetProjectApiKeyService(ProjectRepository())
    
    try:
        return service.execute(project_id, user["user_id"])
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


@router.get("/{project_id}/collections", response_model=dict)
async def list_project_collections(
    project_id: str,
    user: dict = Depends(require_user_key),
):
    """
    Listar todas las colecciones de un proyecto.
    Requiere User API Key.
    """
    from app.services.list_project_collections import ListProjectCollectionsService
    
    service = ListProjectCollectionsService(ProjectRepository())
    
    try:
        return service.execute(project_id, user["user_id"])
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_project(
    payload: ProjectCreateRequest,
    request: Request,
    service: CreateProjectService = Depends(get_create_project_service),
) -> ProjectResponse:
    """
    Crear un nuevo proyecto.
    Requiere User API Key.
    Valida límites del plan del usuario.
    """
    # El middleware ya validó la autenticación
    if request.state.auth_level not in ["user", "master"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User API Key required"
        )
    
    # Obtener user_id del middleware
    user_id = request.state.user_id
    
    try:
        return await service.execute(payload, user_id)
    except ValueError as e:
        # Límite excedido o usuario no encontrado
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/jobs")
async def list_project_jobs(
    project_id: str,
    limit: int = 50,
    status_filter: str = None,
    user: dict = Depends(require_user_key),
    service: ListProjectJobsService = Depends(get_list_project_jobs_service),
):
    """
    Listar jobs de un proyecto específico.
    
    Query params:
    - limit: Número máximo de jobs (default: 50, max: 100)
    - status_filter: Filtrar por estado (pending, processing, completed, failed)
    
    Requiere User API Key.
    """
    user_id = user["user_id"]
    
    try:
        result = service.execute(
            project_id=project_id,
            user_id=user_id,
            limit=limit,
            status_filter=status_filter
        )
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

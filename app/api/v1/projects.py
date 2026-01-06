from fastapi import APIRouter, Depends, status, Request, HTTPException
from app.models.requests import ProjectCreateRequest
from app.models.responses import ProjectResponse
from app.services.create_project import CreateProjectService
from app.infra.project_repository import ProjectRepository
from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository

router = APIRouter()

def get_create_project_service() -> CreateProjectService:
    repo = ProjectRepository()
    user_repo = UserRepository()
    plan_repo = PlanRepository()
    return CreateProjectService(repo, user_repo, plan_repo)

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

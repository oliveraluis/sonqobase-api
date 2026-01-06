from fastapi import APIRouter, Depends, status
from app.models.requests import ProjectCreateRequest
from app.models.responses import ProjectResponse
from app.services.create_project import CreateProjectService
from app.infra.project_repository import ProjectRepository

router = APIRouter()

def get_create_project_service() -> CreateProjectService:
    repo = ProjectRepository()
    return CreateProjectService(repo)

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    payload: ProjectCreateRequest,
    service: CreateProjectService = Depends(get_create_project_service),
) -> ProjectResponse:
    print(payload)
    return service.execute(payload)

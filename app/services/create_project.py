from datetime import datetime, timedelta, timezone
from uuid import uuid4
from secrets import token_hex

from app.domain.entities import Project, Database
from app.models.requests import ProjectCreateRequest
from app.models.responses import (
    ProjectResponse,
    DatabaseResponse,
    ApiKeyResponse,
)
from app.infra.project_repository import ProjectRepositoryProtocol


def _to_response(
    project: Project,
    api_key: str,
) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        expires_at=project.expires_at,
        database=DatabaseResponse(
            name=project.database.name,
            expires_at=project.database.expires_at,
        ),
        api_key=ApiKeyResponse(
            key=api_key,
        ),
    )


class CreateProjectService:
    def __init__(self, repository: ProjectRepositoryProtocol):
        self.repository = repository

    def execute(self, payload: ProjectCreateRequest) -> ProjectResponse:
        # 1️⃣ IDs y expiración
        project_id: str = f"proj_{uuid4().hex[:8]}"
        api_key: str = f"temp_{token_hex(16)}"
        expires_at: datetime = datetime.now(timezone.utc) + timedelta(hours=48)

        # 2️⃣ Database efímera
        database = Database(
            name=f"ephemeral_{uuid4().hex[:6]}",
            expires_at=expires_at,
        )

        # 3️⃣ Dominio
        project = Project(
            id=project_id,
            name=payload.name,
            description=payload.description,
            status="provisioned",
            expires_at=expires_at,
            database=database,
        )

        # 4️⃣ Persistencia
        self.repository.save(project, api_key)

        # 5️⃣ Response
        return _to_response(project, api_key)

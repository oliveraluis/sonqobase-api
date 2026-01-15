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
from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository
from app.infra.event_bus import get_event_bus
from app.domain.events import ProjectCreatedEvent


def _to_response(
    project: Project,
    api_key: str,
) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        slug=project.slug,
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
    """
    Servicio para crear proyectos.
    Valida límites del usuario según su plan.
    """
    
    def __init__(
        self,
        repository: ProjectRepositoryProtocol,
        user_repo: UserRepository = None,
        plan_repo: PlanRepository = None,
    ):
        self.repository = repository
        self.user_repo = user_repo or UserRepository()
        self.plan_repo = plan_repo or PlanRepository()
        self.event_bus = get_event_bus()

    async def execute(
        self,
        payload: ProjectCreateRequest,
        user_id: str,
    ) -> ProjectResponse:
        """
        Crear un nuevo proyecto.
        
        Args:
            payload: Datos del proyecto (name, slug, description)
            user_id: ID del usuario que crea el proyecto
        
        Returns:
            ProjectResponse con el proyecto creado y API key
        
        Raises:
            ValueError: Si el usuario no existe, excede límites, o slug ya existe
        """
        # 1️⃣ Obtener usuario y plan
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario '{user_id}' no encontrado")
        
        plan = self.plan_repo.get_by_name(user.plan_name)
        if not plan:
            raise ValueError(f"Plan '{user.plan_name}' no encontrado")
        
        # 2️⃣ Validar que el slug sea único
        if self.repository.slug_exists(payload.slug):
            raise ValueError(
                f"El slug '{payload.slug}' ya está en uso. "
                f"Por favor elige un identificador diferente."
            )
        
        # 3️⃣ Validar límite de proyectos
        if user.usage.projects_count >= plan.projects_limit:
            raise ValueError(
                f"Límite de proyectos excedido. "
                f"Tu plan permite {plan.projects_limit} proyectos, "
                f"actualmente tienes {user.usage.projects_count}. "
                f"Actualiza tu plan para crear más proyectos."
            )
        
        # 3️⃣ Generar IDs y API key
        project_id: str = f"proj_{uuid4().hex[:8]}"
        api_key: str = f"sonqo_proj_{token_hex(16)}"  # Actualizado formato
        
        # 4️⃣ Calcular expiración según plan
        retention_hours = plan.retention_hours
        expires_at: datetime = datetime.now(timezone.utc) + timedelta(hours=retention_hours)

        # 5️⃣ Database efímera
        database = Database(
            name=f"ephemeral_{uuid4().hex[:6]}",
            expires_at=expires_at,
        )

        # 6️⃣ Crear entidad Project
        project = Project(
            id=project_id,
            user_id=user_id,  # Relación con usuario
            slug=payload.slug,  # Identificador legible
            name=payload.name,
            description=payload.description,
            status="provisioned",
            expires_at=expires_at,
            database=database,
        )

        # 7️⃣ Persistir proyecto
        self.repository.save(project, api_key)
        
        # 8️⃣ Incrementar contador de proyectos del usuario
        self.user_repo.increment_usage(user_id, projects=1)
        
        # 9️⃣ Publicar evento de dominio
        await self.event_bus.publish(ProjectCreatedEvent(
            user_id=user_id,
            project_id=project_id,
            project_slug=payload.slug,
            project_name=payload.name,
            plan_name=user.plan_name,
        ))

        # 🔟 Response
        return _to_response(project, api_key)

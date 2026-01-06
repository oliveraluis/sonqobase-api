"""
Servicio para crear usuarios de SonqoBase.
"""
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from secrets import token_hex

from app.domain.entities import User, UsageStats
from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository


class CreateUserService:
    """Servicio para crear usuarios con un plan específico"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
    ):
        self.user_repo = user_repo
        self.plan_repo = plan_repo
    
    def execute(
        self,
        email: str,
        plan_name: str = "free",
        webhook_url: str | None = None,
    ) -> dict:
        """
        Crear un nuevo usuario.
        
        Args:
            email: Email del usuario
            plan_name: Nombre del plan ("free", "starter", "pro")
            webhook_url: URL para webhooks (solo Plan Pro)
        
        Returns:
            dict con user_id y api_key (en texto plano, solo se muestra una vez)
        
        Raises:
            ValueError: Si el email ya existe o el plan no existe
        """
        # Validar que el email no exista
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError(f"User with email '{email}' already exists")
        
        # Validar que el plan exista
        plan = self.plan_repo.get_by_name(plan_name)
        if not plan:
            raise ValueError(f"Plan '{plan_name}' does not exist")
        
        # Validar webhook_url solo para Plan Pro
        if webhook_url and plan_name != "pro":
            raise ValueError("Webhooks are only available for Pro plan")
        
        # Generar IDs y API key
        user_id = f"user_{uuid4().hex[:12]}"
        api_key = f"sonqo_user_{token_hex(24)}"  # 48 caracteres hex
        
        # Calcular período de uso (mes actual)
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Próximo mes
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)
        
        # Crear entidad User
        user = User(
            id=user_id,
            email=email,
            api_key_hash="",  # Se hashea en el repositorio
            plan_name=plan_name,
            status="active",
            created_at=now,
            updated_at=now,
            usage=UsageStats(
                projects_count=0,
                reads_count=0,
                writes_count=0,
                rag_queries_count=0,
                period_start=period_start,
                period_end=period_end,
            ),
            webhook_url=webhook_url,
        )
        
        # Guardar en base de datos
        self.user_repo.save(user, api_key)
        
        return {
            "user_id": user_id,
            "email": email,
            "plan": plan_name,
            "api_key": api_key,  # Solo se muestra una vez
            "created_at": now,
        }

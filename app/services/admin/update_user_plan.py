"""
Servicio para actualizar el plan de un usuario.
"""
from datetime import datetime, timezone

from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository


class UpdateUserPlanService:
    """Servicio para cambiar el plan de un usuario (upgrade/downgrade)"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
    ):
        self.user_repo = user_repo
        self.plan_repo = plan_repo
    
    def execute(self, user_id: str, new_plan_name: str) -> dict:
        """
        Actualizar plan del usuario.
        
        Args:
            user_id: ID del usuario
            new_plan_name: Nuevo plan ("free", "starter", "pro")
        
        Returns:
            dict con confirmación del cambio
        
        Raises:
            ValueError: Si el usuario o plan no existen
        """
        # Validar que el usuario exista
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found")
        
        # Validar que el plan exista
        new_plan = self.plan_repo.get_by_name(new_plan_name)
        if not new_plan:
            raise ValueError(f"Plan '{new_plan_name}' does not exist")
        
        # Actualizar plan
        old_plan_name = user.plan_name
        self.user_repo.update_plan(user_id, new_plan_name)
        
        return {
            "user_id": user_id,
            "old_plan": old_plan_name,
            "new_plan": new_plan_name,
            "updated_at": datetime.now(timezone.utc),
        }

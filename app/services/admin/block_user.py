"""
Servicio para bloquear/desbloquear usuarios.
"""
from datetime import datetime, timezone

from app.infra.user_repository import UserRepository


class BlockUserService:
    """Servicio para bloquear o desbloquear usuarios"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def execute(self, user_id: str, block: bool = True) -> dict:
        """
        Bloquear o desbloquear usuario.
        
        Args:
            user_id: ID del usuario
            block: True para bloquear, False para desbloquear
        
        Returns:
            dict con confirmación del cambio
        
        Raises:
            ValueError: Si el usuario no existe
        """
        # Validar que el usuario exista
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found")
        
        # Actualizar estado
        new_status = "blocked" if block else "active"
        self.user_repo.update_status(user_id, new_status)
        
        return {
            "user_id": user_id,
            "status": new_status,
            "updated_at": datetime.now(timezone.utc),
        }

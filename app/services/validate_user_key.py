"""
Servicio para validar User API Key y obtener información del usuario.
"""
import logging
from app.infra.user_repository import UserRepository
from app.domain.entities import User

logger = logging.getLogger(__name__)


class ValidateUserKeyService:
    """Servicio para validar User API Key"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def execute(self, user_key: str) -> dict:
        """
        Validar User API Key y retornar información del usuario.
        
        Args:
            user_key: User API Key a validar
        
        Returns:
            Diccionario con información del usuario
        
        Raises:
            ValueError: Si la API key es inválida o el usuario no está activo
        """
        # Validar que la key no esté vacía
        if not user_key or not user_key.strip():
            raise ValueError("API key is required")
        
        # Buscar usuario por API key
        user = self.user_repo.get_by_api_key(user_key)
        
        if not user:
            raise ValueError("Invalid API key")
        
        # Verificar que el usuario esté activo
        if user.status != "active":
            raise ValueError(f"User account is {user.status}")
        
        logger.info(f"User validated: {user.email}")
        
        # Retornar información del usuario
        return {
            "user_id": user.id,
            "email": user.email,
            "plan": user.plan_name,
            "status": user.status,
            "usage": {
                "projects": user.usage.projects_count,
                "reads": user.usage.reads_count,
                "writes": user.usage.writes_count,
                "rag_queries": user.usage.rag_queries_count,
            },
            "created_at": user.created_at.isoformat(),
        }

"""
Servicio para obtener la API key de un proyecto.
"""
import logging
from typing import Optional

from app.infra.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class GetProjectApiKeyService:
    """Servicio para obtener la API key de un proyecto"""
    
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo
    
    def execute(self, project_id: str, user_id: str) -> dict:
        """
        Obtener la API key de un proyecto.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario (para verificar ownership)
        
        Returns:
            Dict con la API key
        
        Raises:
            ValueError: Si el proyecto no existe o no pertenece al usuario
        """
        # Verificar que el proyecto existe y pertenece al usuario
        project = self.project_repo.get_by_id(project_id)
        
        if not project:
            raise ValueError("Project not found")
        
        if project.user_id != user_id:
            raise ValueError("Project does not belong to user")
        
        # Obtener API key desencriptada
        api_key = self.project_repo.get_api_key(project_id)
        
        if not api_key:
            raise ValueError("API key not found or could not be decrypted")
        
        logger.info(f"Retrieved API key for project {project_id}")
        
        return {
            "project_id": project_id,
            "api_key": api_key
        }

"""
Servicio para obtener detalles de un proyecto.
"""
import logging
from typing import Optional

from app.infra.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class GetProjectDetailsService:
    """Servicio para obtener detalles de un proyecto"""
    
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo
    
    def execute(self, project_id: str, user_id: str) -> dict:
        """
        Obtener detalles de un proyecto.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario (para verificar ownership)
        
        Returns:
            Detalles del proyecto serializados
        
        Raises:
            ValueError: Si el proyecto no existe o no pertenece al usuario
        """
        project = self.project_repo.get_by_id(project_id)
        
        if not project:
            raise ValueError("Project not found")
        
        # Verificar ownership
        if project.user_id != user_id:
            raise ValueError("Project does not belong to user")
        
        logger.info(f"Retrieved project {project_id} for user {user_id}")
        
        return {
            "project_id": project.id,
            "name": project.name,
            "slug": project.slug,
            "description": project.description,
            "status": project.status,
            "expires_at": project.expires_at.isoformat(),
            "database": project.database.name,
            "stats": {
                "reads_count": project.stats.reads_count,
                "writes_count": project.stats.writes_count,
                "rag_queries_count": project.stats.rag_queries_count,
                "last_activity": project.stats.last_activity.isoformat() if project.stats.last_activity else None,
            }
        }

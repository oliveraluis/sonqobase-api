"""
Servicio para listar proyectos de un usuario.
"""
import logging
from typing import List

from app.infra.project_repository import ProjectRepository
from app.domain.entities import Project

logger = logging.getLogger(__name__)


class ListUserProjectsService:
    """Servicio para listar proyectos de un usuario"""
    
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo
    
    def execute(self, user_id: str) -> List[dict]:
        """
        Listar todos los proyectos de un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de proyectos serializados
        """
        projects = self.project_repo.get_by_user(user_id)
        
        logger.info(f"User {user_id} has {len(projects)} projects")
        
        return [
            {
                "project_id": p.id,
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "status": p.status,
                "expires_at": p.expires_at.isoformat(),
                "database": p.database.name,
                "stats": {
                    "reads_count": p.stats.reads_count,
                    "writes_count": p.stats.writes_count,
                    "rag_queries_count": p.stats.rag_queries_count,
                    "last_activity": p.stats.last_activity.isoformat() if p.stats.last_activity else None,
                }
            }
            for p in projects
        ]

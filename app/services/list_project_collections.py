"""
Servicio para listar colecciones de un proyecto.
"""
import logging
from typing import List

from app.infra.project_repository import ProjectRepository
from app.infra.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)


class ListProjectCollectionsService:
    """Servicio para listar colecciones de un proyecto"""
    
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo
    
    def execute(self, project_id: str, user_id: str) -> dict:
        """
        Listar todas las colecciones de un proyecto.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario (para verificar ownership)
        
        Returns:
            Dict con lista de colecciones y sus stats
        
        Raises:
            ValueError: Si el proyecto no existe o no pertenece al usuario
        """
        # Verificar que el proyecto existe y pertenece al usuario
        project = self.project_repo.get_by_id(project_id)
        
        if not project:
            raise ValueError("Project not found")
        
        if project.user_id != user_id:
            raise ValueError("Project does not belong to user")
        
        # Obtener colecciones de MongoDB
        client = get_mongo_client()
        db = client[project.database.name]
        
        # Listar todas las colecciones (excluyendo system y audit collections)
        collection_names = [
            name for name in db.list_collection_names()
            if not name.startswith('system.') and not name.startswith('_')
        ]
        
        # Obtener stats de cada colección
        collections = []
        for coll_name in collection_names:
            try:
                coll = db[coll_name]
                doc_count = coll.count_documents({})
                
                collections.append({
                    "name": coll_name,
                    "document_count": doc_count,
                })
            except Exception as e:
                logger.warning(f"Error getting stats for collection {coll_name}: {e}")
                collections.append({
                    "name": coll_name,
                    "document_count": 0,
                })
        
        logger.info(f"Retrieved {len(collections)} collections for project {project_id}")
        
        return {
            "project_id": project_id,
            "database": project.database.name,
            "collections": collections,
            "total_collections": len(collections)
        }

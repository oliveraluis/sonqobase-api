"""
Job de limpieza de bases de datos expiradas.

Este script debe ejecutarse periódicamente (ej: cada hora) como cron job
para eliminar bases de datos efímeras cuyos proyectos han expirado.

Uso:
    python -m app.jobs.cleanup_expired_databases
"""
from datetime import datetime, timezone
import logging

from app.config import settings
from app.infra.mongo_client import get_mongo_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cleanup_expired_databases():
    """
    Elimina bases de datos efímeras de proyectos expirados.
    
    Proceso:
    1. Busca proyectos con expires_at < ahora
    2. Elimina la base de datos efímera asociada
    3. Elimina el registro del proyecto de la metadata
    """
    client = get_mongo_client()
    meta_db = client[settings.mongo_meta_db]
    
    now = datetime.now(timezone.utc)
    
    # Buscar proyectos expirados
    expired_projects = list(meta_db.projects.find({
        "expires_at": {"$lt": now}
    }))
    
    if not expired_projects:
        logger.info("No expired projects found")
        return
    
    logger.info(f"Found {len(expired_projects)} expired projects")
    
    for project in expired_projects:
        project_id = project["project_id"]
        database_name = project["database"]
        
        try:
            # Eliminar base de datos efímera
            client.drop_database(database_name)
            logger.info(f"Dropped database '{database_name}' for project '{project_id}'")
            
            # Eliminar metadata del proyecto
            meta_db.projects.delete_one({"project_id": project_id})
            logger.info(f"Deleted project metadata for '{project_id}'")
            
        except Exception as e:
            logger.error(f"Error cleaning up project '{project_id}': {e}")
            continue
    
    logger.info(f"Cleanup completed. Removed {len(expired_projects)} expired projects")


if __name__ == "__main__":
    logger.info("Starting cleanup job...")
    cleanup_expired_databases()
    logger.info("Cleanup job finished")

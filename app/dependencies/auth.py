"""
Dependencies de autenticación para FastAPI.
Estas dependencies validan los headers de autenticación y aparecen en OpenAPI.
"""
from fastapi import Header, HTTPException, status, Request
from typing import Annotated, Optional

from app.domain.entities import User


async def require_master_key(
    request: Request,
    x_master_key: Annotated[str, Header(description="Master API Key para operaciones administrativas")]
) -> str:
    """
    Dependency que requiere Master API Key.
    
    Args:
        request: Request de FastAPI
        x_master_key: Header X-Master-Key
    
    Returns:
        Master API Key validada
    
    Raises:
        HTTPException: Si no está autenticado con Master Key
    """
    # El middleware ya validó el header, solo verificamos el nivel
    if not hasattr(request.state, 'auth_level') or request.state.auth_level != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master API Key required"
        )
    
    return x_master_key


async def require_user_key(
    request: Request,
    x_user_key: Annotated[str, Header(description="User API Key para operaciones de usuario")]
) -> dict:
    """
    Dependency que requiere User API Key.
    
    Args:
        request: Request de FastAPI
        x_user_key: Header X-User-Key
    
    Returns:
        Diccionario con información del usuario autenticado
    
    Raises:
        HTTPException: Si no está autenticado con User Key
    """
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"require_user_key called")
    logger.info(f"Has auth_level: {hasattr(request.state, 'auth_level')}")
    logger.info(f"Auth level: {getattr(request.state, 'auth_level', 'NOT SET')}")
    logger.info(f"Has user: {hasattr(request.state, 'user')}")
    
    # El middleware ya validó el header, solo verificamos el nivel
    if not hasattr(request.state, 'auth_level') or request.state.auth_level != "user":
        logger.error(f"Auth check failed. auth_level={getattr(request.state, 'auth_level', 'NOT SET')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User API Key required"
        )
    
    user = request.state.user
    
    # Retornar diccionario serializado
    return {
        "user_id": user.id,
        "email": user.email,
        "plan": user.plan_name,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
    }


async def require_project_key(
    request: Request,
    x_api_key: Annotated[str, Header(description="Project API Key para operaciones de proyecto")]
) -> dict:
    """
    Dependency que requiere Project API Key.
    
    Args:
        request: Request de FastAPI
        x_api_key: Header X-API-Key
    
    Returns:
        Información del proyecto autenticado
    
    Raises:
        HTTPException: Si no está autenticado con Project Key
    """
    # El middleware ya validó el header, solo verificamos el nivel
    if not hasattr(request.state, 'auth_level') or request.state.auth_level != "project":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project API Key required"
        )
    
    return {
        "project": request.state.project,
        "project_id": request.state.project_id,
        "user": request.state.user,
        "user_id": request.state.user_id,
    }


async def require_user_or_project_key(
    request: Request,
    x_user_key: Annotated[Optional[str], Header(description="User API Key")] = None,
    x_api_key: Annotated[Optional[str], Header(description="Project API Key")] = None,
) -> dict:
    """
    Dependency que requiere User Key O Project Key.
    
    Args:
        request: Request de FastAPI
        x_user_key: Header X-User-Key (opcional)
        x_api_key: Header X-API-Key (opcional)
    
    Returns:
        Información del usuario autenticado
    
    Raises:
        HTTPException: Si no está autenticado
    """
    # El middleware ya validó el header
    if not hasattr(request.state, 'auth_level'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (User Key or Project Key)"
        )
    
    if request.state.auth_level not in ["user", "project"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User API Key or Project API Key required"
        )
    
    result = {
        "user": request.state.user,
        "user_id": request.state.user_id,
        "auth_level": request.state.auth_level,
    }
    
    # Si es autenticación de proyecto, agregar info del proyecto
    if request.state.auth_level == "project":
        result["project"] = request.state.project
        result["project_id"] = request.state.project_id
    
    return result

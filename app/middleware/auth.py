"""
Middleware de autenticación para SonqoBase.
Soporta 3 niveles de autenticación:
1. Master API Key (admin) - Header: X-Master-Key
2. User API Key (developers) - Header: X-User-Key  
3. Project API Key (end-users) - Header: X-API-Key
"""
from datetime import datetime, timezone
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from app.infra.master_key_repository import MasterKeyRepository
from app.infra.user_repository import UserRepository
from app.infra.api_key_repository import ApiKeyRepository
from app.domain.entities import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que valida API keys y agrega información al request.state
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        logger.info(f"AuthMiddleware.dispatch called for path: {request.url.path}")
        
        # Rutas públicas (no requieren autenticación)
        public_paths = [
            "/pricing",
            "/pricing-data",
            "/contact",
            "/docs-page",
            "/dashboard/login",
            "/dashboard/register",
            "/dashboard",  # Dashboard overview (validación en frontend)
            "/dashboard/projects",  # Projects pages (validación en frontend)
            "/static",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/plans",  # Planes públicos
        ]
        
        # Manejar root path de forma especial
        if request.url.path == "/":
            logger.info(f"Path {request.url.path} is root, skipping auth")
            return await call_next(request)
        
        for path in public_paths:
            if request.url.path.startswith(path):
                logger.info(f"Path {request.url.path} matches public path: {path}")
                return await call_next(request)
        
        # Crear repositorios por request (usan singleton de conexión)
        master_key_repo = MasterKeyRepository()
        user_repo = UserRepository()
        project_key_repo = ApiKeyRepository()
        
        # Intentar autenticación en orden de prioridad
        auth_result = (
            self._try_master_key_auth(request, master_key_repo) or
            self._try_user_key_auth(request, user_repo) or
            self._try_project_key_auth(request, project_key_repo, user_repo)
        )
        
        # Si hubo un error específico durante la autenticación, retornarlo
        if hasattr(request.state, 'auth_error'):
            return request.state.auth_error
        
        if not auth_result:
            # Rutas de admin requieren Master Key
            if request.url.path.startswith("/api/v1/admin"):
                return self._unauthorized_response("Master API Key required. Use header: X-Master-Key")
            
            # Rutas de usuarios requieren User Key
            if request.url.path.startswith("/api/v1/users"):
                return self._unauthorized_response("User API Key required. Use header: X-User-Key")
            
            # Rutas de proyectos requieren Project Key
            if request.url.path.startswith("/api/v1/projects") or \
               request.url.path.startswith("/api/v1/collections"):
                return self._unauthorized_response("Project API Key required. Use header: X-API-Key")
        
        # Continuar con el request
        response = await call_next(request)
        return response
    
    def _unauthorized_response(self, detail: str):
        """Retornar respuesta de error 401"""
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail}
        )
    
    def _try_master_key_auth(
        self,
        request: Request,
        master_key_repo: MasterKeyRepository
    ) -> bool:
        """Intentar autenticación con Master Key"""
        master_key = request.headers.get("X-Master-Key")
        
        if not master_key:
            return False
        
        if master_key_repo.validate(master_key):
            request.state.auth_level = "master"
            request.state.master_key = master_key
            logger.debug("Authenticated with Master Key")
            return True
        
        return False
    
    def _try_user_key_auth(
        self,
        request: Request,
        user_repo: UserRepository
    ) -> bool:
        """Intentar autenticación con User Key"""
        user_key = request.headers.get("X-User-Key")
        
        logger.info(f"_try_user_key_auth called. Has X-User-Key: {bool(user_key)}")
        
        if not user_key:
            logger.info("No X-User-Key header found")
            return False
        
        logger.info(f"Looking for user with key: {user_key[:20]}...")
        user = user_repo.get_by_api_key(user_key)
        
        logger.info(f"User found: {bool(user)}")
        
        if user:
            # Verificar que el usuario esté activo
            if user.status != "active":
                logger.warning(f"User {user.id} is {user.status}")
                # Guardar error en request.state para manejarlo después
                request.state.auth_error = self._forbidden_response(f"User account is {user.status}")
                return False
            
            request.state.auth_level = "user"
            request.state.user = user
            request.state.user_id = user.id
            logger.debug(f"Authenticated user: {user.id}")
            return True
        
        logger.warning("User not found with provided API key")
        return False
    
    def _try_project_key_auth(
        self,
        request: Request,
        project_key_repo: ApiKeyRepository,
        user_repo: UserRepository
    ) -> bool:
        """Intentar autenticación con Project Key"""
        project_key = request.headers.get("X-API-Key")
        
        if not project_key:
            return False
        
        project = project_key_repo.get_project_by_key(project_key)
        
        if project:
            # Verificar que el proyecto no haya expirado
            expires_at = project["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < datetime.now(timezone.utc):
                request.state.auth_error = self._gone_response("Project has expired")
                return False
            
            # Obtener usuario del proyecto
            user = user_repo.get_by_id(project["user_id"])
            
            if not user:
                request.state.auth_error = self._not_found_response("Project owner not found")
                return False
            
            # Verificar que el usuario esté activo
            if user.status != "active":
                request.state.auth_error = self._forbidden_response(f"Project owner account is {user.status}")
                return False
            
            request.state.auth_level = "project"
            request.state.user = user
            request.state.user_id = user.id
            request.state.project = project
            request.state.project_id = project["project_id"]
            logger.debug(f"Authenticated project: {project['project_id']}")
            return True
        
        return False
    
    def _unauthorized_response(self, detail: str):
        """Retornar respuesta de error 401"""
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail}
        )
    
    def _forbidden_response(self, detail: str):
        """Retornar respuesta de error 403"""
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": detail}
        )
    
    def _not_found_response(self, detail: str):
        """Retornar respuesta de error 404"""
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": detail}
        )
    
    def _gone_response(self, detail: str):
        """Retornar respuesta de error 410"""
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content={"detail": detail}
        )

"""
Middleware de autenticación para SonqoBase.
Soporta 3 niveles de autenticación:
1. Master API Key (admin) - Header: X-Master-Key
2. User API Key (developers) - Header: X-User-Key  
3. Project API Key (end-users) - Header: X-API-Key
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from app.infra.master_key_repository import MasterKeyRepository
from app.infra.user_repository import UserRepository
from app.infra.api_key_repository import ApiKeyRepository


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que valida API keys y agrega información al request.state
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.master_key_repo = MasterKeyRepository()
        self.user_repo = UserRepository()
        self.project_key_repo = ApiKeyRepository()
    
    async def dispatch(self, request: Request, call_next):
        # Rutas públicas (no requieren autenticación)
        public_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/plans",  # Planes públicos
        ]
        
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Intentar autenticación en orden de prioridad
        auth_result = (
            self._try_master_key_auth(request) or
            self._try_user_key_auth(request) or
            self._try_project_key_auth(request)
        )
        
        if not auth_result:
            # Rutas de admin requieren Master Key
            if request.url.path.startswith("/api/v1/admin"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Master API Key required. Use header: X-Master-Key"
                )
            
            # Rutas de usuarios requieren User Key
            if request.url.path.startswith("/api/v1/users"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User API Key required. Use header: X-User-Key"
                )
            
            # Rutas de proyectos requieren Project Key
            if request.url.path.startswith("/api/v1/projects") or \
               request.url.path.startswith("/api/v1/collections"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Project API Key required. Use header: X-API-Key"
                )
        
        # Continuar con el request
        response = await call_next(request)
        return response
    
    def _try_master_key_auth(self, request: Request) -> bool:
        """Intentar autenticación con Master Key"""
        master_key = request.headers.get("X-Master-Key")
        
        if not master_key:
            return False
        
        if self.master_key_repo.validate(master_key):
            request.state.auth_level = "master"
            request.state.master_key = master_key
            return True
        
        return False
    
    def _try_user_key_auth(self, request: Request) -> bool:
        """Intentar autenticación con User Key"""
        user_key = request.headers.get("X-User-Key")
        
        if not user_key:
            return False
        
        user = self.user_repo.get_by_api_key(user_key)
        
        if user:
            # Verificar que el usuario esté activo
            if user.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User account is {user.status}"
                )
            
            request.state.auth_level = "user"
            request.state.user = user
            request.state.user_id = user.id
            return True
        
        return False
    
    def _try_project_key_auth(self, request: Request) -> bool:
        """Intentar autenticación con Project Key"""
        project_key = request.headers.get("X-API-Key")
        
        if not project_key:
            return False
        
        project = self.project_key_repo.get_project_by_key(project_key)
        
        if project:
            # Verificar que el proyecto no haya expirado
            from datetime import datetime, timezone
            expires_at = project["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Project has expired"
                )
            
            # Obtener usuario del proyecto
            user = self.user_repo.get_by_id(project["user_id"])
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project owner not found"
                )
            
            if user.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Project owner account is {user.status}"
                )
            
            request.state.auth_level = "project"
            request.state.user = user
            request.state.user_id = user.id
            request.state.project = project
            request.state.project_id = project["project_id"]
            return True
        
        return False

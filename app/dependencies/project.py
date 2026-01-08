from fastapi import Header, Query, Depends, HTTPException, status, Request
from typing import Optional
from datetime import datetime, timezone

from app.infra.project_repository import ProjectRepository
from app.domain.entities import Project

def get_project_repo() -> ProjectRepository:
    return ProjectRepository()

async def get_project_context(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    project_id: Optional[str] = Query(None, alias="project_id"),
    repo: ProjectRepository = Depends(get_project_repo),
) -> Project:
    """
    Resolve project context from X-API-Key OR JWT + project_id.
    """
    # 1. Try X-API-Key (Classic/SDK)
    if x_api_key:
        project = repo.get_by_api_key(x_api_key)
        if not project:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        # Check Expiry
        _check_expiry(project)
        return project

    # 2. Try JWT + project_id (Dashboard)
    # Check if user is authenticated via JWT (AuthMiddleware sets request.state.user)
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        
        # Try header X-Project-Id if query param missing
        if not project_id:
             project_id = request.headers.get("X-Project-Id")
        
        if not project_id:
            raise HTTPException(
                status_code=400, 
                detail="Project context required. Provide 'X-API-Key' header OR 'project_id' query param with JWT."
            )
            
        project = repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify ownership
        if project.user_id != user.id:
            # Check if user is master/admin? (Future proofing, for now strictly owner)
            if getattr(request.state, "auth_level", "") == "master":
                pass 
            else:
                raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
        # Check Expiry
        _check_expiry(project)
        return project

    raise HTTPException(status_code=401, detail="Authentication required (X-API-Key or Bearer Token)")

def _check_expiry(project: Project):
    if project.expires_at:
        expires = project.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Project expired")

"""
Dependencies para FastAPI endpoints.
"""
from app.dependencies.auth import (
    require_master_key,
    require_user_key,
    require_project_key,
    require_user_or_project_key,
)

__all__ = [
    "require_master_key",
    "require_user_key",
    "require_project_key",
    "require_user_or_project_key",
]

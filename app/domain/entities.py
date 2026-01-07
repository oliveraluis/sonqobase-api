from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class Database:
    name: str
    expires_at: datetime


@dataclass(frozen=True)
class ProjectStats:
    """Estadísticas de uso del proyecto"""
    reads_count: int = 0
    writes_count: int = 0
    rag_queries_count: int = 0
    last_activity: datetime | None = None


@dataclass(frozen=True)
class Project:
    id: str
    user_id: str  # Relación con User
    slug: str  # Identificador legible (ej: "altoqperu")
    name: str
    description: str | None
    status: str
    expires_at: datetime
    database: Database
    stats: ProjectStats  # Estadísticas de uso del proyecto



@dataclass(frozen=True)
class Plan:
    """Plan de suscripción (Free, Starter, Pro)"""
    name: str  # "free" | "starter" | "pro"
    display_name: str  # "Free", "Starter", "Pro"
    price_usd: float
    
    # Límites
    projects_limit: int
    reads_limit: int
    writes_limit: int
    rag_queries_limit: int
    pdf_max_size_mb: int
    retention_hours: int
    audit_retention_days: int
    
    # Features
    features: List[str]  # ["webhooks", "analytics_advanced", "export_metrics"]


@dataclass(frozen=True)
class UsageStats:
    """Estadísticas de uso del usuario (se resetea mensualmente)"""
    projects_count: int
    reads_count: int
    writes_count: int
    rag_queries_count: int
    period_start: datetime
    period_end: datetime


@dataclass(frozen=True)
class User:
    """Usuario de SonqoBase (developer que usa la plataforma)"""
    id: str  # user_abc123
    email: str
    api_key_hash: str  # Hash SHA-256 de la User API Key
    plan_name: str  # "free" | "starter" | "pro"
    status: str  # "active" | "blocked" | "suspended"
    created_at: datetime
    updated_at: datetime
    
    # Uso actual
    usage: UsageStats
    
    # Webhooks (solo Plan Pro)
    webhook_url: str | None = None


@dataclass(frozen=True)
class MasterKey:
    """API Key maestra para administración"""
    key_hash: str  # Hash SHA-256
    description: str  # "Admin principal"
    permissions: List[str]  # ["*"] o ["users:create", "users:update", etc.]
    created_at: datetime
    is_active: bool = True


@dataclass(frozen=True)
class Lead:
    """Lead de contacto desde landing page"""
    email: str
    name: str
    company: str | None
    interest: str  # Descripción de su interés
    plan_interest: str  # "free" | "starter" | "pro"
    created_at: datetime
    status: str = "pending"  # "pending" | "contacted" | "converted"
    source: str = "landing_page"

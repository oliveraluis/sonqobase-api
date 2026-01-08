from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.api.v1.projects import router as projects_router
from app.api.v1.collections import router as collection_router
from app.api.v1.admin import router as admin_router
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.plans import router as plans_router
from app.api.v1.jobs import router as jobs_router
from app.api.web import router as web_router
from app.middleware.auth import AuthMiddleware
from app.middleware.error_handler import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler
)
from app.infra.event_bus import get_event_bus

# Importar listeners para auto-registro
import app.listeners
import app.listeners.otp_persistence_listener  # NEW

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SonqoBase API",
    version="1.0.0",
    description="""
## Base de Datos Vectorial Efímera como Servicio

SonqoBase proporciona una API REST para gestionar bases de datos vectoriales efímeras con embeddings automáticos y búsqueda semántica.

### Características Principales
- 🗄️ **Proyectos Multi-tenant**: Cada usuario puede crear múltiples proyectos aislados
- 📄 **Ingesta Automática**: Sube PDFs y genera embeddings automáticamente
- 🧠 **RAG Queries**: Consultas con Retrieval-Augmented Generation
- ⏱️ **TTL Automático**: Los datos expiran automáticamente según el plan
- 🔐 **Autenticación Dual**: User API Keys y Project API Keys

### Autenticación
- **User API Key**: Para gestionar proyectos (header: `X-User-Key`)
- **Project API Key**: Para operaciones en colecciones (header: `X-API-Key`)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "SonqoBase Support",
        "email": "support@sonqobase.com",
    },
    license_info={
        "name": "Proprietary",
    },
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Ocultar modelos por defecto
        "docExpansion": "list",  # Expandir solo tags
        "filter": True,  # Habilitar búsqueda
        "syntaxHighlight.theme": "monokai"  # Tema oscuro
    }
)

# Configurar CORS (Permitir todo para demo, restringir en prod estricto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir localhost:8080 y otros
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Manejadores de Excepciones Globales
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# app.mount("/examples", StaticFiles(directory="examples"), name="examples")  # Removed - not needed with new architecture
app.mount("/sdk-js", StaticFiles(directory="sdk-js"), name="sdk-js")

# Middleware de autenticación
app.add_middleware(AuthMiddleware)

# Router Web (Landing Page y Docs) - OCULTO de OpenAPI
app.include_router(
    web_router,
    include_in_schema=False,  # No mostrar en OpenAPI
)

# Routers de Admin (requieren Master API Key)
app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Admin"],
    include_in_schema=False,  # Ocultar de OpenAPI/Swagger
)

# Routers de Usuarios (requieren User API Key)
app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

# Routers de Autenticación (OTP, Refresh)
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)

# Routers de Planes (públicos)
app.include_router(
    plans_router,
    prefix="/api/v1/plans",
    tags=["Plans"],
)

# Routers de Proyectos (requieren User API Key)
app.include_router(
    projects_router,
    prefix="/api/v1/projects",
    tags=["Projects"],
)

# Routers de Collections (requieren Project API Key)
app.include_router(
    collection_router,
    prefix="/api/v1/collections",
    tags=["Collections"],
)

# Routers de Jobs (requieren autenticación)
app.include_router(
    jobs_router,
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


@app.on_event("startup")
async def startup_event():
    """Inicializar event bus y mostrar listeners registrados"""
    event_bus = get_event_bus()
    listener_count = event_bus.get_listener_count()
    logger.info(f"🚀 SonqoBase started with {listener_count} event listeners registered")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "SonqoBase"}


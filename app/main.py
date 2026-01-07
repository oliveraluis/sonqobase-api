from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging

from app.api.v1.projects import router as projects_router
from app.api.v1.collections import router as collection_router
from app.api.v1.admin import router as admin_router
from app.api.v1.users import router as users_router
from app.api.v1.plans import router as plans_router
from app.api.v1.jobs import router as jobs_router
from app.api.web import router as web_router
from app.middleware.auth import AuthMiddleware
from app.infra.event_bus import get_event_bus

# Importar listeners para auto-registro
import app.listeners

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SonqoBase API",
    version="1.0.0",
    description="""
## Base de Datos Vectorial Efímera como Servicio

SonqoBase te permite almacenar documentos, generar embeddings automáticamente y hacer consultas con IA (RAG) en minutos.

### 🚀 Características

- **Almacenamiento de Documentos**: Guarda y consulta documentos JSON
- **Ingesta de PDFs**: Sube PDFs y conviértelos en bases de conocimiento
- **Consultas RAG**: Haz preguntas en lenguaje natural sobre tus documentos
- **Embeddings Automáticos**: Generación automática de vectores con IA
- **Búsqueda Semántica**: Encuentra documentos por similitud, no solo palabras clave

### 📚 Documentación Completa

Visita [/api-docs](/api-docs) para ver la documentación completa con ejemplos.

### 🔐 Autenticación

Todas las peticiones requieren una API Key en el header `X-API-Key`.
Obtén tu API Key en el [Dashboard](/dashboard).
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
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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


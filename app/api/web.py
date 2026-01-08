"""
Router para servir la landing page y documentación.
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import logging

from app.infra.plan_repository import PlanRepository
from app.infra.lead_repository import LeadRepository
from app.services.create_lead import CreateLeadService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


# Dependency Injection
def get_create_lead_service() -> CreateLeadService:
    return CreateLeadService(lead_repo=LeadRepository())


# Request Models
class ContactRequest(BaseModel):
    email: EmailStr
    name: str
    company: str | None = None
    interest: str
    plan_interest: str  # "free" | "starter" | "pro"


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page principal"""
    return templates.TemplateResponse(
        "landing/index.html",
        {"request": request}
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Página de pricing"""
    return templates.TemplateResponse(
        "landing/pricing.html",
        {"request": request}
    )


@router.get("/api-docs", response_class=HTMLResponse)
async def api_documentation(request: Request):
    """Documentación de la API"""
    return templates.TemplateResponse(
        "docs.html",
        {"request": request}
    )

@router.get("/docs-page", response_class=HTMLResponse)
async def docs_page(request: Request):
    """Página de documentación"""
    return templates.TemplateResponse(
        "docs/index.html",
        {"request": request}
    )


@router.get("/dashboard/login", response_class=HTMLResponse)
async def dashboard_login(request: Request):
    """Dashboard login page"""
    return templates.TemplateResponse(
        "dashboard/login.html",
        {"request": request}
    )


@router.get("/dashboard/register", response_class=HTMLResponse)
async def dashboard_register(request: Request):
    """Dashboard register page"""
    return templates.TemplateResponse(
        "dashboard/register.html",
        {"request": request}
    )


@router.get("/dashboard/desktop-only", response_class=HTMLResponse)
async def dashboard_desktop_only(request: Request):
    """Desktop-only restriction page"""
    return templates.TemplateResponse(
        "dashboard/desktop_only.html",
        {"request": request}
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_overview(request: Request):
    """Dashboard overview page"""
    return templates.TemplateResponse(
        "dashboard/overview.html",
        {"request": request}
    )


@router.get("/dashboard/projects", response_class=HTMLResponse)
async def dashboard_projects(request: Request):
    """Dashboard projects list page"""
    return templates.TemplateResponse(
        "dashboard/projects.html",
        {"request": request}
    )


@router.get("/dashboard/projects/new", response_class=HTMLResponse)
async def dashboard_project_new(request: Request):
    """Dashboard create project page"""
    return templates.TemplateResponse(
        "dashboard/project_new.html",
        {"request": request}
    )


@router.get("/dashboard/projects/{project_id}", response_class=HTMLResponse)
async def dashboard_project_detail(request: Request, project_id: str):
    """Dashboard project detail page"""
    return templates.TemplateResponse(
        "dashboard/project_detail.html",
        {"request": request, "project_id": project_id}
    )


@router.get("/dashboard/projects/{project_id}/playground", response_class=HTMLResponse)
async def dashboard_project_playground(request: Request, project_id: str):
    """Dashboard RAG Playground page"""
    return templates.TemplateResponse(
        "dashboard/playground.html",
        {"request": request, "project_id": project_id, "active_page": "playground"}
    )


@router.get("/dashboard/projects/{project_id}/jobs", response_class=HTMLResponse)
async def dashboard_project_jobs(request: Request, project_id: str):
    """Dashboard Jobs Tracking page"""
    return templates.TemplateResponse(
        "dashboard/jobs.html",
        {"request": request, "project_id": project_id, "active_page": "jobs"}
    )


@router.get("/pricing-data")
async def get_pricing_data():
    """
    Obtener datos de pricing desde la base de datos.
    Endpoint público para cargar dinámicamente en la landing.
    """
    plan_repo = PlanRepository()
    plans = plan_repo.get_all()
    
    return {
        "plans": [
            {
                "name": plan.name,
                "display_name": plan.display_name,
                "price_usd": plan.price_usd,
                "limits": {
                    "projects": plan.projects_limit,
                    "reads_per_month": plan.reads_limit,
                    "writes_per_month": plan.writes_limit,
                    "rag_queries_per_month": plan.rag_queries_limit,
                    "pdf_max_size_mb": plan.pdf_max_size_mb,
                    "retention_hours": plan.retention_hours,
                },
                "features": plan.features,
            }
            for plan in plans
        ]
    }


@router.post("/contact")
async def submit_contact_form(
    payload: ContactRequest,
    service: CreateLeadService = Depends(get_create_lead_service),
):
    """
    Recibir formulario de contacto y guardar lead en BD.
    """
    try:
        result = service.execute(
            email=payload.email,
            name=payload.name,
            company=payload.company,
            interest=payload.interest,
            plan_interest=payload.plan_interest,
        )
        
        return {
            "success": True,
            "message": "¡Gracias por tu interés! Nos pondremos en contacto contigo pronto.",
        }
    
    except ValueError as e:
        # Errores de validación
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error creating lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar tu solicitud. Por favor intenta de nuevo."
        )

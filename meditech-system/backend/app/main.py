from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from structlog import get_logger
from contextlib import asynccontextmanager
import time

from app.core.config import get_settings, Settings
from app.models.database import Base
from app.api import auth, branches, patients, invoices, services, results, users, roles, public


logger = get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("iniciando_meditech_system", version=settings.APP_VERSION)
    
    # Inicializar servicios externos
    # - Conexión a Orthanc
    # - Conexión a OpenELIS
    # - Verificar Redis
    
    yield
    
    # Limpieza al cerrar
    logger.info("deteniendo_meditech_system")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema Integral de Gestión Médica - HIS/PACS/LIS",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    logger.info(
        "request_completada",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    return response


# Middleware de error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "error_no_controlado",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "code": "INTERNAL_ERROR"}
    )


# Rutas de salud
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificación de salud del sistema"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Verifica si el sistema está listo para recibir tráfico"""
    # Aquí verificaríamos conexiones a DB, Redis, Orthanc, OpenELIS
    return {"status": "ready"}


# Registrar routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Usuarios"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(branches.router, prefix="/api/v1/branches", tags=["Sucursales"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Pacientes"])
app.include_router(services.router, prefix="/api/v1/services", tags=["Servicios"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Facturación"])
app.include_router(results.router, prefix="/api/v1/results", tags=["Resultados"])
app.include_router(public.router, prefix="/api/v1/public", tags=["Público"])


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/api/docs",
        "health": "/health"
    }
